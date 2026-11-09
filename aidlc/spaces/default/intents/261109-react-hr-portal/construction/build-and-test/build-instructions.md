# Build Instructions

Use Node 22.12+ or 24 LTS, npm, Python 3.14+ and uv. Existing dependencies are installed; for a clean checkout use npm ci in ui/ and uv sync --dev at the root. No AWS credentials are needed for mocked checks or token-based offline synthesis. Local interactive use needs public identifiers in ui/.env.local and an existing Cognito staff account, as documented in ui/README.md.

Run from ui/ separately: npm run lint; npm run build; npx vitest run src/services.test.ts src/App.test.tsx.

From root: uv run pytest tests/unit/test_api_routes.py tests/unit/test_ui_stack.py tests/unit/test_hr_leave_portal_stack.py; then uv run python app.py. Build UI before synthesis. These semicolon-separated lists describe separate commands; no deployment is included.

Verify exit code zero, ui/dist/index.html and a local CDK cloud assembly. Missing dist means build UI first; missing config affects interactive use, not mocked tests. Use supported Node when investigating jsii warnings. The uv cache may require local filesystem access outside the checkout. Do not deploy, bootstrap, publish layers or push images.
