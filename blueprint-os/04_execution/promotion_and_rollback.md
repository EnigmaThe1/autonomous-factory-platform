# Promotion and Rollback

## Promotion rules
- no release without visible mission/action outcomes
- no promotion without passing core validation suites
- no promotion without matrix smoke coverage

## Rollback rules
- platform releases must be reversible
- schema migrations must be staged and recoverable
- adapter failures must not corrupt backend mission truth

## Runtime rollback principle
Mission-level rollback is explicit and evidence-backed, not implicit undo magic.
