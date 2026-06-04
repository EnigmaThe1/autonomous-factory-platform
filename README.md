# Autonomous Factory Platform

Autonomous Factory Platform is an experimental AI-native software-delivery control plane. It is designed to convert operator intent into structured mission workflows, coordinate specialised agent roles, track evidence, and expose mission state through an API and lightweight dashboard.

This repository is intended as a portfolio-quality backend/control-plane project showing work with agentic workflow design, FastAPI, async Python services, persistent state, evidence tracking, and Docker-based local deployment.

## What the project demonstrates

- **Agentic workflow orchestration** — mission intake, work items, approvals, events and orchestration endpoints.
- **Mission compilation concept** — raw operator requests are treated as input that should be compiled into structured mission contracts before execution.
- **Evidence-aware execution** — mission progress can be linked to logs, artifacts, evidence records and operator-visible status.
- **Backend API design** — FastAPI routes for missions, work items, events, approvals, evidence, logs, settings, workspace access and WebSocket updates.
- **Persistent state** — SQLAlchemy/Alembic database layer with SQLite for local development and PostgreSQL support through Docker Compose.
- **Operator dashboard** — lightweight static dashboard served by the backend for local inspection of mission state.
- **Developer tooling** — pytest, Ruff, editable installs, CLI entry point and containerized startup.

## Architecture overview

The platform is structured around a control-plane model:

```text
Operator request
  -> mission intake / compiler
  -> orchestration service
  -> work items and approvals
  -> evidence, logs and artifacts
  -> API, dashboard and WebSocket updates
  -> database persistence
```

Key areas of the repository:

```text
src/af_core/
  api/          FastAPI application and route modules
  services/     mission, orchestration, evidence and recovery services
  models/       SQLAlchemy ORM models
  schemas/      Pydantic request/response schemas
  cli.py        command-line entry point
  config.py     environment-driven settings

dashboard/static/  lightweight operator dashboard
alembic/           database migrations
tests/             pytest test suite
```

## Technology stack

- Python 3.12+
- FastAPI and Uvicorn
- Pydantic / Pydantic Settings
- SQLAlchemy async ORM
- Alembic migrations
- SQLite for local development
- PostgreSQL via Docker Compose
- WebSockets
- pytest and pytest-asyncio
- Ruff
- Docker / Docker Compose

## Local development

Create and activate a virtual environment, then install the package in editable mode with development dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run the API locally:

```bash
uvicorn af_core.api.app:app --reload --port 8000
```

The dashboard is served at:

```text
http://localhost:8000/dashboard
```

Run tests:

```bash
pytest
```

Run linting/format checks:

```bash
ruff check src/ tests/
ruff format src/ tests/
```

## Docker startup

For a local PostgreSQL-backed environment:

```bash
docker compose up -d
```

This starts:

- PostgreSQL 16 Alpine
- Autonomous Factory API on port `8000`
- Workspace volume mounted into the API container

## CLI usage

The package exposes an `af` command-line entry point:

```bash
af health
af create "Mission title" "Mission prompt text"
af list
af start <mission_id>
af advance <mission_id>
```

## Current status

This is a pre-release / experimental portfolio project. It is useful for demonstrating architecture, API design, agentic workflow modelling, evidence-based execution concepts and Dockerized backend development. It should not be treated as a production autonomous coding system without further security hardening, integration testing and operational review.

## Portfolio relevance

This project is relevant for roles involving:

- AI workflow automation
- Agentic AI systems
- LLM application architecture
- AI product prototyping
- Backend API development
- Technical operations platforms
- Developer tooling and automation

## License

No open-source license is currently provided. Unless a license is added, all rights are reserved by the repository owner.
