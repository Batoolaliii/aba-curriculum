# Test Results

Verification rerun after Code Generation approval, 2026-11-09. Commands captured through tool results; no external services were exercised.

| Command | Directory | Exit | Result |
|---|---|---|---|
| npm run build | ui/ | 0 | tsc -b and Vite succeed; 1404 modules; JS 821.73 kB, gzip 225.60 kB; large-chunk warning |
| npm run lint | ui/ | 0 | No lint failures |
| npx vitest run src/services.test.ts src/App.test.tsx | ui/ | 0 | 2 files, 14 passed, 0 failed, 0 skipped; Vitest 5.1.0/jsdom |
| uv run pytest tests/unit/test_api_routes.py tests/unit/test_ui_stack.py tests/unit/test_hr_leave_portal_stack.py | root | 0 | 8 passed, 0 failed, 0 skipped; Python 3.14.4/pytest 8.4.2; Starlette/httpx warning |
| uv run python app.py | root | 0 | Full local CDK synthesis, SSM tokens retained for deployment; Node 26 untested warning |
| git diff --check | root | 0 | No whitespace errors |
| aidlc engine sensor-traceability --stage build-and-test | root | 0 | pass=true; uncovered=[]; all FR1–FR7 and NFR1–NFR3 mapped |

Initial sandbox uv test attempt could not acquire its existing user cache lock on a read-only filesystem. Re-run with filesystem approval succeeded; this was an environment-access issue, not a test failure. Offline synthesis used the same approved cache access.

Baseline before implementation: UI build/lint passed; Python collection failed on removed HrLeavePortalStack import. Updated scaffold tests now validate actual stacks. No baseline failure was hidden by skipping tests.

Coverage percentage was not measured: the current Testing Contract defines a requirement-driven Minimal strategy and no numeric floor. Requirement coverage is 10/10 mappings; this is not a line-coverage percentage. Target matrix is finalized in build-and-test-summary.md: T1–T5/T7–T8 Met, T6 Unverified (real browser unavailable), T9–T10 N/A for stated reasons. No other applicable target remains Pending.

No live AWS integration, deployment, load testing, real-browser rendering or real keyboard/screen-reader validation was performed. Authenticator is mocked for UI component tests; service token paths and auth errors are tested independently. Browser gap remains visible for human approval. No loop-back needed.
