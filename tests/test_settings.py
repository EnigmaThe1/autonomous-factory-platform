"""Settings API tests."""

import pytest


@pytest.mark.asyncio
async def test_list_settings_seeds_defaults(client):
    resp = await client.get("/api/settings")
    assert resp.status_code == 200
    data = resp.json()
    cats = data["categories"]
    assert "providers" in cats
    assert "api_keys" in cats
    assert "execution" in cats
    assert "connectors" in cats
    assert "safety" in cats
    # Check we have provider model settings
    provider_keys = [s["key"] for s in cats["providers"]]
    assert "providers.planner_model" in provider_keys
    assert "providers.reviewer_model" in provider_keys


@pytest.mark.asyncio
async def test_list_category(client):
    # Seed defaults first
    await client.get("/api/settings")
    resp = await client.get("/api/settings/execution")
    assert resp.status_code == 200
    data = resp.json()
    keys = [s["key"] for s in data]
    assert "execution.default_step_budget" in keys


@pytest.mark.asyncio
async def test_update_setting(client):
    # Seed and get a setting ID
    resp = await client.get("/api/settings")
    cats = resp.json()["categories"]
    setting = cats["execution"][0]
    sid = setting["id"]

    resp = await client.put(
        f"/api/settings/{sid}",
        json={"value": "999"},
    )
    assert resp.status_code == 200
    assert resp.json()["value"] == "999"


@pytest.mark.asyncio
async def test_secret_masking(client):
    resp = await client.get("/api/settings")
    cats = resp.json()["categories"]
    # API keys should be masked if they have values
    for s in cats["api_keys"]:
        if s["is_secret"] and s["value"] and s["value"] != "****":
            # Non-empty secrets should be masked
            assert "****" in s["value"] or len(s["value"]) <= 8


@pytest.mark.asyncio
async def test_create_custom_setting(client):
    resp = await client.post(
        "/api/settings",
        params={
            "category": "custom",
            "key": "custom.my_setting",
            "value": "hello",
            "description": "A custom setting",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["key"] == "custom.my_setting"
    assert resp.json()["value"] == "hello"


@pytest.mark.asyncio
async def test_create_duplicate_setting_fails(client):
    await client.post(
        "/api/settings",
        params={"category": "test", "key": "test.dup", "value": "a"},
    )
    resp = await client.post(
        "/api/settings",
        params={"category": "test", "key": "test.dup", "value": "b"},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_delete_setting(client):
    resp = await client.post(
        "/api/settings",
        params={"category": "test", "key": "test.deleteme", "value": "x"},
    )
    sid = resp.json()["id"]
    resp = await client.delete(f"/api/settings/{sid}")
    assert resp.status_code == 200
    assert resp.json()["deleted"] is True


@pytest.mark.asyncio
async def test_update_nonexistent_setting(client):
    resp = await client.put(
        "/api/settings/nonexistent",
        json={"value": "x"},
    )
    assert resp.status_code == 404
