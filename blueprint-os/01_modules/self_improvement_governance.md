# Self-improvement governance

## Purpose
This module defines how AF can improve itself safely.

## Core rule
AF may not freely rewrite itself. It may only self-improve through bounded missions governed by the same architecture as ordinary operator missions, with stricter approval and validation gates.

## Canonical flow
1. detect recurring weakness or opportunity
2. create self-improvement proposal
3. compile proposal into bounded mission
4. execute in isolated branch/sandbox
5. review and validate
6. promote only after approval
7. keep rollback artifact and evidence

## Forbidden behaviors
- direct uncontrolled self-rewrite on live baseline
- bypassing validation because the change is "obvious"
- connector or permission expansion without explicit approval
- self-promotion after failed validation
