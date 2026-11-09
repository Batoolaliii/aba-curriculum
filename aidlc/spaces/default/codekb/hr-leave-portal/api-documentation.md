# API Documentation

## Authentication and middleware
BackendStack configures Cognito authorization on API Gateway default methods and wildcard CORS preflight. FastAPI also allows all origins/methods/headers. Existing Cognito client enables user_password and user_srp; self signup is disabled. Health is named public in FastAPI but gateway default authorization still applies.

## Registered API routes
| Method/path | Input | Success |
|---|---|---|
| GET /public/health | None | 200, status ok |
| POST /employees | name, department, startDate ISO date, role default employee | 201, employee item |
| GET /employees | optional hiredFrom/hiredTo dates | 200, employees array |
| GET /employees/{employee_id} | employee ID | 200 item, 404 Employee not found |
| POST /hr-requests/time-off | user_id, start_date, end_date | 202, executionArn |
| POST /hr-requests | user_id, prompt | 202, executionArn |

GET /employees is registered twice; first registration performs range filtering only when both dates are supplied. Models validate types/dates, but not nonblank names or start/end ordering. Framework validation errors use FastAPI detail shape. boto3 failures are not mapped explicitly.

Employee item: PK, SK, GSI1PK, GSI1SK, employeeId, name, department, startDate, role. Query results are unpaginated first pages.

## Defined but unregistered leave routes
- POST /employees/{employee_id}/leave: startDate, endDate, note default empty; returns saved item, 201.
- GET same path: optional month YYYY-MM; returns leave array.
- PUT /employees/{employee_id}/leave/{start_date}: endDate and note; upserts item, 200.
Leave item: PK employee ID, SK start date, employeeId, startDate, endDate, note. No deletion API.

## Agent contract
hrAgent/app/agent/parse.py accepts JSON prompt string or messages array (takes precedence) and optional actorId string default default. Trailing toolUse blocks are removed from supplied history. Runtime session is supplied through X-Amzn-Bedrock-AgentCore-Runtime-Session-Id, not body. main.py yields Strands event dictionaries with event content, filtering empty contentBlockStart. Optional AgentCore memory uses MEMORY_AGENTMEMORY_ID and AWS_REGION. No browser integration exists yet.

## Workflow behavior
TimeOff builds an email; other requests invoke Nova then publish output to SNS. Both increment HR/HrRequests with request type and user ID dimensions. There is no status/results endpoint. CDK outputs expose API URL, pool/client IDs, table name, runtime ARN and workflow ARN.

