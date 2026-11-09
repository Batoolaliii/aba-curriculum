# UI deployment readiness review

Prepared 2026-11-09. No deployment, change-set creation or AWS resource mutation was performed. Existing UI styling, layouts and behavior are preserved.

## Readiness and scope

The UI is prepared for an explicitly authorized UI-only deployment in us-east-1 in the same account as the current backend/agent. It has not been deployed or verified in a real browser through CloudFront. The prior backend route deployment is already complete; this task makes no backend changes.

One release blocker was corrected in app.py: UI configuration now reads the existing HrLeavePortalAgentRuntime.AgentRuntimeArn CloudFormation output instead of an undeployed generated PublishOutput. The runtime itself is unchanged. All five generated config output references were checked against deployed stacks: none are missing.

## Checks run

| Check | Result |
|---|---|
| VITE_API_URL= npm run build, from ui/ | Pass, TypeScript and production build; runtime config branch selected without editing local env |
| npm run lint, from ui/ | Pass |
| npx vitest run src/services.test.ts src/App.test.tsx | 16 passed |
| uv run pytest tests/unit/test_api_routes.py tests/unit/test_ui_stack.py tests/unit/test_hr_leave_portal_stack.py | 8 passed |
| UI assertions rerun after reference correction | 3 passed |
| Read-only CDK diff and synthesis | Pass |
| Existing-output reference validation | 5 references; 0 missing |
| git diff --check | Pass |

Diff command (not deployment):

```sh
cdk diff HrLeavePortalUi HrLeavePortalBackend HrLeavePortalAgentRuntime --exclusively --no-change-set --no-lookups --app 'uv run python app.py'
```

Backend: no differences. Agent: no infrastructure differences; CDK's default hides metadata-only differences. UI: new resources only. No employee records or live agent sessions were accessed by these checks.

## New resources

- One retained S3 bucket for built UI and public config.json; SSE-S3 encryption, all public access blocked and bucket policy denies non-TLS requests.
- One CloudFront distribution using its default HTTPS cloudfront.net hostname/certificate, with an S3 Origin Access Control. No custom domain, ACM certificate, DNS zone or WAF is created.
- Two CloudFront Functions: SPA navigation rewrite for static requests, and /agentcore prefix removal for the separate HTTPS AgentCore origin.
- One response-headers policy for static UI security headers (HSTS, no sniffing, frame deny, no referrer).
- CDK asset-delivery machinery: one deployment Lambda, AWS CLI layer, IAM role/policy, log group and bucket-deployment custom resource. These perform asset upload/pruning and CloudFront invalidation during releases; they are not a continuously running application server. CDK metadata is also synthesized.
- Outputs UiUrl, UiBucketName and UiDistributionId.

No new Cognito pool/client, API, data table, workflow, SNS topic or AgentCore runtime. No backend or agent resource replacement.

## IAM and security review

CloudFront can read UI objects only for this distribution ARN. The deployment role can read bootstrap assets and manage objects in this new UI bucket, including deletion for deployment pruning. It cannot modify the HR table or agent. CDK's invalidation permission uses resource * for CreateInvalidation/GetInvalidation; this is the main broad action scope in the new role. The Lambda role also has basic execution-log permissions.

The UI shell and public identifiers are publicly served; HR APIs and agent requests require existing Cognito credentials. This remains trusted-staff access, not per-employee ownership. Agent proxy forwards bearer/session headers and query strings without caching, and excludes the viewer Host header. Do not put secrets in config.json. The stack does not add browser telemetry, monitoring alarms or access logging; operational instrumentation remains future work. Retained bucket storage can continue to cost money after stack deletion.

## Required configuration

- Existing backend ApiUrl with prod stage, user-pool ID and client ID, existing AgentRuntimeArn and us-east-1 region. All are wired into generated config.json; no manual production .env file is needed.
- Keep VITE_API_URL empty for the production artifact. The local .env.local was preserved. The production build already uses runtime configuration; a later ordinary npm run build in this checkout would replace that artifact with a local-override build.
- Existing Cognito staff accounts; signup remains disabled. Current password/SRP sign-in needs no hosted-UI callback-domain change. Authenticated live-browser sign-in/expiry and AgentCore streaming still need smoke checks after an authorized release.
- Existing bootstrap assets/roles, SSM layer/image parameters used by root synthesis, and permissions to create the listed UI resources, pass the deployment Lambda role and publish assets. No new bootstrap or image/layer publication was attempted.

## Costs — planning estimate, not a quote

The existing stack uses ordinary usage-based CloudFront distribution billing; it does not enroll a flat-rate plan. With a small staff audience, tiny asset storage and remaining shared CloudFront free allowances, allow roughly $1–$5/month for UI hosting as a conservative initial budget; actual incremental cost may be below $1. This estimate excludes API/Cognito/DynamoDB/SNS/workflow usage, AgentCore/Bedrock model costs, tax and support. Agent usage can exceed the hosting bill. No account billing allowance/discount data was queried.

Illustrative low-traffic scenario: 100,000 static/config requests per month and less than 1 GB transfer/storage. S3 Standard GETs are $0.0004 per 1,000, so even if every request reaches S3, 100,000 GETs cost about $0.04, plus storage, deploy-time PUT/LIST and asset/log storage. Both static assets and config currently disable caching, so expect origin GETs rather than assuming cache savings. Deployment Lambda/logging and occasional invalidations add small usage-based charges; storage and request counts determine actual totals.

CloudFront's advertised pay-as-you-go allowance is 1 TB outbound, 10 million HTTP(S) requests and 2 million Functions invocations monthly, shared across the relevant account/organization. Existing workloads may consume it. Proxy requests/data transfer to origin are not all covered by those free categories. Beyond allowances, rates vary by viewer geography; current Middle East outbound tier is $0.110/GB after the first free TB, and HTTPS requests are $0.012 per 10,000 after the free request tier. Do not interpret this as an all-in cost cap.

Sources checked 2026-11-09:
- https://aws.amazon.com/cloudfront/pricing/pay-as-you-go/
- https://aws.amazon.com/cloudfront/faqs/ (free-tier sharing and excluded proxy usage)
- https://aws.amazon.com/s3/pricing/ (S3 Standard GET example and transfer-to-CloudFront exemption)

## Future UI-only command — not run

After explicit authorization, using the reviewed build and account/region:

```sh
cdk deploy HrLeavePortalUi --exclusively --no-lookups --app 'uv run python app.py'
```

Do not use --all or deploy backend/agent dependencies. Rerun the read-only diff if source, public config references or assets change. There is no fixed CloudFront URL until deployment creates the distribution.

After deployment: verify HTTPS, config values, SPA navigation, Cognito sign-in/expiry, read-only employee/leave views and streamed chat/session/error behavior. Do not test writes or notifications without permission. Check responsive/keyboard behavior in a real browser. Rollback uses the previous complete UI asset/config pair and invalidation; for an initial failed release, withdraw the new UI distribution under explicit authorization rather than deleting backend resources. Bucket is retained and deployment pruning means a separate previous artifact must be retained for rollback.

Remaining warnings: roughly 822 kB minified JS bundle; existing dependency/React peer advisories; Node 26 jsii compatibility warning (Node 22/24 recommended); Starlette/httpx deprecation. No forced upgrades or design changes were introduced. CDK lookup-role assumption failed but read-only comparisons succeeded using same-account credentials; deploy permissions are not proven by a diff.
