# Delivery Configuration — Preparation Only

## Current State

No existing .github pipeline was found. scripts/build_layer.sh and scripts/build_and_push_agent.sh publish existing backend assets and are not part of UI verification. Express omitted CI Pipeline and Infrastructure Design; the reviewed code and tested Python CDK stacks are the deployment evidence. No automated AWS deployment job is installed or enabled.

## Local Release Candidate Checks

From ui/: npm ci; npx vitest run src/services.test.ts src/App.test.tsx; npm run lint; npm run build. Run each separately. Before a shared artifact build, ensure local VITE variables are not baked into production: production uses generated config.json. Do not modify or delete a person's .env.local without their direction; build in a clean checkout instead.

From root: uv sync --dev; uv run pytest tests/unit/test_api_routes.py tests/unit/test_ui_stack.py tests/unit/test_hr_leave_portal_stack.py; uv run python app.py. Each is a separate command. This locally synthesizes all stacks, without AWS lookups or deployment.

## Artifact and Future Promotion Contract

Release candidate consists of matching source revision, ui/dist assets, synthesized cloud assembly, test evidence and configuration manifest. Record a source commit plus working-tree patch identity for any dirty checkout; never label an uncommitted build with HEAD alone. Keep the previous working artifact/configuration together for rollback. No artifact has been uploaded or released here.

The UI stack is HrLeavePortalUi; existing dependencies retain names HrLeavePortalBackend, HrLeavePortalAgentRuntime, HrLeavePortalNotifications and HrLeavePortalStateMachine. Runtime-generated config uses existing API/pool/client/runtime references; no AWS keys in browser assets. Future account/region and installed CDK CLI version must be verified against the lockfile and current AWS guidance before live commands are chosen. No deploy command is run or automatically triggered by these notes.

## Security Assessment

Private encrypted S3 uses OAC and SSL enforcement; CloudFront exposes only intended static assets/config and the authenticated AgentCore path. The agent origin forwards authorization/session headers and disables caching. API remains Cognito-protected with its existing broad trusted-staff admission; there is no new role or ownership boundary. Public configuration is not a secret store. Preserve the existing table/pool/runtime and do not recreate them to fix release issues. IAM changes are confined to CDK's asset delivery/storage access; review synthesized resource/IAM differences before any separately authorized rollout.
