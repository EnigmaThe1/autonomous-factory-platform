# Connectors and secrets model

## Storage
Secrets should live in a dedicated secret store abstraction. Mission state stores only references and usage metadata.

## Connector invocation flow
1. mission contract requests capability
2. policy binder decides if connector is allowed
3. connector token/secret is resolved at runtime
4. invocation is executed with bounded scope
5. metadata audit entry is recorded

## Minimum governance fields
- connector id
- workspace scope
- role scope
- approval class
- mutating vs read-only
- last rotated
- last used
