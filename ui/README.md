# HR Leave Portal UI

React + TypeScript + Vite staff workspace using the existing Cognito user pool, API Gateway backend and AgentCore hrAgent. This change prepares deployment; nothing has been deployed to AWS.

## Run locally

Prerequisites: Node.js 22.12+ or 24 LTS, npm, and credentials for an existing Cognito staff account. Python 3.14+ and uv are needed only for CDK/API checks. Self-registration is disabled.

1. From `ui/`, run `npm ci`.
2. Copy `.env.example` to `.env.local` and fill in the public identifiers from your **existing** stack outputs:
   - `VITE_API_URL`: `HrLeavePortalBackend.ApiUrl`, including the API stage (for example `/prod/`).
   - `VITE_USER_POOL_ID`: `HrLeavePortalBackend.UserPoolId`.
   - `VITE_USER_POOL_CLIENT_ID`: `HrLeavePortalBackend.UserPoolClientId`.
   - `VITE_AGENT_RUNTIME_ARN`: `HrLeavePortalAgentRuntime.AgentRuntimeArn` for the runtime already authorized for this user pool/client.
   - `VITE_AWS_REGION`: region hosting those resources.
3. Run `npm run dev` and open the localhost URL Vite prints (normally http://localhost:5173).
4. Sign in with your existing staff credentials. Amplify handles temporary-password, password-reset and other Cognito sign-in challenges.

All these values are public identifiers, not credentials. Never put AWS access keys, client secrets or passwords in Vite environment variables. `.env.local` is ignored by the existing UI gitignore. Restart Vite after editing it.

The Vite development proxy sends `/agentcore/*` to the configured region's AgentCore HTTPS endpoint and removes the prefix. It forwards bearer authorization and session headers. The backend API uses its existing CORS configuration. Local UI actions call real existing resources: employee/leave writes and HR notifications are real. If the current backend has not yet registered its leave router, leave calls will return 404 until that backend change is separately deployed; the local UI does not alter AWS infrastructure.

## Staff workflows

- Directory: list, search locally, filter by both hire dates, add employee.
- Employee workspace: select an employee, list leave (optional month), add or update records. Leave records and asynchronous time-off requests are distinct.
- HR requests: submit time off or a general question. An execution ARN means **accepted for processing**, not approved, completed or delivered. The backend has no result polling API.
- Assistant: streamed hrAgent text, stable session per conversation, new-conversation reset and cancellation. Stopping the response stops receiving text; server-side tool actions may still complete. Refresh directory/leave after agent actions.

This is for **trusted HR staff**. Existing Cognito admission grants broad API/agent access; there is no new per-user ownership or HR role enforcement. Restrict who gets accounts. Chat identifies the signed-in staff actor, not the selected employee, so employee references must be explicit in prompts. hrAgent can change/delete employee records, change leave and send HR notifications. AI output is displayed as text.

## Checks (no AWS mutations)

From `ui/`:

```sh
npx vitest run src/services.test.ts src/App.test.tsx
npm run lint
npm run build
```

From the repository root:

```sh
uv sync --dev
uv run pytest tests/unit/test_api_routes.py tests/unit/test_ui_stack.py tests/unit/test_hr_leave_portal_stack.py
uv run python app.py
```

Build UI before running CDK synthesis: the new UiStack rejects a missing `ui/dist/index.html`. `uv run python app.py` synthesizes the cloud assembly locally with SSM references resolved at deployment time; it does not perform lookups or deploy resources. Do **not** run cdk deploy, bootstrap, layer publication or image-push scripts as part of local verification.

The stack deploys the build plus a generated public `config.json` whose values reference the existing resources. Production loads that configuration without rebuilding identifiers into the application. Local Vite variables take precedence when supplied. For a production build in this checkout, run `VITE_API_URL= npm run build` (POSIX shell). This disables the local configuration branch for that build without editing `.env.local`, so production loads stack-generated configuration. Alternatively build in a clean checkout with no local Vite overrides. Do not rebuild with the ordinary local command immediately before a release, as that would bake local configuration back into the artifact.

## Hosting prepared for later

`hr_leave_portal/ui_stack.py` creates a retained private S3 asset bucket with CloudFront Origin Access Control and HTTPS distribution. SPA navigation rewrite applies only to static requests. A separate uncached `/agentcore/*` behavior proxies AgentCore without the viewer Host header, forwards authorization/session headers and query strings, and preserves HTTP errors and streamed text. Static/config responses are not cached; a future optimization can add immutable caching to hashed assets.

The root Python CDK app adds `HrLeavePortalUi` using references to existing backend and agent stacks; it does not duplicate the pool, API, table, workflow, SNS topic or runtime. Outputs: `UiUrl`, `UiBucketName`, `UiDistributionId`. Future deployment needs separate authorization, existing SSM layer/image parameters and a built UI. Synthesizing does not prove live Cognito/API/AgentCore authorization or CloudFront streaming. Test those after an authorized deployment. No real credentials, live integration tests or browser QA were available during this change.

The UI reads the deployed agent stack's existing `AgentRuntimeArn` output directly. It does not require publishing an additional agent output or updating that stack. See `docs/ui-deployment-review.md` for the latest pre-deployment checks, resource/IAM review, expected costs and a UI-only release command. UI deployment remains subject to separate authorization.

## Integration references

- [AWS: Invoke an AgentCore Runtime agent](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-invoke-agent.html): OAuth invocation uses HTTPS rather than the AWS SDK, with sessions and SSE.
- [Amplify: connect to existing resources](https://docs.amplify.aws/react/frontend/connect-to-existing-resources/): manually configure the existing user pool/client.
- [Amplify Authenticator configuration](https://ui.docs.amplify.aws/react/connected-components/authenticator/configuration): connected sign-in and challenge handling.

The existing dependency set emits Amplify/XState React peer warnings, and npm reports moderate dependency advisories. No forced dependency upgrades were made.
