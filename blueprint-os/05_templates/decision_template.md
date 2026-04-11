# Decision Template — Example

## Decision title
Standalone platform is the primary product shell.

## Context
The editor-extension-first runtime introduced fragility in webviews, shared hosts, and action bridges.

## Decision
Move the main product to a standalone backend + dashboard architecture. Keep editor integrations as thin adapters.

## Consequences
Positive:
- stronger runtime control
- better observability
- easier scaling and testing

Trade-offs:
- additional platform engineering work
- need for adapter protocol design
