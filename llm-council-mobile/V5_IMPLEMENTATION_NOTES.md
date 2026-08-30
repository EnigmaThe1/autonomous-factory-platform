# LLM Council Mobile v5 implementation invariants

1. API success is not model success. Empty, nil, malformed or instruction-noncompliant responses are not council-usable.
2. Exhaustive repository audit coverage is enforced by software. A model cannot enter peer review unless every required repository file/part assigned to it was processed successfully.
3. GitHub recursive-tree truncation or failure to fetch a required file aborts an exhaustive audit rather than silently reducing scope.
4. Generated/vendor/binary/oversized exclusions are explicit and outside the coverage denominator.
5. Repository secrets are redacted heuristically before source text is sent to model providers.
6. Model agreement is not proof; repository audits include an adversarial verification pass before chairman synthesis.
7. Export uses Android Storage Access Framework and user-selected folders; no broad storage permission is requested.
8. GitHub credentials are encrypted using the existing Android Keystore-backed settings key.
9. Long repository audits run in a foreground service with visible progress/cancel notification.
10. Repository audit outputs preserve commit SHA, coverage, model identity, peer reviews, rankings and final report for reproducibility.
