#!/usr/bin/env python3
import aws_cdk as cdk
from aws_cdk import Validations
# from cdk_nag import AwsSolutionsChecks

from hr_leave_portal.agent_runtime_stack import AgentRuntimeStack
from hr_leave_portal.backend_stack import BackendStack
from hr_leave_portal.notification_stack import NotificationStack
from hr_leave_portal.state_machine_stack import StateMachineStack
from hr_leave_portal.ui_stack import UiStack
from hr_leave_portal.dashboard_stack import DashboardStack

app = cdk.App()

# Uncomment to audit every stack against the AWS Solutions rule pack.
# Synth fails while findings are unacknowledged.
# Validations.of(app).add_plugins(AwsSolutionsChecks(app, verbose=True))

notifications = NotificationStack(app, "HrLeavePortalNotifications")

backend = BackendStack(
    app,
    "HrLeavePortalBackend",
    ui_origin="https://d1a282crm22ojw.cloudfront.net",
)

state_machine = StateMachineStack(
    app,
    "HrLeavePortalStateMachine",
    hr_email_topic=notifications.hr_email_topic,
    api_function=backend.api_function,
)

agent = AgentRuntimeStack(
    app,
    "HrLeavePortalAgentRuntime",
    table=backend.table,
    hr_email_topic=notifications.hr_email_topic,
    user_pool=backend.user_pool,
    user_pool_client=backend.user_pool_client,
)

UiStack(
    app,
    "HrLeavePortalUi",
    api_url=backend.api.url,
    user_pool_id=backend.user_pool.user_pool_id,
    user_pool_client_id=backend.user_pool_client.user_pool_client_id,
    # Reuse the deployed stack's public output without requiring an agent update.
    agent_runtime_arn=cdk.Fn.get_stack_output(
        agent.stack_name,
        "AgentRuntimeArn",
        region=cdk.Aws.REGION,
    ),
)

DashboardStack(
    app,
    "HrLeavePortalDashboard",
    api_function=backend.api_function,
    api=backend.api,
)

app.synth()