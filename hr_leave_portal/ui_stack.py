"""Static UI hosting; consumes existing resources and never creates an agent."""
from pathlib import Path
from aws_cdk import (
    Aws, CfnOutput, Duration, RemovalPolicy, Stack,
    aws_cloudfront as cloudfront, aws_cloudfront_origins as origins,
    aws_s3 as s3, aws_s3_deployment as deployment,
)
from constructs import Construct


class UiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, api_url: str,
                 user_pool_id: str, user_pool_client_id: str,
                 agent_runtime_arn: str, ui_dist: str = "ui/dist", **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        if not (Path(ui_dist) / "index.html").is_file():
            raise ValueError("UI build missing: run npm run build in ui/ before CDK synthesis.")
        self.bucket = s3.Bucket(
            self, "UiAssets", block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED, enforce_ssl=True,
            removal_policy=RemovalPolicy.RETAIN,
        )
        static_origin = origins.S3BucketOrigin.with_origin_access_control(self.bucket)
        spa = cloudfront.Function(self, "SpaNavigation", code=cloudfront.FunctionCode.from_inline(
            "function handler(event) { var r = event.request; "
            "if (r.uri === '/' || r.uri.split('/').pop().indexOf('.') === -1) r.uri = '/index.html'; "
            "return r; }"
        ))
        strip_prefix = cloudfront.Function(self, "AgentPath", code=cloudfront.FunctionCode.from_inline(
            "function handler(event) { var r = event.request; "
            "r.uri = r.uri.replace(/^\\/agentcore/, ''); return r; }"
        ))
        policy = cloudfront.ResponseHeadersPolicy(self, "UiSecurityHeaders",
            security_headers_behavior=cloudfront.ResponseSecurityHeadersBehavior(
                content_type_options=cloudfront.ResponseHeadersContentTypeOptions(override=True),
                frame_options=cloudfront.ResponseHeadersFrameOptions(frame_option=cloudfront.HeadersFrameOption.DENY, override=True),
                referrer_policy=cloudfront.ResponseHeadersReferrerPolicy(referrer_policy=cloudfront.HeadersReferrerPolicy.NO_REFERRER, override=True),
                strict_transport_security=cloudfront.ResponseHeadersStrictTransportSecurity(access_control_max_age=Duration.days(365), include_subdomains=True, override=True),
            ))
        self.distribution = cloudfront.Distribution(self, "UiDistribution",
            default_root_object="index.html",
            default_behavior=cloudfront.BehaviorOptions(
                origin=static_origin, viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                response_headers_policy=policy,
                function_associations=[cloudfront.FunctionAssociation(function=spa, event_type=cloudfront.FunctionEventType.VIEWER_REQUEST)],
            ), additional_behaviors={
                "/agentcore/*": cloudfront.BehaviorOptions(
                    origin=origins.HttpOrigin(f"bedrock-agentcore.{Aws.REGION}.{Aws.URL_SUFFIX}",
                        protocol_policy=cloudfront.OriginProtocolPolicy.HTTPS_ONLY,
                        read_timeout=Duration.seconds(60)),
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.HTTPS_ONLY,
                    allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                    cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                    # This managed policy forwards Authorization, session ID and query strings,
                    # while replacing the viewer Host with the AgentCore origin hostname.
                    origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
                    function_associations=[cloudfront.FunctionAssociation(function=strip_prefix, event_type=cloudfront.FunctionEventType.VIEWER_REQUEST)],
                ),
            })
        deployment.BucketDeployment(self, "DeployUi", destination_bucket=self.bucket,
            sources=[deployment.Source.asset(ui_dist), deployment.Source.json_data("config.json", {
                "apiUrl": api_url, "userPoolId": user_pool_id,
                "userPoolClientId": user_pool_client_id, "agentRuntimeArn": agent_runtime_arn,
                "region": Aws.REGION, "agentBaseUrl": "/agentcore",
            })], distribution=self.distribution, distribution_paths=["/*"],
            cache_control=[deployment.CacheControl.no_cache()],
        )
        CfnOutput(self, "UiUrl", value=f"https://{self.distribution.distribution_domain_name}")
        CfnOutput(self, "UiBucketName", value=self.bucket.bucket_name)
        CfnOutput(self, "UiDistributionId", value=self.distribution.distribution_id)
