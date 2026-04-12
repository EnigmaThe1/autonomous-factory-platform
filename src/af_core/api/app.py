"""FastAPI application with lifespan management."""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from af_core.api.routes import (
    approvals,
    artifacts,
    events,
    evidence,
    health,
    logs,
    missions,
    orchestration,
    settings,
    uploads,
    work_items,
    workspace,
    ws,
)
from af_core.database import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await init_db()
    yield
    await close_db()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Autonomous Factory",
        description="AI-native autonomous software delivery platform",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(missions.router)
    app.include_router(work_items.router)
    app.include_router(events.router)
    app.include_router(approvals.router)
    app.include_router(orchestration.router)
    app.include_router(uploads.router)
    app.include_router(ws.router)
    app.include_router(settings.router)
    app.include_router(artifacts.router)
    app.include_router(evidence.router)
    app.include_router(logs.router)
    app.include_router(workspace.router)

    # Serve dashboard static files at /dashboard, with root redirect
    dashboard_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "dashboard",
        "static",
    )
    if os.path.isdir(dashboard_dir):
        app.mount("/dashboard", StaticFiles(directory=dashboard_dir, html=True), name="dashboard")

        from fastapi.responses import RedirectResponse

        @app.get("/", include_in_schema=False)
        async def root_redirect():
            return RedirectResponse(url="/dashboard")

    return app


app = create_app()
