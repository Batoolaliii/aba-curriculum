# Current backend-only deployment review

2026-11-09. Read-only CDK diff against the latest deployed backend; no deployment or employee-data modification performed.

## Changes since the last deployment

- Existing Lambda code asset changes from 0a33ce2c5fd9ce9d87a0b8277387e215ea5d18f95e2b2780d79703f3024a7757.zip to db3bd065f288b4602b6308c8cdfe4fd4a0df61cedb8a30e191de032edc139a7e.zip, with matching asset metadata (updated after the two findings were fixed).
- API Lambda gains POWERTOOLS_SERVICE_NAME=hr-api and POWERTOOLS_LOG_LEVEL=INFO. Existing TABLE_NAME and workflow environment references are retained.
- Lambda tracing changes from deployed PassThrough to Active.
- Existing Lambda execution-role policy gains xray:PutTelemetryRecords and xray:PutTraceSegments on resource *.
- No resource additions/removals/replacements, API Gateway route changes, table/schema changes, Cognito changes or stack-output changes. UI and agent stacks were not selected.

Read the deployed Lambda archive in memory and compared all non-cache files to api/. Four files differ; none added/removed:

| File | Pending changes |
|---|---|
| handler.py | Powertools Logger/Tracer setup; HTTP middleware logs method/path and response status; decorated Lambda wrapper; leave/HR router registration order adjusted |
| services/employee_service.py | Logger/Tracer setup and capture_method decorators; employee operations log identifiers, department, date filters, counts and found status; equivalent response locals/formatting |
| services/hr_request_service.py | Logger/Tracer setup, workflow method decorators and execution-ARN logging |
| services/leave_service.py | Logger/Tracer setup, leave method decorators and identifier/date/month logging; whitespace cleanup |

The leave router registration itself was already deployed in the preceding backend release; it is not a newly exposed endpoint in this diff. Data-access operations/payloads remain the same; new instrumentation adds logging and tracing effects.

## Findings resolved locally — not deployed

1. Removed the assignment that overwrote the decorated Lambda handler. A reusable Mangum adapter is now called by the exported handler with Logger context injection and Tracer handler capture intact. Regression test invokes the actual exported handler with a synthetic API Gateway event, checks the health response and request-ID context, and observes the tracer provider call.
2. Consolidated list_by_hire_date into one decorated function. It preserves no-bound, lower-only, upper-only and inclusive two-bound queries, logs requested filters and returned count, and propagates database errors. Parameterized tests inspect query expressions and verify logger/tracer calls without accessing AWS.

Both changes are local only. Existing identifier/date logging broadens telemetry content and should be considered when deciding log access/retention. No API routes, payload contracts or persistence operations were changed by these fixes.

## Dependencies and validation

Read-only inspection of the attached deployed fastapi:1 layer confirmed both aws_lambda_powertools and aws_xray_sdk are present. The CDK diff proposes no layer update. Local dev dependencies include aws-lambda-powertools[tracer]. scripts/build_layer.sh is capable of publishing a layer and updating SSM, but was not executed.

The earlier leave-service whitespace edit preserved Python AST and behavior. This follow-up also normalized whitespace in the touched employee service, with AST equality checked before/after normalization. Scoped git diff --check passed for the handler, employee service and targeted tests. Other pending service edits were preserved.

Backend regression tests: 11 passed (test_api_routes.py and test_hr_leave_portal_stack.py), including six new cases for the actual decorated Lambda entry point, four date-bound combinations and query failure propagation. CDK synthesis and the final backend-only template diff succeeded. Existing Starlette/httpx and Node 26 compatibility warnings remain. No resource additions/removals/replacements or layer changes; no UI/agent deployment. Live X-Ray delivery remains unverified until a separately authorized backend release.

Command used:

```sh
cdk diff HrLeavePortalBackend --exclusively --no-change-set --no-lookups --app 'uv run python app.py'
```

CDK lookup-role assumption was unavailable but the read-only comparison succeeded with existing same-account credentials. No change set or deployment was created.
