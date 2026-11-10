from aws_cdk import (
    Aws,
    CfnOutput,
    Fn,
    Stack,
    aws_bedrockagentcore as agentcore,
    aws_cognito as cognito,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_sns as sns,
    aws_ssm as ssm,
)
from constructs import Construct

# build_and_push_agent.sh stores the pushed image URI in this SSM parameter.
AGENT_IMAGE_URI_PARAM = "/hr-leave-portal/agent-image-uri"
AGENT_MODEL_ID = "us.amazon.nova-2-lite-v1:0"


class AgentRuntimeStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        table: dynamodb.Table,
        hr_email_topic: sns.Topic,
        user_pool: cognito.IUserPool,
        user_pool_client: cognito.IUserPoolClient,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        model_resources = [
            f"arn:aws:bedrock:{Aws.REGION}:{Aws.ACCOUNT_ID}:inference-profile/{AGENT_MODEL_ID}",
            "arn:aws:bedrock:*::foundation-model/amazon.nova-2-lite-v1:0",
            f"arn:aws:bedrock:{Aws.REGION}:{Aws.ACCOUNT_ID}:inference-profile/global.anthropic.claude-sonnet-5",
            "arn:aws:bedrock:*::foundation-model/anthropic.claude-sonnet-5",
        ]

        agent_image_uri = ssm.StringParameter.value_for_string_parameter(
            self, AGENT_IMAGE_URI_PARAM
        )

        agent_artifact = agentcore.AgentRuntimeArtifact.from_image_uri(
            agent_image_uri
        )

        cognito_auth = agentcore.RuntimeAuthorizerConfiguration.using_cognito(
            user_pool, [user_pool_client]
        )

        agent_runtime = agentcore.Runtime(
            self,
            "HrAgentRuntime",
            runtime_name="hrAgent",
            agent_runtime_artifact=agent_artifact,
            protocol_configuration=agentcore.ProtocolType.HTTP,
            authorizer_configuration=cognito_auth,
            environment_variables={
                "TABLE_NAME": table.table_name,
                "HR_EMAIL_TOPIC_ARN": hr_email_topic.topic_arn,
            },
        )

        agent_runtime.add_to_role_policy(
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

        hr_email_topic.grant_publish(agent_runtime.role)

        agent_runtime.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                ],
                resources=model_resources,
            )
        )

        repo_with_tag = Fn.select(1, Fn.split("/", agent_image_uri))
        agent_repo_name = Fn.select(0, Fn.split(":", repo_with_tag))

        agent_runtime.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ecr:GetAuthorizationToken"],
                resources=["*"],
            )
        )

        agent_runtime.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "ecr:BatchGetImage",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchCheckLayerAvailability",
                ],
                resources=[
                    f"arn:aws:ecr:{Aws.REGION}:{Aws.ACCOUNT_ID}:repository/{agent_repo_name}"
                ],
            )
        )

        self.agent_runtime_arn = agent_runtime.agent_runtime_arn

        CfnOutput(
            self,
            "AgentRuntimeArn",
            value=agent_runtime.agent_runtime_arn,
        )
