import os

from strands.models.bedrock import BedrockModel


def load_model() -> BedrockModel:
    """Get Bedrock model client using IAM credentials."""
    return BedrockModel(
        model_id="us.amazon.nova-2-lite-v1:0",
        guardrail_id=os.environ["GUARDRAIL_ID"],
        guardrail_version=os.environ["GUARDRAIL_VERSION"],
        guardrail_trace="enabled",
    )