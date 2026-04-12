"""Mission API tests."""

import pytest


@pytest.mark.asyncio
async def test_create_mission(client):
    resp = await client.post(
        "/api/missions",
        json={
            "title": "Test mission",
            "raw_prompt": "Build a hello world app",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Test mission"
    assert data["status"] in ("pending", "compiled")
    assert data["id"]


@pytest.mark.asyncio
async def test_list_missions(client):
    await client.post(
        "/api/missions",
        json={
            "title": "Mission A",
            "raw_prompt": "Do A",
        },
    )
    await client.post(
        "/api/missions",
        json={
            "title": "Mission B",
            "raw_prompt": "Do B",
        },
    )
    resp = await client.get("/api/missions")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["missions"]) == 2


@pytest.mark.asyncio
async def test_get_mission(client):
    create_resp = await client.post(
        "/api/missions",
        json={
            "title": "Fetch me",
            "raw_prompt": "Details here",
        },
    )
    mission_id = create_resp.json()["id"]

    resp = await client.get(f"/api/missions/{mission_id}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Fetch me"


@pytest.mark.asyncio
async def test_get_mission_not_found(client):
    resp = await client.get("/api/missions/nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_cancel_mission(client):
    create_resp = await client.post(
        "/api/missions",
        json={
            "title": "Cancel me",
            "raw_prompt": "Will be cancelled",
        },
    )
    mission_id = create_resp.json()["id"]

    resp = await client.post(f"/api/missions/{mission_id}/cancel")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_cancel_already_cancelled(client):
    create_resp = await client.post(
        "/api/missions",
        json={
            "title": "Cancel twice",
            "raw_prompt": "Double cancel",
        },
    )
    mission_id = create_resp.json()["id"]
    await client.post(f"/api/missions/{mission_id}/cancel")

    resp = await client.post(f"/api/missions/{mission_id}/cancel")
    assert resp.status_code == 409
