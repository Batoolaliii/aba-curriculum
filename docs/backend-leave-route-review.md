# Backend leave route deployment review

Prepared 2026-11-09. Nothing deployed; no employee data changed. The CDK comparison used read-only template diff mode, not a CloudFormation change set:

```sh
cdk diff HrLeavePortalBackend --exclusively --no-change-set --no-lookups --app 'uv run python app.py'
```

## Reviewed changes

- Update existing Lambda ApiFunctionCE271BD4 code asset from a5d3876ae66799e823380d377665ff006ad992e70c70d7e1db88151b3a32d972.zip to 0a33ce2c5fd9ce9d87a0b8277387e215ea5d18f95e2b2780d79703f3024a7757.zip. Matching asset-path metadata changes as well.
- Add outputs PublishOutputRefHrApiAC1A9B33B6A94844 and PublishOutputRefHrApiDeploymentStageprod0007C856ADD3C6F2. These publish references to the existing API ID and prod stage for the separately prepared UI stack; they create no API or stage resources.
- No resource additions, removals or replacements; no IAM, Cognito, DynamoDB, Lambda configuration/layer/environment or API Gateway route changes in the template diff.

Downloaded the deployed Lambda archive into memory and compared every non-cache file with api/: only handler.py differs. No added or removed packaged source files. The source change registers the existing leave_controller.router, removes a duplicate employee_controller import and adds a final newline. Controller/service code already exists in the deployed package.

Registering this router exposes GET and POST /employees/{employee_id}/leave and PUT /employees/{employee_id}/leave/{start_date} through the existing FastAPI/Mangum Lambda proxy. The existing Cognito protection, CORS and table grants remain unchanged. No new Gateway resource or API-stage deployment is needed because the proxy already forwards those paths to Lambda. Registration exposes all three defined methods, not only the read method.

## Later deployment, only after authorization

Use the intended AWS account and us-east-1 region and rerun the read-only diff if source, SSM layer parameter, dependencies or deployed infrastructure changed. Confirm the diff still matches the above. Then the backend-only command from the repository root would be:

```sh
cdk deploy HrLeavePortalBackend --exclusively --no-lookups --app 'uv run python app.py'
```

This command was NOT run. It would upload the new Lambda asset and update the backend stack. Do not use --all, deploy the UI/agent stacks, bootstrap, publish layers or push agent images for this route fix. The app synthesizes other stacks locally, but --exclusively restricts the deployment to the named backend stack. Existing deploy-role/asset-publish permissions are required; do not change bootstrap IAM merely to bypass a permission error.

After an authorized rollout, use the UI's existing signed-in session to GET leave for employee 35807c84 with no month and with month=2026-10. Expect the existing 2026-10-29 record; month=2026-11 legitimately excludes it. Verify expired/unauthenticated requests remain denied. Do not POST/PUT merely to smoke-test this read-path fix. Rollback, if needed, is a backend update to the previous Lambda code asset through the normal release process, not deletion of the table, pool or stack.

## UI fix and verification

Portal.tsx now stores leave errors separately from an empty successful result. Failed fetches show a contextual error with Refresh guidance and hide stale/empty records. A successful retry clears the error. Monotonic request IDs prevent earlier responses from overriding newer employee/month/refresh requests.

- Vitest: 16 passed (includes failed request/retry and failed month-filter regressions).
- ESLint and TypeScript/production build: passed; existing large-bundle warning remains.
- Mocked API route tests: 3 passed; existing Starlette/httpx warning remains.
- git diff --check: passed.
- Backend CDK template diff: succeeded. CDK could not assume its lookup role, but completed with existing same-account credentials. Node 26 jsii compatibility warning remains. No roles were changed.

No browser visual test or live authenticated API smoke was run for this fix. The running Vite server picks up the UI source change locally.
