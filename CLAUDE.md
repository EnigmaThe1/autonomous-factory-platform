# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repository Is

This is the **Blueprint OS** for **Autonomous Factory** — an AI-native autonomous software delivery platform. The repository currently contains only the architecture and design specification (no runnable code yet). The platform is in a pre-implementation "transition-in-progress" state, migrating from a prior editor-extension codebase to a standalone platform.

## Repository Structure

All content lives under `blueprint-os/` organized into numbered sections:

- `00_canonical/` — **Canonical truth.** `blueprint.md`, `implementation_ledger.md`, and `architecture_decisions.md` are the highest-authority documents. Start here.
- `01_modules/` — Module-level specs (orchestration, agents, tools, safety, storage, testing, auth, observability, etc.)
- `02_foundation/` — Operating doctrine: bounded autonomy rule, recoverability-first rule, AI-native design principles
- `03_project_design/` — Concrete design: architecture, agent roles, workflows, state model, data flow, API/interfaces, deployment model
- `04_execution/` — Build plan: implementation stages, build order, milestone plan, validation plan, MVP acceptance metrics
- `05_templates/` — Templates for new blueprint documents, modules, decisions, and validation entries
- `06_archive/` — Superseded versions and retired decisions
- `07_meta/` — Blueprint maintenance rules, update protocol, versioning policy

## Key Architecture Concepts

**Six-layer architecture:** Operator surfaces → Control plane → Execution plane → Evidence/recoverability plane → State plane → Adapter plane

**Five canonical agents:** Planner, Researcher, Implementer, Reviewer, Validator — supervised by a separate Orchestrator/Controller that is *not* an agent itself (ADR-003, ADR-004).

**Mission lifecycle:** Raw operator intent → Mission Compiler (mandatory, ADR-005) → Compiled mission contract → Orchestrator routes to agents → Evidence engine evaluates sufficiency → Promotion/rollback decision.

**Deployment model:** Local-first (Docker or native single-node) with optional scale-out (ADR-009). Editor integrations are thin adapters only (ADR-001, ADR-002).

## Design Invariants

These are non-negotiable and must be respected in any implementation work:

- Never execute raw missions without compilation (ADR-005)
- Tool failures only block when the tool was necessary AND no substitute evidence exists (ADR-006)
- Mission-start must always produce a visible stateful outcome — no silent no-ops (ADR-007)
- All critical state must be JSON-safe, durable, and serializable (ADR-008)
- Self-improvement is deferred and must go through bounded missions with validation and rollback (ADR-010, ADR-015)
- Prefer recoverability over raw autonomy when trade-offs arise
- Execution must be isolated with explicit kill/recovery semantics (ADR-013)
- All contracts and events must be schema-governed and versioned (ADR-014)

## Blueprint Update Protocol

When modifying blueprint documents:
1. Check if the change affects canonical truth (`00_canonical/`)
2. Update canonical files first if yes
3. Update the implementation ledger
4. Update impacted module/design/execution files
5. Record direction changes in `06_archive/`
6. Never let lower-level files silently diverge from canonical truth

## Build Order (When Implementation Begins)

1. Platform-core packages and shared types
2. Persistence layer and mission store
3. Mission start + compiler + visible outcomes
4. Controller + work-item lifecycle
5. Evidence/failure/recovery engine
6. Tool gateway and bounded workspace runner
7. Dashboard (mission list, inspector, approvals)
8. Adapter bridges (Cursor, VS Code, CLI)
9. Regression mission matrix certification
