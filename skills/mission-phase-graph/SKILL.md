# Mission Phase Graph

## Purpose
Convert a mission contract into a phased execution graph.

## Use when
- the mission is multi-step
- multiple capability families may be needed
- dependencies or checkpoints matter
- execution mode is not obvious

## Procedure
1. Restate the mission in concrete terms.
2. Split work into phases.
3. Identify prerequisites and dependency edges.
4. Mark checkpoints, validation gates, and review gates.
5. Identify candidate escalation points.
6. Produce a minimal phase graph.

## Output
- phase list
- dependency edges
- checkpoints
- escalation candidates
- exit criteria
