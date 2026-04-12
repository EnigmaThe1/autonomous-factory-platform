# AGENTS.md

This project uses the Autonomous Factory Hybrid Pack.

Codex-specific operating rules:
- Use existing skills before inventing new workflows.
- Keep autonomy high.
- Avoid unnecessary hard gates.
- Preserve host safety.
- Use `capabilities/` state files when updating learned behavior.
- Prefer scoped rollback over broad reset when failures are local.
- Separate what is proven, inferred, assumed, partially proven, or unknown.
- Finish with a clean delivery state: done, partial, blocked, assumed.

## Pack map
- `agents/` = canonical role library
- `skills/` = reusable task skills
- `capabilities/` = adaptive state and policy files
- `templates/` = structured outputs
- `bin/` = helper scripts

## Expected behavior
- Be adaptive, not rigid.
- Do not expand scope without reason.
- Keep deliverables operator-usable.
- Surface important uncertainty clearly.
- Use proportionate effort; stop when marginal gains are low unless risk still warrants depth.
