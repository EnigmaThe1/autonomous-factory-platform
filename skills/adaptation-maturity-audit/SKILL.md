# Adaptation Maturity Audit

## Purpose
Check whether a learned adaptation has enough evidence to strengthen, or should remain tentative.

## Procedure
1. Review evidence breadth, recency, and consistency.
2. Detect overreaction to weak or narrow evidence.
3. Recommend one of:
   - keep_tentative
   - strengthen_soft_default
   - dampen
   - rollback

## Output
- maturity finding
- recommended action
- evidence rationale
