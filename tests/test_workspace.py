"""Workspace API endpoint tests."""

import os

import pytest


@pytest.mark.asyncio
async def test_workspace_info(client):
    resp = await client.get("/api/workspace/info")
    assert resp.status_code == 200
    data = resp.json()
    assert "path" in data
    assert "exists" in data


@pytest.mark.asyncio
async def test_workspace_browse_root(client):
    resp = await client.get("/api/workspace/browse")
    assert resp.status_code == 200
    data = resp.json()
    assert "workspace_root" in data
    assert "entries" in data
    assert "current_path" in data


@pytest.mark.asyncio
async def test_workspace_tree(client):
    resp = await client.get("/api/workspace/tree?max_depth=2")
    assert resp.status_code == 200
    data = resp.json()
    assert "tree" in data
    assert isinstance(data["tree"], list)


@pytest.mark.asyncio
async def test_workspace_validate_path(client, tmp_path):
    resp = await client.get(
        "/api/workspace/validate-path",
        params={"path": str(tmp_path)},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["exists"] is True
    assert data["is_directory"] is True
    assert data["valid"] is True


@pytest.mark.asyncio
async def test_workspace_validate_bad_path(client):
    resp = await client.get(
        "/api/workspace/validate-path",
        params={"path": "/nonexistent/path/xyz"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["exists"] is False
    assert data["valid"] is False


@pytest.mark.asyncio
async def test_workspace_create_dir(client):
    resp = await client.post(
        "/api/workspace/create-dir",
        params={"path": "test_subdir_ws"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["created"] is True


@pytest.mark.asyncio
async def test_workspace_browse_escapes(client):
    resp = await client.get(
        "/api/workspace/browse", params={"path": "../../etc"}
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_workspace_file_not_found(client):
    resp = await client.get(
        "/api/workspace/file",
        params={"path": "nonexistent_file.txt"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_workspace_set_root(client, tmp_path):
    resp = await client.put(
        "/api/workspace/set-root",
        params={"path": str(tmp_path)},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["workspace_root"] == str(tmp_path)


@pytest.mark.asyncio
async def test_workspace_set_root_invalid(client):
    resp = await client.put(
        "/api/workspace/set-root",
        params={"path": "/nonexistent/dir/xyz"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_workspace_mission_dir(client):
    # Create a mission first
    resp = await client.post(
        "/api/missions",
        json={"title": "WS Test", "raw_prompt": "test workspace"},
    )
    mid = resp.json()["id"]
    resp = await client.get(f"/api/workspace/mission/{mid}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["mission_id"] == mid
    assert "missions/" in data["path"]


@pytest.mark.asyncio
async def test_workspace_view_file(client, tmp_path):
    # Set workspace to tmp_path, create a file, then view it
    from af_core.config import settings

    old = settings.workspace_root
    settings.workspace_root = str(tmp_path)
    try:
        test_file = tmp_path / "hello.py"
        test_file.write_text("print('hello')\n")

        resp = await client.get(
            "/api/workspace/file", params={"path": "hello.py"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "hello.py"
        assert "print" in data["content"]
        assert data["lines"] == 2
    finally:
        settings.workspace_root = old
