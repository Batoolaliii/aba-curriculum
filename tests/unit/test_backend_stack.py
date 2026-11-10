"""Offline assertions for BackendStack's synthesized infrastructure contract."""

from pathlib import Path

import pytest
from aws_cdk import App
from aws_cdk.assertions import Match, Template

from hr_leave_portal.backend_stack import BackendStack, LAYER_ARN_PARAM


@pytest.fixture
def template(monkeypatch):
    # BackendStack packages the relative 'api' asset. Do not depend on pytest's cwd.
    monkeypatch.chdir(Path(__file__).resolve().parents[2])
    stack = BackendStack(App(), "BackendUnderTest")
    return Template.from_stack(stack)


def test_table_keys_and_on_demand_billing(template):
    template.resource_count_is("AWS::DynamoDB::Table", 1)
    template.has_resource_properties("AWS::DynamoDB::Table", {
        "BillingMode": "PAY_PER_REQUEST",
        "KeySchema": [
            {"AttributeName": "PK", "KeyType": "HASH"},
            {"AttributeName": "SK", "KeyType": "RANGE"},
        ],
        "AttributeDefinitions": Match.array_with([
            {"AttributeName": "PK", "AttributeType": "S"},
            {"AttributeName": "SK", "AttributeType": "S"},
        ]),
    })


def test_gsi1_keys_and_all_projection(template):
    template.has_resource_properties("AWS::DynamoDB::Table", {
        "AttributeDefinitions": Match.array_with([
            {"AttributeName": "GSI1PK", "AttributeType": "S"},
            {"AttributeName": "GSI1SK", "AttributeType": "S"},
        ]),
        "GlobalSecondaryIndexes": Match.array_with([Match.object_like({
            "IndexName": "GSI1",
            "KeySchema": [
                {"AttributeName": "GSI1PK", "KeyType": "HASH"},
                {"AttributeName": "GSI1SK", "KeyType": "RANGE"},
            ],
            "Projection": {"ProjectionType": "ALL"},
        })]),
    })


def test_api_lambda_tracing_and_environment(template):
    template.resource_count_is("AWS::Lambda::Function", 1)
    table_id, = template.find_resources("AWS::DynamoDB::Table")
    template.has_resource_properties("AWS::Lambda::Function", {
        "Handler": "handler.lambda_handler",
        "TracingConfig": {"Mode": "Active"},
        "Environment": {"Variables": Match.object_like({
            "TABLE_NAME": {"Ref": table_id},
            "POWERTOOLS_SERVICE_NAME": "hr-api",
            "POWERTOOLS_LOG_LEVEL": "INFO",
        })},
    })


def test_api_layer_references_configured_ssm_parameter(template):
    # CDK emits an SSM-valued template parameter, not a literal layer ARN.
    # Discover its logical ID so this assertion survives CDK naming changes.
    parameters = template.to_json().get("Parameters", {})
    layer_parameters = [name for name, value in parameters.items()
                        if value.get("Default") == LAYER_ARN_PARAM]
    assert len(layer_parameters) == 1
    parameter_id = layer_parameters[0]
    template.has_parameter(parameter_id, {
        "Type": "AWS::SSM::Parameter::Value<String>",
        "Default": LAYER_ARN_PARAM,
    })
    template.has_resource_properties("AWS::Lambda::Function", {
        "Handler": "handler.lambda_handler",
        "Layers": Match.array_with([{"Ref": parameter_id}]),
    })
    # This checks the reference only; it neither reads SSM nor inspects layer contents.


def test_rest_api_and_cognito_authorizer(template):
    template.resource_count_is("AWS::ApiGateway::RestApi", 1)
    template.resource_count_is("AWS::ApiGateway::Authorizer", 1)
    api_id, = template.find_resources("AWS::ApiGateway::RestApi")
    pool_id, = template.find_resources("AWS::Cognito::UserPool")
    template.has_resource_properties("AWS::ApiGateway::Authorizer", {
        "Type": "COGNITO_USER_POOLS",
        "IdentitySource": "method.request.header.Authorization",
        "RestApiId": {"Ref": api_id},
        "ProviderARNs": [{"Fn::GetAtt": [pool_id, "Arn"]}],
    })


def test_actual_proxy_methods_are_protected_and_preflight_is_public(template):
    api_id, = template.find_resources("AWS::ApiGateway::RestApi")
    authorizer_id, = template.find_resources("AWS::ApiGateway::Authorizer")
    resources = template.find_resources("AWS::ApiGateway::Resource")
    proxy_ids = [name for name, resource in resources.items()
                 if resource["Properties"]["PathPart"] == "{proxy+}"]
    assert len(proxy_ids) == 1
    root = {"Fn::GetAtt": [api_id, "RootResourceId"]}
    proxy = {"Ref": proxy_ids[0]}
    template.has_resource_properties("AWS::ApiGateway::Resource", {
        "PathPart": "{proxy+}", "ParentId": root, "RestApiId": {"Ref": api_id},
    })

    # LambdaRestApi synthesizes ANY and OPTIONS on / and /{proxy+}; individual
    # FastAPI routes live inside Lambda and are not separate Gateway methods.
    methods = template.find_resources("AWS::ApiGateway::Method")
    assert methods
    for resource in methods.values():
        properties = resource["Properties"]
        expected = {
            "RestApiId": {"Ref": api_id},
            "ResourceId": properties["ResourceId"],
            "HttpMethod": properties["HttpMethod"],
        }
        if properties["HttpMethod"] == "OPTIONS":
            expected.update({
                "AuthorizationType": "NONE", "AuthorizerId": Match.absent(),
                "ApiKeyRequired": False, "Integration": Match.object_like({"Type": "MOCK"}),
            })
        else:
            expected.update({
                "AuthorizationType": "COGNITO_USER_POOLS",
                "AuthorizerId": {"Ref": authorizer_id},
                "Integration": Match.object_like({"Type": "AWS_PROXY"}),
            })
        template.has_resource_properties("AWS::ApiGateway::Method", expected)

    # Assert the discovered routes themselves, rather than guessing a method count.
    for resource_id in (root, proxy):
        for method in ("ANY", "OPTIONS"):
            template.has_resource_properties("AWS::ApiGateway::Method", {
                "ResourceId": resource_id, "HttpMethod": method,
                "RestApiId": {"Ref": api_id},
            })
