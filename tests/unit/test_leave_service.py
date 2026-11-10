import importlib
import sys

import boto3
import pytest
from moto import mock_aws

TABLE_NAME = "test-leave"
MODULE_NAME = "api.services.leave_service"


@pytest.fixture
def leave_service(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")
    monkeypatch.setenv("POWERTOOLS_TRACE_DISABLED", "true")
    monkeypatch.setenv("TABLE_NAME", TABLE_NAME)

    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        previous_module = sys.modules.pop(MODULE_NAME, None)
        try:
            yield importlib.import_module(MODULE_NAME)
        finally:
            sys.modules.pop(MODULE_NAME, None)
            if previous_module is not None:
                sys.modules[MODULE_NAME] = previous_module


@pytest.fixture
def table(leave_service):
    return boto3.resource(
        "dynamodb", region_name="us-east-1"
    ).Table(TABLE_NAME)


def test_save_writes_expected_leave_item(leave_service, table):
    # Arrange
    expected = {
        "PK": "employee1",
        "SK": "2026-07-06",
        "employeeId": "employee1",
        "startDate": "2026-07-06",
        "endDate": "2026-07-10",
        "note": "Holiday",
    }

    # Act
    result = leave_service.save(
        "employee1", "2026-07-06",
        {"endDate": "2026-07-10", "note": "Holiday"},
    )
    stored = table.get_item(
        Key={"PK": "employee1", "SK": "2026-07-06"}
    )["Item"]

    # Assert
    assert result == expected
    assert stored == expected


def test_save_defaults_note_to_empty_string(leave_service, table):
    # Arrange
    data = {"endDate": "2026-07-10"}

    # Act
    result = leave_service.save("employee1", "2026-07-06", data)
    stored = table.get_item(
        Key={"PK": "employee1", "SK": "2026-07-06"}
    )["Item"]

    # Assert
    assert result["note"] == ""
    assert stored["note"] == ""


def test_save_same_keys_overwrites_existing_leave(leave_service, table):
    # Arrange
    leave_service.save(
        "employee1", "2026-07-06",
        {"endDate": "2026-07-10", "note": "v1"},
    )

    # Act
    leave_service.save(
        "employee1", "2026-07-06",
        {"endDate": "2026-07-12", "note": "v2"},
    )
    stored = table.scan()["Items"]

    # Assert
    assert len(stored) == 1
    assert stored[0]["endDate"] == "2026-07-12"
    assert stored[0]["note"] == "v2"


def test_list_without_month_returns_only_employee_leave_sorted(leave_service):
    # Arrange
    for date in ["2026-09-01", "2026-07-06", "2026-08-03"]:
        leave_service.save("employee1", date, {"endDate": date})
    leave_service.save(
        "employee2", "2026-07-01", {"endDate": "2026-07-02"}
    )

    # Act
    result = leave_service.list_for_employee("employee1", None)

    # Assert
    assert [item["startDate"] for item in result] == [
        "2026-07-06", "2026-08-03", "2026-09-01",
    ]
    assert all(item["employeeId"] == "employee1" for item in result)


def test_list_with_month_excludes_other_months(leave_service):
    # Arrange
    for date in ["2026-07-20", "2026-08-03", "2026-07-06"]:
        leave_service.save("employee1", date, {"endDate": date})

    # Act
    result = leave_service.list_for_employee("employee1", "2026-07")

    # Assert
    assert [item["startDate"] for item in result] == [
        "2026-07-06", "2026-07-20",
    ]


def test_list_for_employee_without_leave_returns_empty_list(leave_service):
    # Arrange
    leave_service.save(
        "employee2", "2026-07-06", {"endDate": "2026-07-10"}
    )

    # Act
    result = leave_service.list_for_employee("employee1", None)

    # Assert
    assert result == []
