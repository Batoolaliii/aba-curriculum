# Requirements Analysis Questions

The existing UI is a React/Vite starter. Cognito protects the API and hrAgent. No AWS deployment will be performed.

## Q1. [Product owner] Initial UI workflows

Which workflows should the first UI include? Existing employee APIs support listing, filtering and creation; leave routes exist but need registration. HR requests return an execution ID without a status endpoint.

A. Employee directory and creation, employee leave list/create/update, time-off and general HR requests, and hrAgent chat; register existing leave routes with targeted regression tests.
B. Employee directory and creation, time-off and general HR requests, and hrAgent chat; leave backend routes unchanged.
C. hrAgent chat only, with Cognito sign-in.
X. Other (please specify)

[Answer]: A. Employee directory and creation, employee leave list/create/update, time-off and general HR requests, and hrAgent chat; register existing leave routes with targeted regression tests.

## Q2. [Product owner] Employee identity and access

The existing API authenticates callers but has no per-employee or role authorization, and employee IDs are independent of Cognito accounts. Who is this first UI for?

A. Trusted HR staff: signed-in users select an employee for leave and HR requests; retain the existing authorization model and document it.
B. Employee self-service: map Cognito users to employee records and enforce ownership in backend and agent tools before exposing employee data or actions.
X. Other (please specify)

[Answer]: A. Trusted HR staff: signed-in users select an employee for leave and HR requests; retain the existing authorization model and document it.
