"""Mission compiler tests."""

import pytest


@pytest.mark.asyncio
async def test_create_mission_auto_compiles(client):
    resp = await client.post(
        "/api/missions",
        json={
            "title": "Build user authentication system",
            "raw_prompt": (
                "Create a JWT-based auth system in ./src/auth"
                " with login and signup endpoints"
            ),
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "compiled"
    assert data["contract"] is not None
    assert data["contract"]["normalized_objective"] == "Build user authentication system"
    assert data["contract"]["normalized_scope"]["referenced_paths"]


@pytest.mark.asyncio
async def test_create_mission_without_compile(client):
    resp = await client.post(
        "/api/missions?compile=false",
        json={
            "title": "Deferred compile test",
            "raw_prompt": "This will be compiled later",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "pending"
    assert data["contract"] is None


@pytest.mark.asyncio
async def test_explicit_compile_endpoint(client):
    # Create without compile
    create_resp = await client.post(
        "/api/missions?compile=false",
        json={
            "title": "Compile later",
            "raw_prompt": "Implement feature in ./src/feature with proper tests",
        },
    )
    mission_id = create_resp.json()["id"]
    assert create_resp.json()["status"] == "pending"

    # Now compile
    compile_resp = await client.post(f"/api/missions/{mission_id}/compile")
    assert compile_resp.status_code == 200
    data = compile_resp.json()
    assert data["status"] == "compiled"
    assert data["contract"] is not None


@pytest.mark.asyncio
async def test_compiler_detects_short_prompt(client):
    resp = await client.post(
        "/api/missions",
        json={
            "title": "Vague",
            "raw_prompt": "fix it",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    # Should have an underspecified warning finding
    findings = data["findings"]
    categories = [f["category"] for f in findings]
    assert "ambiguity" in categories
    underspec = [
        f for f in findings if f["details"] and f["details"].get("type") == "underspecified"
    ]
    assert len(underspec) > 0


@pytest.mark.asyncio
async def test_compiler_detects_no_output_action(client):
    resp = await client.post(
        "/api/missions",
        json={
            "title": "Research only mission",
            "raw_prompt": (
                "Analyze the ./src/utils directory and"
                " understand the architecture patterns"
            ),
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    findings = data["findings"]
    no_output = [f for f in findings if f.get("details", {}).get("type") == "no_clear_output"]
    assert len(no_output) > 0


@pytest.mark.asyncio
async def test_compiler_extracts_paths(client):
    resp = await client.post(
        "/api/missions",
        json={
            "title": "Multi-path mission",
            "raw_prompt": "Read ./src/main.py and ./tests/test_main.py then create ./src/utils.py",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    scope = data["contract"]["normalized_scope"]
    assert len(scope["referenced_paths"]) >= 3
    assert scope["estimated_breadth"] in ("narrow", "broad")


@pytest.mark.asyncio
async def test_compiler_detects_destructive_action(client):
    resp = await client.post(
        "/api/missions",
        json={
            "title": "Cleanup mission",
            "raw_prompt": "Delete all temporary files in ./tmp and remove ./old_config.json",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    findings = data["findings"]
    destructive = [f for f in findings if f.get("details", {}).get("type") == "destructive_action"]
    assert len(destructive) > 0
