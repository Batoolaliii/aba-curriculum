# Cross-Unit Traceability

Result from sensor-traceability: PASS, uncovered []. Express has no Units; code-generation owns one implementation iteration. Structural coverage does not prove live deployment behavior.

| ID | Owning stage | Target file | Evidence |
|---|---|---|---|
| FR1 | code-generation | ui/src/App.tsx | App.test.tsx and services.test.ts, mocked auth/jsdom |
| FR2 | code-generation | ui/src/Portal.tsx | App.test.tsx, jsdom employee flow |
| FR3 | code-generation | api/handler.py | test_api_routes.py and App.test.tsx |
| FR4 | code-generation | ui/src/Portal.tsx | App.test.tsx asynchronous acceptance contracts |
| FR5 | code-generation | ui/src/services.ts | services.test.ts chunk/token/session checks; App.test.tsx cancel/new session |
| FR6 | code-generation | hr_leave_portal/ui_stack.py | test_ui_stack.py and offline synthesis |
| FR7 | code-generation | ui/README.md | Config validation tests and documentation review |
| NFR1 | code-generation | tests/unit/test_api_routes.py | API/backend regressions pass; baseline recorded |
| NFR2 | code-generation | ui/src/App.css | Responsive CSS and jsdom inspection only; real-browser target Unverified |
| NFR3 | code-generation | ui/src/App.test.tsx | All named suites plus lint/type/build pass |

All IDs are built and mapped; no uncovered elements. Real-browser responsive/accessibility behavior is not established by Node/jsdom evidence and remains a stated verification gap.
