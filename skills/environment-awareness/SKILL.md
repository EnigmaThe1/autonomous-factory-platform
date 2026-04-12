# Environment Awareness

## Purpose
Understand the current execution environment so the system can make smarter decisions without restricting normal project autonomy.

## Use when
- the mission may depend on the current runtime context
- you need to know whether container, CI, remote, or local execution changes the best approach
- tool or capability choices depend on environment facts

## Procedure
1. Detect repo/workspace boundaries.
2. Detect OS and shell context.
3. Detect containers, devcontainers, or CI.
4. Detect available runtimes and package managers.
5. Summarize constraints and opportunities.
6. Recommend a practical execution posture.

## Output
- environment summary
- execution zones
- toolchain signals
- constraints
- recommended posture
