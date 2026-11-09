# Code Structure

- app.py: composition root for four Python CDK stacks.
- hr_leave_portal/: backend resources, notifications, workflow definition wiring, agent runtime.
- api/handler.py: FastAPI application, CORS, routers, Mangum entrypoint.
- api/models.py: Pydantic request models.
- api/controllers/: employee, HR request, and currently unregistered leave routes.
- api/services/: DynamoDB employee/leave access and Step Functions start operations.
- state_machines/hr_state_machine_definition.json: JSONata choice, email construction/model call, SNS, metrics.
- hrAgent/app/agent/: main streaming entrypoint, payload normalization, model, optional memory, employee/leave/email tools, container and Python manifest.
- hrAgent/agentcore/: generated AgentCore application settings plus alternate TypeScript CDK app.
- ui/: React starter, CSS/static assets, Vite/TypeScript/ESLint configuration, npm manifest and lockfile.
- scripts/: layer publication and agent image build/push scripts; both mutate AWS and were not run.
- tests/unit/: stale CDK scaffold tests.
- src/hr_leave_portal/: packaging placeholder main; tools/employee_tools.py empty.

Python uses snake_case modules/functions and CDK stack classes. API payloads mix camelCase employee/leave fields with snake_case workflow fields. UI uses functional components, single quotes, no semicolons, and CSS files. See dependencies.md for import relationships.

