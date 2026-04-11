# Auth and access model

## Authentication
Near-term MVP can support local trusted mode plus local accounts. The architecture must still be designed so external auth providers can be added without reworking mission ownership or approvals.

## Authorization axes
Access decisions are made across:
- user role
- workspace membership
- action type
- target resource
- environment tier
- approval requirement

## Ownership
Each mission belongs to:
- one workspace
- one requesting actor
- one policy snapshot

Approvals are evaluated against the actor and the workspace policy, not just a global default.
