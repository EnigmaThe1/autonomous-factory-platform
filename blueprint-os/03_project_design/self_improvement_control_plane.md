# Self-improvement control plane

## Position in architecture
Self-improvement is not a hidden side process. It is a specialized mission family handled by the same control plane with stricter policy and validation.

## Required gates
- proposal gate
- risk classification gate
- isolated implementation gate
- review gate
- validator gate
- promotion gate
- rollback-ready gate

## Ledger requirement
Every self-improvement attempt must update a dedicated improvement ledger with:
- hypothesis
- change set
- validation results
- promotion outcome
- rollback reference
