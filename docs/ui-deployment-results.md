# UI deployment results

2026-11-09: deployed only HrLeavePortalUi with the reviewed configuration and explicit user authorization. CloudFormation CREATE_COMPLETE.

URL: https://d1a282crm22ojw.cloudfront.net

Distribution: E23E5JJTQW72RZ. Backend and agent stacks were excluded with --exclusively; their LastUpdated timestamps remain earlier than this UI release. No employee data was created or modified, and no agent prompt was sent.

The first non-interactive CDK attempt published assets/prepared a change set but could not confirm reviewed IAM changes without a TTY. The same command was rerun interactively and the already-authorized UI IAM changes confirmed. Only the UI stack was deployed.

## Read-only smoke checks

| Check | Result |
|---|---|
| HTTPS root | 200; exact match to reviewed local index |
| Page title | People & Leave · HR Portal |
| Referenced JS and CSS | Both 200; byte-for-byte matches to reviewed build |
| SPA deep link /employees/35807c84 | 200; same index page |
| /config.json | 200; all six config fields match intended existing resources/region/proxy base; no-cache |
| Security headers | HSTS max-age=31536000 with subdomains; nosniff; frame DENY |
| Anonymous backend leave GET | 401, authentication still required |
| Agent proxy GET without token | 405 and non-HTML response; not rewritten to SPA; GET did not invoke agent |
| Anonymous direct S3 index access | 403, bucket private |

No Cognito user credentials/browser session were available to this check. Authenticated sign-in, actual streamed POST invocation and real-browser responsive behavior remain unverified. The agent GET response checks routing/method handling only and does not establish authenticated streaming or bearer-token rejection on POST. No write/notification workflow smoke checks were run.

The initial title check looked for the generic string HR Leave Portal and returned false; follow-up comparison confirmed the deployed page exactly matches the reviewed build and its intentional People & Leave · HR Portal title. No source or deployed asset changes were needed.
