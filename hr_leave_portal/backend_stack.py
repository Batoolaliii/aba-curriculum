from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    aws_apigateway as apigw,
    aws_cognito as cognito,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_ssm as ssm,
)
from constructs import Construct

# The build script publishes the layer's Version ARN to this SSM parameter.
LAYER_ARN_PARAM = "/hr-leave-portal/fastapi-layer-arn"


class BackendStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        ui_origin: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        allowed_origins = ["http://localhost:5173"]
        if ui_origin:
            allowed_origins.append(ui_origin)

        table = dynamodb.Table(
            self,
            "HrTable",
            partition_key=dynamodb.Attribute(
                name="PK", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="SK", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True,
            ),
            removal_policy=RemovalPolicy.DESTROY,
        )

        table.add_global_secondary_index(
            index_name="GSI1",
            partition_key=dynamodb.Attribute(
                name="GSI1PK", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="GSI1SK", type=dynamodb.AttributeType.STRING
            ),
        )

        # Read the ARN the build script stored, resolved at synth time.
        fastapi_layer_arn = ssm.StringParameter.value_for_string_parameter(
            self, LAYER_ARN_PARAM
        )

        fastapi_layer = lambda_.LayerVersion.from_layer_version_arn(
            self, "FastApiLayer", layer_version_arn=fastapi_layer_arn
        )

        api_function = lambda_.Function(
            self,
            "ApiFunction",
            runtime=lambda_.Runtime.PYTHON_3_14,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("api", exclude=["__pycache__", "*.pyc"]),
            layers=[fastapi_layer],
            timeout=Duration.seconds(10),
            memory_size=512,
            environment={
                "TABLE_NAME": table.table_name,
                "POWERTOOLS_SERVICE_NAME": "hr-api",
                "POWERTOOLS_LOG_LEVEL": "INFO",
            },
            tracing=lambda_.Tracing.ACTIVE,
        )

        if ui_origin:
            api_function.add_environment("UI_ORIGIN", ui_origin)

        api_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "dynamodb:PutItem",
                    "dynamodb:GetItem",
                    "dynamodb:Query",
                    "dynamodb:DeleteItem",
                ],
                resources=[
                    table.table_arn,
                    f"{table.table_arn}/index/*",
                ],
            )
        )

        self.api_function = api_function
        self.table = table

        self.user_pool = cognito.UserPool(
            self,
            "HrUserPool",
            self_sign_up_enabled=False,
            sign_in_aliases=cognito.SignInAliases(email=True),
            removal_policy=RemovalPolicy.DESTROY,
        )

        self.user_pool_client = self.user_pool.add_client(
            "HrUserPoolClient",
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True,
            ),
        )

        authorizer = apigw.CognitoUserPoolsAuthorizer(
            self,
            "HrAuthorizer",
            cognito_user_pools=[self.user_pool],
        )

        self.api = apigw.LambdaRestApi(
            self,
            "HrApi",
            handler=api_function,
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=allowed_origins,
                allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            ),
            default_method_options=apigw.MethodOptions(
                authorization_type=apigw.AuthorizationType.COGNITO,
                authorizer=authorizer,
            ),
        )

        CfnOutput(self, "ApiUrl", value=self.api.url)
        CfnOutput(self, "TableName", value=table.table_name)
        CfnOutput(self, "UserPoolId", value=self.user_pool.user_pool_id)
        CfnOutput(
            self,
            "UserPoolClientId",
            value=self.user_pool_client.user_pool_client_id,
        )
