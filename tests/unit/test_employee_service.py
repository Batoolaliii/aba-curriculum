import importlib
import re
import sys

import boto3
import pytest
from moto import mock_aws

TABLE_NAME = "test-employees"
MODULE_NAME = "api.services.employee_service"


@pytest.fixture
def employee_service(monkeypatch):
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
                {"AttributeName": "GSI1PK", "AttributeType": "S"},
                {"AttributeName": "GSI1SK", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "GSI1",
                    "KeySchema": [
                        {"AttributeName": "GSI1PK", "KeyType": "HASH"},
                        {"AttributeName": "GSI1SK", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        previous_module = sys.modules.pop(MODULE_NAME, None)
        try:
            module = importlib.import_module(MODULE_NAME)
            yield module
        finally:
            sys.modules.pop(MODULE_NAME, None)
            if previous_module is not None:
                sys.modules[MODULE_NAME] = previous_module


@pytest.fixture
def table(employee_service):
    return boto3.resource(
        "dynamodb", region_name="us-east-1"
    ).Table(TABLE_NAME)


def employee_data():
    return {
        "name": "Ada Lovelace",
        "department": "Engineering",
        "startDate": "2024-06-03",
    }


def test_create_generates_eight_character_id_and_stores_employee(
    employee_service, table
):
    # Arrange
    data = employee_data()

    # Act
    result = employee_service.create(data)
    stored = table.get_item(
        Key={"PK": "USER", "SK": result["SK"]}
    )["Item"]

    # Assert
    assert re.fullmatch(r"[0-9a-f]{8}", result["SK"])
    assert result["PK"] == "USER"
    assert result["employeeId"] == result["SK"]
    assert stored == result


def test_create_called_twice_generates_different_ids(employee_service):
    # Arrange
    data = employee_data()

    # Act
    first = employee_service.create(data)
    second = employee_service.create(data)

    # Assert
    assert first["employeeId"] != second["employeeId"]


def test_save_writes_expected_item(employee_service, table):
    # Arrange
    data = {**employee_data(), "role": "admin"}
    expected = {
        "PK": "USER",
        "SK": "employee1",
        "GSI1PK": "USER_BY_DATE",
        "GSI1SK": "2024-06-03",
        "employeeId": "employee1",
        "name": "Ada Lovelace",
        "department": "Engineering",
        "startDate": "2024-06-03",
        "role": "admin",
    }

    # Act
    result = employee_service.save("employee1", data)
    stored = table.get_item(
        Key={"PK": "USER", "SK": "employee1"}
    )["Item"]

    # Assert
    assert result == expected
    assert stored == expected


def test_save_defaults_role_to_employee(employee_service, table):
    # Arrange
    data = employee_data()

    # Act
    result = employee_service.save("employee2", data)
    stored = table.get_item(
        Key={"PK": "USER", "SK": "employee2"}
    )["Item"]

    # Assert
    assert result["role"] == "employee"
    assert stored["role"] == "employee"


def test_delete_removes_only_requested_employee(employee_service, table):
    employee_service.save("employee1", employee_data())
    employee_service.save("employee2", employee_data())
    leave = {"PK": "employee1", "SK": "2026-10-29", "note": "Leave"}
    table.put_item(Item=leave)

    employee_service.delete("employee1")

    assert "Item" not in table.get_item(Key={"PK": "USER", "SK": "employee1"})
    assert table.get_item(Key={"PK": "USER", "SK": "employee2"})["Item"]["employeeId"] == "employee2"
    assert table.get_item(Key={"PK": "employee1", "SK": "2026-10-29"})["Item"] == leave
