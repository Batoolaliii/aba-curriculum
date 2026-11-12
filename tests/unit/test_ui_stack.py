from pathlib import Path

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template
import pytest

from hr_leave_portal.ui_stack import UiStack


def build(**kwargs):
    return UiStack(
        cdk.App(),
        "Ui",
        api_url="https://api.example/prod/",
        user_pool_id="pool",
        user_pool_client_id="client",
        agent_runtime_arn=(
            "arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/test"
        ),
        **kwargs,
    )


def test_private_https_hosting_and_existing_resource_configuration(tmp_path):
    (tmp_path / "index.html").write_text("<html></html>", encoding="utf-8")
    template = Template.from_stack(build(ui_dist=str(tmp_path)))

    template.has_resource_properties(
        "AWS::S3::Bucket",
        {
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "BlockPublicPolicy": True,
                "IgnorePublicAcls": True,
                "RestrictPublicBuckets": True,
            }
        },
    )

    template.has_resource_properties(
        "AWS::CloudFront::Distribution",
        {
            "DistributionConfig": {
                "DefaultCacheBehavior": {
                    "ViewerProtocolPolicy": "redirect-to-https",
                },
                "CacheBehaviors": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "PathPattern": "/agentcore/*",
                                "CachePolicyId": (
                                    "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"
                                ),
                                "OriginRequestPolicyId": (
                                    "b689b0a8-53d0-40ab-baf2-68738e2966ac"
                                ),
                            }
                        )
                    ]
                ),
            }
        },
    )

    template.resource_count_is("AWS::BedrockAgentCore::Runtime", 0)
    template.resource_count_is("AWS::Cognito::UserPool", 0)
    template.resource_count_is("AWS::DynamoDB::Table", 0)

    template.has_resource_properties(
        "Custom::CDKBucketDeployment",
        {"SourceMarkers": Match.any_value()},
    )


def test_requires_prebuilt_ui():
    with pytest.raises(ValueError, match="UI build missing"):
        build(ui_dist="no-such-build")


def test_spa_rewrite_and_agent_prefix_removal_are_separate(tmp_path):
    (tmp_path / "index.html").write_text("<html></html>", encoding="utf-8")
    template = Template.from_stack(build(ui_dist=str(tmp_path))).to_json()

    functions = [
        resource["Properties"]["FunctionCode"]
        for resource in template["Resources"].values()
        if resource["Type"] == "AWS::CloudFront::Function"
    ]

    assert any("index.html" in source for source in functions)
    assert any(
        "agentcore" in source and "index.html" not in source
        for source in functions
    )
    assert Path("ui/README.md").is_file()
