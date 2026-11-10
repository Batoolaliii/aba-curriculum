from aws_cdk import (
    CfnOutput,
    Stack,
    aws_kms as kms,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subscriptions,
)
from constructs import Construct


class NotificationStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        hr_email_address = self.node.try_get_context("hrEmail")
        if not hr_email_address:
            raise ValueError("Missing required context value: hrEmail")

        hr_email_topic = sns.Topic(
            self,
            "HrEmailTopic",
            master_key=kms.Alias.from_alias_name(
                self, "SnsKey", "alias/aws/sns"
            ),
        )

        hr_email_topic.add_subscription(
            sns_subscriptions.EmailSubscription(hr_email_address)
        )

        self.hr_email_topic = hr_email_topic

        CfnOutput(
            self,
            "HrEmailTopicArn",
            value=hr_email_topic.topic_arn,
        )