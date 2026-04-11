# Implementation Ledger — Autonomous Factory

## Purpose

This ledger records implementation truth for the standalone Autonomous Factory platform. It tracks what is conceptually complete, partially reusable, deferred, or not yet built.

## Status legend
- **DONE** — concept or module exists and is considered reusable/stable enough to carry forward
- **PARTIAL** — meaningful work exists but requires extraction/refactor
- **PLANNED** — designed but not implemented in the standalone platform yet
- **DEFERRED** — intentionally postponed
- **RETIRED** — no longer part of the intended architecture

## Ledger entries

### L-001 — Canonical five-agent model
- Status: DONE
- Truth: Planner, Researcher, Implementer, Reviewer, Validator remain the canonical mission agents.
- Notes: Orchestrator/controller remains separate.

### L-002 — Mission orchestration concepts
- Status: PARTIAL
- Truth: Mission queueing, work-item lifecycle, recovery routing, and completion-collapse logic have been developed in the extension codebase.
- Migration need: extract into standalone platform core without editor-coupled UI paths.

### L-003 — Mission Compiler preflight
- Status: PARTIAL
- Truth: A real pre-execution mission compiler layer now exists conceptually and in extension implementation form.
- Migration need: make it platform-native, schema-driven, and API-visible.

### L-004 — Tool necessity / evidence sufficiency
- Status: PARTIAL
- Truth: The system now reasons about optional/preferred/required evidence more explicitly.
- Migration need: make evidence contracts first-class, not mostly heuristic.

### L-005 — Failure classification and recovery routing
- Status: PARTIAL
- Truth: Structured failure classes and recovery routes exist in extension form.
- Migration need: decouple from editor/webview assumptions and expose in dashboard/API.

### L-006 — Regression mission matrix
- Status: DONE
- Truth: A reusable mission matrix and operator docs exist and should be carried into the standalone platform testing strategy.

### L-007 — Editor-heavy runtime shell
- Status: RETIRED as primary architecture
- Truth: The extension/webview host is no longer the intended main product shell.
- Replacement: standalone dashboard + API + thin adapters.

### L-008 — Standalone platform architecture
- Status: PLANNED
- Truth: This blueprint package defines the target architecture and build sequence.

### L-009 — Controlled self-improvement subsystem
- Status: DEFERRED
- Truth: Desired later capability; must route through bounded missions, validation, rollback, and improvement ledger.

### L-010 — Mission compiler/operator prompt sanity-checking
- Status: PLANNED/PARTIAL
- Truth: The system should verify paths, repo truth, and assumptions before execution rather than following prompts literally.
- Next action: make the compiler schema-first and operator-visible.

## Immediate next implementation slices

1. establish platform-core package boundaries
2. define durable data model and persistence layer
3. create API and dashboard skeleton
4. migrate mission start / compiler / orchestrator logic out of extension shell
5. define workspace execution adapter boundary

## Change discipline

Update this ledger whenever:
- a module becomes reusable or retired
- the canonical architecture changes
- a deferred capability becomes active work
- a major migration milestone is completed


## v2 gap audit and enhancement pass

Status: complete

Added deeper specification for:
- observability and telemetry
- authentication, RBAC, and audit trails
- execution isolation and resource controls
- data contracts and schema governance
- secrets and connectors governance
- self-improvement governance

The package is now stronger as a build-directed blueprint and less reliant on implicit operator interpretation.
