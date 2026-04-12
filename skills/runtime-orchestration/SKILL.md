# Runtime Orchestration

## Purpose
Manage mission progression through a phased execution graph.

## Procedure
1. Load the current mission graph and runtime state.
2. Identify the next runnable phase.
3. Check whether required capabilities are activated.
4. Check whether approvals or reviews are required.
5. Advance only the minimum justified phase.
6. Update runtime state honestly.

## Output
- current phase
- next runnable action
- blockers
- required capabilities
- state update
