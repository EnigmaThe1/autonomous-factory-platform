# Generic Activation Policy

Use lifecycle states to control optional capabilities:
- discovered: known but not yet reviewed
- reviewed: inspected for relevance and basic safety
- approved: explicitly allowed for future use
- mirrored: available through a local mirror or local metadata snapshot
- activated: enabled for the current mission
- retired: no longer used

Prefer the smallest justified next state. Do not jump from discovered to activated without review and approval unless a local policy explicitly allows it.
