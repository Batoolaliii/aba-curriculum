# Technology Stack

Declared versions/ranges from local manifests; dependency freshness was not assessed against registries.

| Area | Declared technology |
|---|---|
| Root Python | >=3.14, uv_build >=0.13.5,<0.14.0 |
| Root infrastructure | aws-cdk-lib >=2.273.0,<3.0.0; constructs >=10.5.0,<11.0.0 |
| API/dev | FastAPI >=0.162.0; Mangum >=0.22.0; uvicorn >=0.54.0; boto3 >=1.43.121; pytest 8.4.2 |
| Root runtime SDK | botocore[crt] >=1.43.121 |
| UI | React/React DOM ^19.3.1; aws-amplify ^6.22.2; @aws-amplify/ui-react ^6.15.7 |
| UI tooling | Vite ^8.3.6; TypeScript ~6.0.3; ESLint ^10.14.0; plugin-react ^6.1.2; typescript-eslint ^8.72.1 |
| Agent Python | >=3.10; hatchling ~=1.27.0; Python 3.12 container |
| Agent SDK | bedrock-agentcore[strands-agents] >=1.18.1,<2.0.0; strands-agents >=1.62.0,<2.0.0; botocore[crt] ~=1.43.0; aws-opentelemetry-distro ~=0.21.0 |
| Alternate CDK | @aws/agentcore-cdk 1.0.0; aws-cdk-lib ~2.269.0; constructs ~10.7.0; TypeScript ~5.9.3; aws-cdk ~2.1126.0 |

Managed resources: API Gateway REST API, Lambda Python 3.14, DynamoDB, Cognito, SNS, Step Functions, Bedrock, AgentCore, ECR, SSM, CloudWatch. No UI hosting stack exists.

