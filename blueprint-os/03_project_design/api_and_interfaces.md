# API and Interfaces

## External interfaces

### Web dashboard
Primary operator UI for mission control, approvals, reports, and diagnostics.

### REST/HTTP API
- create mission
- get mission
- list missions
- approve/reject actions
- fetch reports/artifacts
- diagnostics and health

### Realtime channel
WebSocket or SSE for:
- mission events
- agent activity
- timeline updates
- compiler findings
- report readiness

### Adapter APIs
Thin client/adapters should use stable backend interfaces rather than internal platform modules.

## Internal interfaces
- mission compiler interface
- orchestrator interface
- evidence engine interface
- tool gateway interface
- persistence interface
- adapter interface
