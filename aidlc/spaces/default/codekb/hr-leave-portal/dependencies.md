# Dependencies

## Internal graph
- app.py imports all four stack classes.
- StateMachineStack receives NotificationStack topic and BackendStack Lambda; injects HR_STATE_MACHINE_ARN and StartExecution permission.
- AgentRuntimeStack receives backend table, pool/client and notification topic.
- api/handler.py imports controllers; registered employee/HR controllers import models and matching services.
- Employee and leave services import boto3 DynamoDB and require TABLE_NAME at import.
- HR service imports boto3 Step Functions and requires HR_STATE_MACHINE_ARN at import.
- Agent main imports parse, model.load, memory.session and tool modules; tool modules require TABLE_NAME and HR_EMAIL_TOPIC_ARN at import.
- UI main imports App and index.css; App imports starter assets and App.css. No backend client/config module.
- Alternate AgentCore CDK bin reads project settings and transforms them for its stack.

## External/build boundaries
Root CDK resolves FastAPI layer and agent image through SSM parameters populated by scripts. Agent Docker build uses its uv.lock. UI has its own npm lockfile. Root package-lock.json has no package dependencies. Root Python build packages src/hr_leave_portal/ while CDK imports the separate root hr_leave_portal/ package.

No circular Python imports identified. Stack references deserve care: injecting the workflow ARN into an existing backend Lambda can produce cross-stack dependency relationships that should be checked during synthesis. No AWS commands or build scripts were executed.

