# Safety and Guardrails Module

## Purpose
Describe the non-negotiable safety boundaries for Autonomous Factory.

## Guardrail categories

### Scope guardrails
- missions must operate only within approved workspace/repo scope
- protected paths require explicit policy/approval behavior
- outside-workspace mutation is denied by default

### Execution guardrails
- no destructive git operations by default
- no dependency changes unless explicitly within scope
- no secret extraction or unsafe config dumping
- no silent widening of mission scope

### Autonomy guardrails
- autonomy is bounded by evidence, recoverability, and policy
- optional tool failure must not block by default
- required evidence failure must not be downgraded incorrectly

### Recoverability guardrails
- every meaningful state transition should be durable and inspectable
- rollback pathways must remain available where applicable
- no invisible start failures, no dead-button actions, no silent no-ops

### Promotion guardrails
- review and validation requirements must be honored before promotion
- operator-facing status must reflect true state

## Protected recovery spine
The following must remain robust even under failure:
- mission persistence
- mission compiler findings
- approvals
- visible blocked/error outcomes
- event/timeline truth
- rollback/promotion controls
