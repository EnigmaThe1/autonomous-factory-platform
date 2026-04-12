"""Orchestrator / mission lifecycle tests."""

import pytest


async def _create_and_start(client) -> str:
    """Helper: create, compile, start a mission. Returns mission_id."""
    resp = await client.post(
        "/api/missions",
        json={
            "title": "Build feature X",
            "raw_prompt": "Implement feature X in ./src/feature_x with tests and review",
        },
    )
    mission_id = resp.json()["id"]
    assert resp.json()["status"] == "compiled"

    start_resp = await client.post(f"/api/missions/{mission_id}/start")
    assert start_resp.status_code == 200
    return mission_id


@pytest.mark.asyncio
async def test_start_mission_seeds_work_items(client):
    mission_id = await _create_and_start(client)

    # Check work items were created
    wi_resp = await client.get(f"/api/missions/{mission_id}/work-items")
    assert wi_resp.status_code == 200
    items = wi_resp.json()
    assert len(items) == 5  # Plan, Research, Implement, Review, Validate

    roles = [i["role"] for i in items]
    assert "planner" in roles
    assert "researcher" in roles
    assert "implementer" in roles
    assert "reviewer" in roles
    assert "validator" in roles


@pytest.mark.asyncio
async def test_start_mission_only_planner_ready(client):
    mission_id = await _create_and_start(client)

    wi_resp = await client.get(f"/api/missions/{mission_id}/work-items")
    items = wi_resp.json()

    ready = [i for i in items if i["status"] == "ready"]
    assert len(ready) == 1
    assert ready[0]["role"] == "planner"


@pytest.mark.asyncio
async def test_get_next_work_item(client):
    mission_id = await _create_and_start(client)

    resp = await client.post(f"/api/missions/{mission_id}/work-items/next")
    assert resp.status_code == 200
    assert resp.json()["role"] == "planner"


@pytest.mark.asyncio
async def test_work_item_lifecycle(client):
    mission_id = await _create_and_start(client)

    # Get planner
    next_resp = await client.post(f"/api/missions/{mission_id}/work-items/next")
    planner_id = next_resp.json()["id"]

    # Start it
    start_resp = await client.post(f"/api/missions/{mission_id}/work-items/{planner_id}/start")
    assert start_resp.status_code == 200
    assert start_resp.json()["status"] == "running"

    # Complete it
    complete_resp = await client.post(
        f"/api/missions/{mission_id}/work-items/{planner_id}/complete",
        json={"plan": "step 1, step 2"},
    )
    assert complete_resp.status_code == 200
    assert complete_resp.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_advance_unlocks_next_work_item(client):
    mission_id = await _create_and_start(client)

    # Complete planner
    next_resp = await client.post(f"/api/missions/{mission_id}/work-items/next")
    planner_id = next_resp.json()["id"]
    await client.post(f"/api/missions/{mission_id}/work-items/{planner_id}/start")
    await client.post(f"/api/missions/{mission_id}/work-items/{planner_id}/complete")

    # Advance mission
    advance_resp = await client.post(f"/api/missions/{mission_id}/advance")
    assert advance_resp.status_code == 200

    # Researcher should now be ready
    next_resp2 = await client.post(f"/api/missions/{mission_id}/work-items/next")
    assert next_resp2.status_code == 200
    assert next_resp2.json()["role"] == "researcher"


@pytest.mark.asyncio
async def test_mission_completes_when_all_done(client):
    mission_id = await _create_and_start(client)

    # Complete all 5 work items in order
    for _ in range(5):
        await client.post(f"/api/missions/{mission_id}/advance")
        next_resp = await client.post(f"/api/missions/{mission_id}/work-items/next")
        if next_resp.status_code == 404:
            break
        wi_id = next_resp.json()["id"]
        await client.post(f"/api/missions/{mission_id}/work-items/{wi_id}/start")
        await client.post(f"/api/missions/{mission_id}/work-items/{wi_id}/complete")

    # Final advance to check completion
    advance_resp = await client.post(f"/api/missions/{mission_id}/advance")
    assert advance_resp.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_work_item_retry_on_failure(client):
    mission_id = await _create_and_start(client)

    next_resp = await client.post(f"/api/missions/{mission_id}/work-items/next")
    planner_id = next_resp.json()["id"]
    await client.post(f"/api/missions/{mission_id}/work-items/{planner_id}/start")

    # Fail it — should retry (goes back to ready)
    fail_resp = await client.post(
        f"/api/missions/{mission_id}/work-items/{planner_id}/fail?reason=transient+error"
    )
    assert fail_resp.status_code == 200
    assert fail_resp.json()["status"] == "ready"
    assert fail_resp.json()["retry_count"] == 1


@pytest.mark.asyncio
async def test_cannot_start_uncompiled_mission(client):
    resp = await client.post(
        "/api/missions?compile=false",
        json={
            "title": "Not compiled",
            "raw_prompt": "Will not start",
        },
    )
    mission_id = resp.json()["id"]

    start_resp = await client.post(f"/api/missions/{mission_id}/start")
    assert start_resp.status_code == 409


@pytest.mark.asyncio
async def test_events_recorded(client):
    mission_id = await _create_and_start(client)

    events_resp = await client.get(f"/api/missions/{mission_id}/events")
    assert events_resp.status_code == 200
    events = events_resp.json()
    assert len(events) > 0
    event_types = [e["event_type"] for e in events]
    assert "mission.queued" in event_types
