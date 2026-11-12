import aws_cdk as core
import aws_cdk.assertions as assertions

from hr_leave_portal.backend_stack import BackendStack
from hr_leave_portal.notification_stack import NotificationStack


def test_existing_backend_resources():
    app = core.App()
    stack = BackendStack(app, "HrLeavePortalBackend")
    template = assertions.Template.from_stack(stack)

    template.resource_count_is("AWS::DynamoDB::Table", 1)
    template.resource_count_is("AWS::Cognito::UserPool", 1)
    template.resource_count_is("AWS::ApiGateway::RestApi", 1)


def test_sns_topic_created():
    app = core.App(context={"hrEmail": "hr@example.com"})
    stack = NotificationStack(app, "HrLeavePortalNotifications")
    template = assertions.Template.from_stack(stack)

    template.resource_count_is("AWS::SNS::Topic", 1)