# Component Inventory

## React UI
ui/src/: unconnected template; depends on React/React DOM, Vite and CSS. Amplify libraries are installed but unused.

## Backend API
api/: FastAPI/Mangum entry, Pydantic models, controllers and boto3 services. Depends on DynamoDB and Step Functions environment references.

## Backend Infrastructure
hr_leave_portal/backend_stack.py: DynamoDB table/GSI, API Lambda and layer, Cognito pool/client, Cognito authorizer, API Gateway, outputs.

## HR Workflow
state_machine_stack.py and state_machines/: JSONata workflow, execution permissions and API environment wiring; uses Bedrock, SNS and CloudWatch.

## Notifications
notification_stack.py: SNS topic and email subscription with source-configured recipient.

## HR Agent
hrAgent/app/agent/: Strands streamed invocation, Nova model, optional memory, employee/leave/email tools.

## Agent Infrastructure
agent_runtime_stack.py: Cognito-authorized hrAgent runtime, existing table/topic references, ECR/model permissions, SSM image reference. hrAgent/agentcore/cdk/ separately wraps generated AgentCoreApplication.

## Build and Tests
scripts/ publishes layer and container to AWS; tests/unit/ contains obsolete scaffold assertions. Root and package manifests describe build commands.

