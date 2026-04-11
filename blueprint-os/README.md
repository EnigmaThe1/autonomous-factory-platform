# Blueprint OS — Autonomous Factory

This package contains the filled Blueprint OS for **Autonomous Factory**, re-scoped as a **standalone AI-native platform** instead of a heavy editor-dependent extension.

## What this package is for

This blueprint turns the current extension-era learning into a durable product plan for a platform that:
- compiles raw operator intent into execution-grade mission contracts
- runs multi-agent software-delivery missions with bounded autonomy
- enforces evidence-first execution, recoverability, and safety
- exposes a standalone dashboard and API
- supports optional thin adapters for Cursor, VS Code, CLI, and future clients

## Canonical truth

Treat these files as the top-level truth:
- `00_canonical/blueprint.md`
- `00_canonical/implementation_ledger.md`
- `00_canonical/architecture_decisions.md`

## How to read this package

1. Start with the canonical files in `00_canonical/`.
2. Read the operating doctrine in `02_foundation/`.
3. Read the concrete project design in `03_project_design/`.
4. Use `04_execution/` as the staged build plan.
5. Use `07_meta/` to keep the blueprint live and controlled over time.

## Key decision already reflected here

The main product is now a **standalone Autonomous Factory platform**.
Editor integrations remain valuable, but only as **thin adapters** rather than the primary runtime shell.

## v2 status
This package now includes a gap-audit enhancement pass covering observability, auth/RBAC, execution isolation, data contracts, secrets/connectors, and self-improvement governance.
