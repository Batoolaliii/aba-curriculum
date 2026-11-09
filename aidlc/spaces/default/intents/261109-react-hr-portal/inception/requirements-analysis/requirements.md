# Requirements

## Intent Analysis

Build a working React interface for trusted HR staff using the existing backend and AgentCore hrAgent. Extend the existing React/Vite/Amplify starter, preserve working functionality and resource identities, and provide a Python CDK UI stack and local run instructions. No AWS deployment is authorized. [desc] [Q1] [Q2]

## Sources

- [desc] Initial description: project-description.json, retrieved with the project-description utility; reiterated no AWS deployment in chat.
- [scope] Workflow-selected scope: express; Minimal depth and test strategy.
- [Q1] requirements-analysis-questions.md: full portal and registration of existing leave routes.
- [Q2] requirements-analysis-questions.md: trusted HR staff; retain existing authorization model.
- Existing-code context: aidlc/spaces/default/codekb/hr-leave-portal/ (business-overview.md, architecture.md, code-structure.md, api-documentation.md).

## Functional Requirements

### FR1 — Existing Cognito sign-in [desc] [Q2]

Reuse the existing user pool and client for sign-in, any required password challenge, session restoration and sign-out. No self-registration UI. Given valid staff credentials, signing in opens the portal; invalid or expired credentials show an actionable error or return to sign-in. Signed-out users cannot load authenticated records or send chat messages. Browser configuration contains public identifiers only.

### FR2 — Employee directory and creation [Q1]

List employees, filter by the existing hiredFrom/hiredTo date range, select an employee and create an employee using existing fields (name, department, startDate and role). Given a valid form, creation calls the existing API and refreshes the directory; blank required values and inverted date ranges prevent submission. Empty results and API errors have visible states and retry options. Do not claim pagination or deletion support absent from the API.

### FR3 — Employee leave records [Q1]

Register and reuse the existing leave router. For a selected employee, list leave with optional month filtering, create a leave record and update its end date and note using the existing employee/start-date keys. Valid submissions refresh records; end-before-start and malformed dates prevent submission. Failed requests preserve entered data and show errors. Preserve existing employee and HR request endpoints with regression checks.

### FR4 — Time-off and general HR requests [Q1]

Submit time-off dates or a general HR prompt for the selected employee using existing endpoints and field names. Display the returned workflow execution identifier as an accepted asynchronous request. Empty prompts and invalid date ranges prevent submission. Show API errors; never imply that acceptance means approval, delivery or workflow completion. Do not add polling without a backend status API.

### FR5 — AgentCore hrAgent chat [desc] [Q1] [Q2]

Integrate the existing runtime and its Cognito authorization. Send prompts with a stable conversation session identifier and an appropriate actor identifier; parse streamed responses into readable assistant text without exposing raw tool payloads. Provide sending, cancellation, error and new-conversation states. Disable duplicate sends while a response is active. A new conversation creates a new session; authorization failures require renewed sign-in. Staff can see that the agent can change employee/leave data and send HR notifications; a conversation is distinct from the asynchronous HR request form. Never put AWS credentials or client secrets into browser assets.

### FR6 — CDK UI hosting and configuration [desc]

Add a UI hosting stack following the existing Python CDK conventions, consuming existing API, Cognito and runtime references without replacing backend resources. Serve the built SPA over HTTPS with private static storage and SPA navigation support. Provide public runtime/build configuration and outputs needed to connect the UI. Synthesis must demonstrate resource wiring and constrained static-asset access. Preserve the existing agent deployment choice; do not create another runtime, pool or backend table.

### FR7 — Local run and verification documentation [desc]

Document prerequisites, dependency installation, public configuration values and where to obtain them, local dev/build/test commands, and the distinction between local checks and future deployment. Missing configuration produces a clear setup message. Local development can use already deployed backend resources; no AWS changes are required by the local instructions. Explain trusted-staff access and agent side effects.

## Non-Functional Requirements

### NFR1 — Preserve functionality and resource identities [desc]

Run applicable baseline checks before changing application code and repeat relevant checks afterwards. Record pre-existing failures separately and fix regressions from this change. Existing working endpoint contracts and CDK resource identities remain compatible. Changes stay limited to UI integration, required backend wiring, deployment preparation and associated tests/docs.

### NFR2 — Usability and resilience [desc] [Q1]

Core screens work at 375px and 1280px viewport widths without horizontal page overflow. Forms have associated labels, keyboard-operable controls, visible focus and accessible status/error announcements. All API-driven views show loading, empty and failure states. Display model text safely as text or sanitized content, never executable HTML.

### NFR3 — Requirement-driven checks [scope] [desc]

Run UI type checks, lint, production build and targeted requirement tests; run backend regressions and CDK synthesis/assertions relevant to integration. Include happy-path coverage for each added component and tests for authentication failure, request validation, streamed text/session handling and infrastructure configuration. Record commands, outcomes and any checks that cannot run. Do not call AWS deploy, bootstrap, image push, layer publication or other AWS mutation commands.

## Constraints

- React UI in existing ui/; existing Python CDK project conventions. [desc]
- Trusted HR staff only. Cognito authentication is retained; per-employee ownership and HR role authorization are not added. All admitted users must be trusted with the existing API and agent powers. [Q2]
- No AWS deployment or AWS resource mutation. CDK and any pipeline work are preparation only; actual deployment execution is excluded until separately authorized. [desc]
- Reuse existing backend resources and AgentCore runtime; preserve existing agent deployment configuration. [desc]
- Request completion cannot be polled with existing API; do not invent status outcomes. [Q1]

## Out of Scope

Employee self-service ownership, new approval workflows, employee deletion API, leave deletion API, pagination APIs, new agent deployment, AWS deployment, and production validation against resources that do not yet exist. Existing unrelated defects are documented unless needed to make this integration work. [desc] [Q1] [Q2]

## Assumptions & Open Questions

None. Runtime identifiers and public endpoint values are supplied through explicit configuration or stack references rather than guessed. Deployment-region and SDK details are implementation checks against existing source and official documentation, not additional product requirements.
