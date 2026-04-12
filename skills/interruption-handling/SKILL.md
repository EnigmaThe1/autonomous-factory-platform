# Interruption Handling

## Purpose
Improve how the system responds to pauses, redirects, and partial invalidation.

## Use when
- missions are interrupted mid-flow
- human steering changes the path
- some earlier work is invalidated but not everything

## Procedure
1. Review the interruption type.
2. Assess what work remains valid.
3. Decide whether to continue, adapt, fork, pause, or restart.
4. Preserve as much useful coherence as possible.

## Output
- interruption finding
- recommended response
- salvage note
- confidence
- rollback condition
