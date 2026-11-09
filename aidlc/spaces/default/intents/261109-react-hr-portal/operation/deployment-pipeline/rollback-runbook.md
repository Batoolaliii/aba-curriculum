# Rollback Runbook — Preparation Only

## Authorization and Prerequisites

No rollback or deployment has run. Before a future release, a release owner must retain the previous complete UI artifact, generated configuration and synthesized templates, record account/region and distribution ID, and validate the recovery steps in staging. This runbook has been reviewed against source, not rehearsed against AWS.

## Triggers

Sign-in/session failures, incorrect API/runtime configuration, broken core workflows, elevated distribution/origin errors, or suspected sensitive-data exposure. Notify the designated release owner; if security-related, restrict access first under a separately authorized response. No personal escalation contacts were provided; assign them before a release.

## Recovery Procedure

1. Stop further promotion. Record the failed release identity, errors, time and affected operations without passwords, tokens or HR payloads.
2. With explicit AWS mutation authorization, redeploy the previous compatible UI artifact and matching public config using the same stack and distribution identity; invalidate changed static/config paths. Use a clean checkout of the known good candidate rather than overwriting this working tree.
3. For a first UI deployment with no previous working UI, withdraw access to the new distribution under operator approval; retain backend data. Do not destroy the application or existing stacks as a rollback shortcut.
4. Leave the additive leave-router registration in place if it is healthy. If an API rollback is required, select the prior Lambda asset/template while preserving table, user pool and workflow identities. Do not remove the leave API while a UI that depends on it remains accessible.
5. Validate HTTPS, config and sign-in; then read-only directory/leave and a safe agent prompt. Only rerun mutating HR actions with permission: agent cancellation and UI rollback do not reverse tool calls, accepted workflows, saved records or sent notifications.
6. Record recovery evidence and arrange defect remediation before another release.

## Data and Security

No schema migration is introduced, so no database restore is part of normal UI rollback. The UI bucket is retained. Do not delete Cognito/DynamoDB/SNS/AgentCore resources. A resource replacement or unexpected IAM expansion in a rollback change set is an abort condition. Never include tokens or personal HR data in recovery logs.
