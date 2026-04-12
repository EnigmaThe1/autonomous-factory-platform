# Meta-Learning

## Purpose
Refine the system's own decision heuristics using accumulated mission evidence.

## Use when
- several missions have been completed
- learned patterns already exist
- the system should improve its weighting logic, not only remember outcomes

## Procedure
1. Review cross-mission learning outputs.
2. Review evidence weights, phase-promotion behavior, and live-feedback trends.
3. Detect which heuristics are systematically too aggressive or too conservative.
4. Propose soft tuning changes.

## Output
- heuristic adjustment
- supporting evidence
- confidence
- rollback condition
