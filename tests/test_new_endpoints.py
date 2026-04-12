"""Tests for artifacts, evidence, reports, logs, and diagnostics endpoints."""

import pytest


@pytest.mark.asyncio
async def test_diagnostics_endpoint(client):
    resp = await client.get("/api/diagnostics")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "missions" in data
    assert "work_items" in data
    assert "pending_approvals" in data
    assert "total_events" in data
    assert "recent_events" in data


@pytest.mark.asyncio
async def test_health_with_db(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"


@pytest.mark.asyncio
async def test_favicon(client):
    resp = await client.get("/favicon.ico")
    assert resp.status_code == 200
    assert "svg" in resp.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_artifacts_empty(client):
    # Create a mission first
    resp = await client.post(
        "/api/missions?compile=false",
        json={
            "title": "Art test",
            "raw_prompt": "test",
        },
    )
    mid = resp.json()["id"]
    resp = await client.get(f"/api/missions/{mid}/artifacts")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_artifacts_after_upload(client):
    resp = await client.post(
        "/api/missions?compile=false",
        json={
            "title": "Upload art",
            "raw_prompt": "test",
        },
    )
    mid = resp.json()["id"]

    # Upload a file with mission_id
    await client.post(
        "/api/uploads/file",
        files={"file": ("test.txt", b"hello", "text/plain")},
        data={"dest": "", "mission_id": mid},
    )

    resp = await client.get(f"/api/missions/{mid}/artifacts")
    assert resp.status_code == 200
    arts = resp.json()
    assert len(arts) == 1
    assert arts[0]["name"] == "test.txt"


@pytest.mark.asyncio
async def test_evidence_empty(client):
    resp = await client.post(
        "/api/missions?compile=false",
        json={
            "title": "Ev test",
            "raw_prompt": "test",
        },
    )
    mid = resp.json()["id"]
    resp = await client.get(f"/api/missions/{mid}/evidence")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_tool_invocations_empty(client):
    resp = await client.post(
        "/api/missions?compile=false",
        json={
            "title": "TI test",
            "raw_prompt": "test",
        },
    )
    mid = resp.json()["id"]
    resp = await client.get(f"/api/missions/{mid}/tool-invocations")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_reports_empty(client):
    resp = await client.post(
        "/api/missions?compile=false",
        json={
            "title": "Rpt test",
            "raw_prompt": "test",
        },
    )
    mid = resp.json()["id"]
    resp = await client.get(f"/api/missions/{mid}/reports")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_logs_export(client):
    resp = await client.get("/api/logs/events")
    assert resp.status_code == 200
    assert "ndjson" in resp.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_logs_missions_export(client):
    resp = await client.get("/api/logs/missions")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
