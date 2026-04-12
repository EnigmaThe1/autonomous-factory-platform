"""End-to-end integration test — full mission lifecycle."""

import pytest


@pytest.mark.asyncio
async def test_full_mission_lifecycle(client):
    """Exercise the complete flow: create -> compile -> start -> run all agents -> complete."""

    # 1. Create mission (auto-compiles)
    create_resp = await client.post(
        "/api/missions",
        json={
            "title": "Implement user authentication",
            "raw_prompt": (
                "Create a JWT-based authentication system in ./src/auth. "
                "Must include login, signup, and token refresh endpoints. "
                "Ensure proper password hashing and input validation."
            ),
        },
    )
    assert create_resp.status_code == 201
    mission = create_resp.json()
    mission_id = mission["id"]
    assert mission["status"] == "compiled"
    assert mission["contract"] is not None
    assert mission["contract"]["normalized_objective"] == "Implement user authentication"
    # Findings may or may not be present depending on prompt analysis

    # 2. Start mission
    start_resp = await client.post(f"/api/missions/{mission_id}/start")
    assert start_resp.status_code == 200
    assert start_resp.json()["status"] == "queued"

    # 3. Verify work items seeded
    wi_resp = await client.get(f"/api/missions/{mission_id}/work-items")
    work_items = wi_resp.json()
    assert len(work_items) == 5
    roles = [wi["role"] for wi in work_items]
    assert roles == ["planner", "researcher", "implementer", "reviewer", "validator"]

    # 4. Run through all 5 agents
    completed_count = 0
    for step in range(10):  # safety limit
        # Advance to unlock next items
        await client.post(f"/api/missions/{mission_id}/advance")

        # Get next ready item
        next_resp = await client.post(f"/api/missions/{mission_id}/work-items/next")
        if next_resp.status_code == 404:
            break

        wi = next_resp.json()
        wi_id = wi["id"]

        # Start the work item
        start_wi = await client.post(f"/api/missions/{mission_id}/work-items/{wi_id}/start")
        assert start_wi.json()["status"] == "running"

        # Complete it with mock output
        complete_wi = await client.post(
            f"/api/missions/{mission_id}/work-items/{wi_id}/complete",
            json={"result": f"Completed {wi['role']} phase"},
        )
        assert complete_wi.json()["status"] == "completed"
        completed_count += 1

    assert completed_count == 5

    # 5. Final advance — mission should complete
    final_resp = await client.post(f"/api/missions/{mission_id}/advance")
    assert final_resp.json()["status"] == "completed"
    assert final_resp.json()["final_verdict"] == "completed"

    # 6. Verify events recorded
    events_resp = await client.get(f"/api/missions/{mission_id}/events")
    events = events_resp.json()
    event_types = [e["event_type"] for e in events]
    assert "mission.queued" in event_types
    assert "mission.completed" in event_types
    assert "work_item.started" in event_types
    assert "work_item.completed" in event_types

    # 7. Verify mission is in completed list
    list_resp = await client.get("/api/missions?status=completed")
    assert list_resp.json()["total"] >= 1


@pytest.mark.asyncio
async def test_mission_with_failure_and_retry(client):
    """Test that transient failures trigger retries."""
    create_resp = await client.post(
        "/api/missions",
        json={
            "title": "Test retry behavior",
            "raw_prompt": "Create a simple test file in ./tests/test_retry.py",
        },
    )
    mission_id = create_resp.json()["id"]

    await client.post(f"/api/missions/{mission_id}/start")
    await client.post(f"/api/missions/{mission_id}/advance")

    # Get planner and start it
    next_resp = await client.post(f"/api/missions/{mission_id}/work-items/next")
    wi_id = next_resp.json()["id"]
    await client.post(f"/api/missions/{mission_id}/work-items/{wi_id}/start")

    # Fail it — should go back to ready (retry)
    fail_resp = await client.post(
        f"/api/missions/{mission_id}/work-items/{wi_id}/fail?reason=Connection+timed+out"
    )
    assert fail_resp.json()["status"] == "ready"
    assert fail_resp.json()["retry_count"] == 1

    # Start and complete it on retry
    await client.post(f"/api/missions/{mission_id}/work-items/{wi_id}/start")
    complete_resp = await client.post(
        f"/api/missions/{mission_id}/work-items/{wi_id}/complete",
        json={"result": "Completed on retry"},
    )
    assert complete_resp.json()["status"] == "completed"
    assert complete_resp.json()["retry_count"] == 1


@pytest.mark.asyncio
async def test_mission_cancel_during_execution(client):
    """Test cancelling a running mission."""
    create_resp = await client.post(
        "/api/missions",
        json={
            "title": "Mission to cancel",
            "raw_prompt": "Build something that will be cancelled",
        },
    )
    mission_id = create_resp.json()["id"]
    await client.post(f"/api/missions/{mission_id}/start")

    cancel_resp = await client.post(f"/api/missions/{mission_id}/cancel")
    assert cancel_resp.json()["status"] == "cancelled"

    # Cannot start again
    start_again = await client.post(f"/api/missions/{mission_id}/start")
    assert start_again.status_code == 409
