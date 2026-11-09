# Test Instructions

Methodology: test-after. Minimal requirement-driven coverage, happy path per component, plus two error/edge cases per test file. No numeric coverage floor is configured by this contract; do not weaken any existing threshold.

Runner readiness: npm install in ui/ after adding vitest, jsdom, @testing-library/react, @testing-library/user-event and @testing-library/jest-dom. Use uv sync --dev if Python dependencies are missing; add httpx only if required by API TestClient.

Run from ui/: npx vitest run src/services.test.ts src/App.test.tsx

Run from project root: uv run pytest tests/unit/test_api_routes.py tests/unit/test_ui_stack.py tests/unit/test_hr_leave_portal_stack.py

Baseline uses the existing Python test file before repair, npm run build and npm run lint from ui/. Final validation also runs UI production build/lint and offline CDK synthesis. No deployment or AWS mutation commands.

Mock Amplify auth, fetch/stream responses and API service persistence/workflow calls. Test data is synthetic; never use credentials or live HR data. Assert authenticated calls, failed auth, employee creation/filtering, leave updates/date validation, asynchronous acceptance IDs, streaming chunk splits/new sessions/cancellation, missing setup, and private hosting configuration. Every FR and NFR needs one meaningful test or documented concrete validation; FR7 includes instructions/config checks. Keep existing tests green or explicitly record pre-existing failures.
