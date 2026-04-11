# Architecture Decisions

## ADR-001 — Standalone platform is the primary product shell
- Status: Accepted
- Decision: Autonomous Factory will be built as a standalone platform, not as an editor-extension-first product.
- Reason: extension-host, webview, service-worker, and shared-runtime fragility create unnecessary platform risk.

## ADR-002 — Keep editor integrations as thin adapters
- Status: Accepted
- Decision: Cursor/VS Code/CLI integrations remain valuable, but only as thin adapters to the standalone backend.
- Reason: editor integration is still useful for workspace context and convenience, but should not own core runtime state.

## ADR-003 — Canonical five-agent model remains
- Status: Accepted
- Decision: Planner, Researcher, Implementer, Reviewer, and Validator remain the canonical mission agents.
- Reason: role specialization improves quality, clarity, and downstream governance.

## ADR-004 — Orchestrator remains separate from agent set
- Status: Accepted
- Decision: Orchestration, mission control, and policy supervision remain outside the five-agent set.
- Reason: the controller should supervise and arbitrate, not act as just another worker role.

## ADR-005 — Mission Compiler is mandatory before execution
- Status: Accepted
- Decision: raw missions must be compiled into authoritative contracts before planning/execution.
- Reason: prompt literalism, bad paths, and input/output confusion are too costly.

## ADR-006 — Evidence sufficiency decides whether failures matter
- Status: Accepted
- Decision: tool failures only block when the failed tool was necessary and sufficient substitute evidence does not exist.
- Reason: prevents brittle overreaction to optional or environmental probe failures.

## ADR-007 — Persistence-first mission registration
- Status: Accepted
- Decision: mission-start attempts must always produce a visible stateful outcome.
- Reason: silent no-op behavior is unacceptable in an autonomous control platform.

## ADR-008 — Platform truth must be durable and serializable
- Status: Accepted
- Decision: critical state, contracts, findings, and outcomes must be JSON-safe, durable, and recoverable.
- Reason: UI refreshes and runtime restarts must not erase mission truth.

## ADR-009 — Local-first deployment with scale-out path
- Status: Accepted
- Decision: the initial platform should run well on a single local machine, with later support for multi-service or remote deployment.
- Reason: matches current operator workflow while preserving future scalability.

## ADR-010 — Controlled self-improvement is future, not implicit
- Status: Accepted
- Decision: self-improvement is deferred until the platform can route it through bounded missions, validation, rollback, and an improvement ledger.
- Reason: uncontrolled self-modification is not acceptable.


## v2 addendum decisions

### AD-011 — Observability is a first-class subsystem
The platform must emit structured traces, metrics, logs, and operator-facing diagnostics as a core capability, not an afterthought.

### AD-012 — Auth and RBAC are mandatory platform primitives
The standalone platform must not assume a single trusted local operator forever. User identity, role binding, workspace authority, and approval authority are canonical concerns.

### AD-013 — Execution must be isolated by design
Mission execution, tool invocation, and workspace mutation must run inside bounded isolation domains with explicit kill/recovery semantics.

### AD-014 — Contract schemas are canonical truth
Mission contracts, evidence contracts, event envelopes, approval objects, and reports must be schema-governed and versioned.

### AD-015 — Self-improvement is governed, not free-form
The platform may propose and execute self-improvement only through bounded missions, validation, promotion gates, and rollback controls.
