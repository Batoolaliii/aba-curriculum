"""Route regressions with service modules replaced before import; no AWS."""
import importlib
import sys
from pathlib import Path
from types import ModuleType
from types import SimpleNamespace
from unittest.mock import Mock
from fastapi.testclient import TestClient
import pytest

@pytest.fixture
def client(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).parents[2] / "api"))
    package = importlib.import_module("services")
    services = {}
    for name in ("employee_service", "leave_service", "hr_request_service"):
        module = ModuleType(f"services.{name}")
        for method in ("create", "get", "delete", "list_all", "list_by_hire_date", "save", "list_for_employee", "start_hr_request", "start_time_off_request"):
            setattr(module, method, Mock())
        monkeypatch.setitem(sys.modules, f"services.{name}", module)
        monkeypatch.setattr(package, name, module, raising=False)
        services[name] = module
    for name in list(sys.modules):
        if name in ("handler", "controllers") or name.startswith("controllers."):
            monkeypatch.delitem(sys.modules, name)
    return TestClient(importlib.import_module("handler").app), services

def test_leave_routes_registered(client):
    http, services = client
    leave = services["leave_service"]
    leave.save.return_value = {"startDate": "2026-11-10", "endDate": "2026-11-12"}
    leave.list_for_employee.return_value = [leave.save.return_value]
    assert http.post("/employees/e1/leave", json={"startDate": "2026-11-10", "endDate": "2026-11-12"}).status_code == 201
    assert len(http.get("/employees/e1/leave?month=2026-11").json()["leave"]) == 1
    assert http.put("/employees/e1/leave/2026-11-10", json={"endDate": "2026-11-13", "note": "Updated"}).status_code == 200
    leave.save.assert_called_with("e1", "2026-11-10", {"endDate": "2026-11-13", "note": "Updated"})

def test_invalid_leave_dates_and_month(client):
    http, services = client
    assert http.post("/employees/e1/leave", json={"startDate": "bad", "endDate": "2026-11-12"}).status_code == 422
    assert http.get("/employees/e1/leave?month=invalid").status_code == 422
    services["leave_service"].save.assert_not_called()

def test_employee_and_hr_contracts_preserved(client):
    http, services = client
    employees = services["employee_service"]
    employees.list_all.return_value = [{"employeeId": "e1"}]
    employees.list_by_hire_date.return_value = []
    employees.get.return_value = None
    assert http.get("/employees").json() == {"employees": [{"employeeId": "e1"}]}
    assert http.get("/employees?hiredFrom=2026-01-01&hiredTo=2026-12-31").json() == {"employees": []}
    assert http.get("/employees/missing").status_code == 404
    services["hr_request_service"].start_hr_request.return_value = {"executionArn": "execution-1"}
    assert http.post("/hr-requests", json={"user_id": "e1", "prompt": "Benefits"}).status_code == 202


def test_exported_lambda_handler_keeps_logging_tracing_and_mangum(client, monkeypatch):
    handler = importlib.import_module("handler")
    context = SimpleNamespace(function_name="hr-api", memory_limit_in_mb=512,
                              invoked_function_arn="arn:aws:lambda:us-east-1:123456789012:function:hr-api",
                              aws_request_id="request-test")
    event = {"resource": "/{proxy+}", "path": "/public/health", "httpMethod": "GET",
             "headers": {"host": "example.com"}, "requestContext": {"identity": {"sourceIp": "127.0.0.1"}},
             "body": None, "isBase64Encoded": False}
    traced = Mock(wraps=handler.tracer.provider.in_subsegment)
    monkeypatch.setattr(handler.tracer.provider, "in_subsegment", traced)
    response = handler.lambda_handler(event, context)
    assert response["statusCode"] == 200
    assert response["body"] == '{"status":"ok"}'
    assert handler.logger.get_current_keys()["function_request_id"] == "request-test"
    traced.assert_called()


@pytest.fixture
def employee_service(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).parents[2] / "api"))
    monkeypatch.setenv("TABLE_NAME", "test-table")
    import boto3
    resource = Mock()
    monkeypatch.setattr(boto3, "resource", Mock(return_value=resource))
    monkeypatch.delitem(sys.modules, "services.employee_service", raising=False)
    module = importlib.import_module("services.employee_service")
    yield module, resource.Table.return_value
    sys.modules.pop("services.employee_service", None)


@pytest.mark.parametrize("start,end,operator,dates", [
    (None, None, None, []),
    ("2026-01-01", None, ">=", ["2026-01-01"]),
    (None, "2026-12-31", "<=", ["2026-12-31"]),
    ("2026-01-01", "2026-12-31", "BETWEEN", ["2026-01-01", "2026-12-31"]),
])
def test_hire_date_lookup_preserves_bounds_and_instrumentation(employee_service, monkeypatch, start, end, operator, dates):
    from boto3.dynamodb.conditions import ConditionExpressionBuilder
    service, table = employee_service
    records = [{"employeeId": "e1"}]
    table.query.return_value = {"Items": records}
    log = Mock()
    monkeypatch.setattr(service.logger, "info", log)
    traced = Mock(wraps=service.tracer.provider.in_subsegment)
    monkeypatch.setattr(service.tracer.provider, "in_subsegment", traced)
    assert service.list_by_hire_date(start, end) == records
    kwargs = table.query.call_args.kwargs
    assert kwargs["IndexName"] == "GSI1"
    condition = ConditionExpressionBuilder().build_expression(kwargs["KeyConditionExpression"], is_key_condition=True)
    assert list(condition.attribute_value_placeholders.values()) == ["USER_BY_DATE", *dates]
    assert set(condition.attribute_name_placeholders.values()) == ({"GSI1PK", "GSI1SK"} if operator else {"GSI1PK"})
    if operator:
        assert operator in condition.condition_expression
    log.assert_any_call("listing employees by hire date", hired_from=start, hired_to=end)
    log.assert_any_call("listed employees by hire date", count=1)
    traced.assert_called()


def test_hire_date_lookup_propagates_database_errors(employee_service):
    service, table = employee_service
    table.query.side_effect = RuntimeError("database unavailable")
    with pytest.raises(RuntimeError, match="database unavailable"):
        service.list_by_hire_date(None, None)


def caller_client(http, sub, groups=""):
    # Exercise the real auth helpers with Gateway claims, not local admin fallback.
    async def app(scope, receive, send):
        scope = {**scope, "aws.event": {"requestContext": {"authorizer": {
            "claims": {"sub": sub, "cognito:groups": groups}
        }}}}
        await http.app(scope, receive, send)
    return TestClient(app)


@pytest.mark.parametrize("sub,groups", [("owner-sub", ""), ("other-sub", "admins")])
def test_delete_employee_allows_owner_or_admin(client, sub, groups):
    http, services = client
    employees = services["employee_service"]
    records = {"e1": {"employeeId": "e1", "cognitoSub": "owner-sub"}}
    employees.get.side_effect = records.get
    employees.delete.side_effect = lambda employee_id: records.pop(employee_id)
    response = caller_client(http, sub, groups).delete("/employees/e1")
    assert response.status_code == 200
    assert response.json() == {"deleted": "e1"}
    employees.get.assert_called_once_with("e1")
    employees.delete.assert_called_once_with("e1")
    assert "e1" not in records


@pytest.mark.parametrize("record", [
    {"employeeId": "e1", "cognitoSub": "owner-sub"}, {"employeeId": "e1"},
])
def test_delete_employee_rejects_non_owner_without_deleting(client, record):
    http, services = client
    employees = services["employee_service"]
    records = {"e1": record.copy()}
    employees.get.side_effect = records.get
    employees.delete.side_effect = lambda employee_id: records.pop(employee_id)
    response = caller_client(http, "non-owner", "employees").delete("/employees/e1")
    assert response.status_code == 404
    assert response.json() == {"detail": "Employee not found"}
    employees.delete.assert_not_called()
    assert records == {"e1": record}


def test_delete_missing_employee_returns_404_without_deleting(client):
    http, services = client
    services["employee_service"].get.return_value = None
    response = caller_client(http, "admin-sub", "admins").delete("/employees/missing")
    assert response.status_code == 404
    assert response.json() == {"detail": "Employee not found"}
    services["employee_service"].delete.assert_not_called()


@pytest.mark.parametrize("query,start,end", [
    ("hiredFrom=2026-01-01&hiredTo=2026-12-31", "2026-01-01", "2026-12-31"),
    ("hiredFrom=2026-01-01", "2026-01-01", None),
    ("hiredTo=2026-12-31", None, "2026-12-31"),
])
def test_single_list_route_preserves_hire_date_filters(client, query, start, end):
    http, services = client
    employees = services["employee_service"]
    employees.list_by_hire_date.return_value = [{"employeeId": "e1"}]
    response = caller_client(http, "non-owner").get(f"/employees?{query}")
    assert response.status_code == 200
    assert response.json() == {"employees": [{"employeeId": "e1"}]}
    employees.list_by_hire_date.assert_called_once_with(start, end)
    employees.list_all.assert_not_called()
    router = importlib.import_module("controllers.employee_controller").router
    routes = [route for route in router.routes
              if getattr(route, "path", None) == "/employees"
              and "GET" in getattr(route, "methods", set())]
    assert len(routes) == 1
