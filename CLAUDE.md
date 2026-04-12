# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

This project uses the Autonomous Factory Hybrid Pack.

Claude-specific operating rules:
- Use existing skills before inventing new flows.
- Keep autonomy high.
- Avoid unnecessary hard gates.
- Preserve host safety.
- Use capabilities/ state files for learning and adaptive behavior.
- Prefer scoped rollback over broad reset when failures are local.
- Surface important uncertainty clearly.
- Finish with a clean delivery state: done, partial, blocked, assumed.

How to use this repo:
- `agents/` = canonical role library
- `skills/` = reusable skills
- `capabilities/` = adaptive state and learning files
- `templates/` = structured report/output templates
- `bin/` = helper scripts

When starting work:
1. Read this file.
2. Inspect relevant skills and agents.
3. Use helper scripts in `bin/` when useful.
4. Keep outputs operator-usable and explicit about uncertainty.

## What This Repository Is

**Autonomous Factory** — an AI-native autonomous software delivery platform. It compiles raw operator intent into mission contracts, runs them through five specialized agents (Planner, Researcher, Implementer, Reviewer, Validator) supervised by an orchestrator, and enforces evidence-based promotion with bounded autonomy.

## Commands

```bash
# Setup
source .venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest                         # all tests
pytest tests/test_compiler.py  # single file
pytest -k test_name            # single test by name
pytest -v --tb=short           # verbose with short tracebacks

# Lint
ruff check src/ tests/
ruff format src/ tests/

# Run server (development, SQLite)
python -m af_core

# Run server (explicit)
uvicorn af_core.api.app:app --reload --port 8000

# CLI adapter
af health
af create "Title" "Prompt text"
af list
af start <mission_id>
af advance <mission_id>

# Docker (PostgreSQL)
docker compose up -d
```

## Repository Structure

```
blueprint-os/           # Architecture specification (canonical truth)
src/af_core/            # Platform implementation
  models/               # SQLAlchemy ORM models (mission, work_item, evidence, event, approval, report)
  schemas/              # Pydantic API request/response schemas
  services/             # Business logic
    mission_compiler.py # ADR-005: raw prompt -> compiled contract
    orchestrator.py     # ADR-004: mission lifecycle, work-item state machine, approvals
    evidence_engine.py  # ADR-006: evidence sufficiency evaluation
    failure_recovery.py # Failure classification + recovery routing
    tool_gateway.py     # Bounded tool execution with policy enforcement
    event_bus.py        # In-process pub/sub for realtime events
    mission_service.py  # Intake + compilation orchestration
  api/
    app.py              # FastAPI application factory
    routes/             # REST endpoints: missions, work_items, events, approvals, orchestration, ws
  cli.py                # CLI adapter (thin client to backend API)
  config.py             # Settings from environment (AF_ prefix)
  database.py           # Async SQLAlchemy engine + session
dashboard/static/       # Single-page web dashboard (vanilla JS)
tests/                  # pytest async tests
alembic/                # Database migrations
```

## Key Architecture Concepts

**Six-layer architecture:** Operator surfaces -> Control plane -> Execution plane -> Evidence/recoverability plane -> State plane -> Adapter plane

**Five canonical agents:** Planner, Researcher, Implementer, Reviewer, Validator — supervised by a separate Orchestrator/Controller that is *not* an agent itself (ADR-003, ADR-004).

**Mission lifecycle:** Pending -> Compiling -> Compiled -> Queued -> Running -> Completed/Failed/Blocked/Cancelled. The compiler is mandatory (ADR-005) before execution. Work items follow: Pending -> Ready -> Running -> Completed/Failed/Skipped.

**Evidence sufficiency (ADR-006):** Tool failures only block when the tool was REQUIRED and no substitute evidence exists. Optional failures continue. Preferred failures degrade.

**Failure recovery:** Failures are classified (transient, environmental, logical, scope/policy violation) and routed to actions (continue, retry, replan, block, escalate).

## Design Invariants

- Never execute raw missions without compilation (ADR-005)
- Tool failures only block when necessary AND no substitute evidence exists (ADR-006)
- Mission-start must always produce a visible stateful outcome — no silent no-ops (ADR-007)
- All critical state must be JSON-safe, durable, and serializable (ADR-008)
- Prefer recoverability over raw autonomy when trade-offs arise
- Execution must be isolated with explicit kill/recovery semantics (ADR-013)
- All contracts and events must be schema-governed and versioned (ADR-014)
- The orchestrator is separate from the five agents — it supervises, not acts (ADR-004)

## Blueprint Update Protocol

When modifying blueprint documents in `blueprint-os/`:
1. Check if the change affects canonical truth (`00_canonical/`)
2. Update canonical files first if yes
3. Update the implementation ledger
4. Never let lower-level files silently diverge from canonical truth
