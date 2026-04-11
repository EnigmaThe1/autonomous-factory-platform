# Observability and telemetry

## Purpose
This module defines how Autonomous Factory makes its internal reasoning path operationally visible without exposing private chain-of-thought. The goal is not voyeurism. The goal is diagnosability, auditability, performance control, and trust.

## Required observability layers

### 1. Trace events
Every mission must emit structured trace events for:
- mission intake
- compiler findings
- plan generation
- work-item dispatch
- tool invocation start/result
- evidence sufficiency decisions
- recovery routing
- approval decisions
- completion / rollback / block outcomes

Each trace event should carry:
- event id
- mission id
- work item id when relevant
- correlation id / interaction id
- component name
- event name
- severity
- timestamp
- machine-readable payload

### 2. Metrics
The platform should expose metrics for:
- mission start latency
- compiler normalization counts
- time to first useful action
- tool success/failure rates
- optional-tool failures converted to degrade/continue
- retry counts by class
- blocked missions by reason
- completion rates by mission family
- average approval latency
- regression matrix pass rates

### 3. Operator diagnostics
Operators should be able to inspect:
- latest compiler findings
- latest start attempt trace id
- current mission phase
- current blocking reason
- evidence sufficiency status
- last tool failure classification
- last recovery decision

### 4. Audit log
Certain events must always be audit-persisted:
- mission creation
- policy changes
- approvals and rejections
- protected-path access attempts
- connector access
- secret usage events (metadata only, never secret contents)
- self-improvement promotion events

## Telemetry principles
- no secret values in telemetry
- no unbounded raw stdout persistence by default
- redact file content when not necessary
- keep operator-facing diagnostics readable
- preserve enough machine structure for filtering and analytics

## Minimum dashboards
- mission operations dashboard
- runtime health dashboard
- approval and policy dashboard
- regression certification dashboard
- connector and secrets access dashboard
