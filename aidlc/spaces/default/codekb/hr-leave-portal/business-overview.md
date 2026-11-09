# Business Overview

The repository implements an HR employee and leave portal with an AI assistant. Employees have generated IDs, names, departments, hire dates and roles. Leave records are keyed by employee and starting date. General HR questions and time-off submissions start asynchronous workflows that publish HR email notifications and request metrics.

The AI hrAgent can create/read/update/delete employee records, save/list leave, draft leave emails, and publish messages to HR. It uses the same DynamoDB schema and SNS topic as the API. These capabilities can mutate shared resources; the UI must distinguish chat from the asynchronous request workflow.

A React/Vite starter exists under ui/ but currently displays framework template content. It has no HR functionality, auth configuration or backend calls. Existing infrastructure is the integration target, not a replacement. See api-documentation.md and architecture.md.

