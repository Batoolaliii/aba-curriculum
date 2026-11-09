# Deployment Strategy — Not Executed

## Decision and Alternatives

Prepare a manually approved CDK release of the static UI using private S3 and CloudFront, reusing existing backend stacks. No release takes place in this task. Alternative automatic-on-merge deployment is not configured because the user excluded AWS deployment and no existing pipeline needs preservation. Blue/green/canary would introduce infrastructure and traffic-routing decisions beyond this request; no percentage rollout is claimed.

## Environment Promotion Matrix

| Environment | Current status | Gate before future promotion |
|---|---|---|
| Local | UI build and mocked tests verified | Public config and existing trusted staff credentials for manual use |
| Staging | No new environment deployed | Explicit deployment authorization, account/region, reviewed CDK change set, browser and live smoke checklist |
| Production | No deployment authorized | Separate release approval after staging validation and rollback readiness |

## Future Release Order

1. Identify existing resource outputs and deployment account/region; verify user pool admission and agent authorization match.
2. Build clean assets and synthesize; inspect differences for backend replacements and IAM/resource changes. Abort if existing pool/table/runtime replacement is proposed.
3. Separately authorize backend API router update and UI hosting deployment; registration must reach the live API before leave screens can succeed. Do not publish agent images/layers merely to deploy UI.
4. Validate config.json values, HTTPS, static assets, SPA navigation and auth expiry. In a real browser verify 375px/1280px layout, keyboard and focus behavior.
5. With synthetic HR data and permission for resulting notifications, verify employee create/filter, leave save/update, request execution acceptance and streamed agent text/new session/cancel. Check cross-user session separation and agent origin error handling. Clean test data only with explicit instructions.
6. Compare health/errors with baseline and record the release candidate identity and outputs.

## Abort Criteria

Abort or roll back on sign-in failure, sensitive data exposure, unexpected resource replacement, lost authenticated headers, static/config failures, repeated 5xx or broken leave endpoints. Do not promote with unverified browser or live integration behavior. No feature flag service is introduced; an authorized operator can withdraw the UI release through rollback. No automatic alarm/rollback configuration is claimed.
