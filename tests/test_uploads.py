"""File and zip upload tests."""

import io
import zipfile

import pytest


@pytest.mark.asyncio
async def test_upload_single_file(client):
    resp = await client.post(
        "/api/uploads/file",
        files={"file": ("hello.py", b"print('hello')\n", "text/x-python")},
        data={"dest": ""},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["filename"] == "hello.py"
    assert data["size"] == 15


@pytest.mark.asyncio
async def test_upload_file_to_subdirectory(client):
    resp = await client.post(
        "/api/uploads/file",
        files={"file": ("config.json", b'{"key": "value"}', "application/json")},
        data={"dest": "src/config"},
    )
    assert resp.status_code == 200
    assert "src/config/config.json" in resp.json()["path"]


@pytest.mark.asyncio
async def test_upload_file_with_mission(client):
    # Create a mission first
    mission_resp = await client.post(
        "/api/missions?compile=false",
        json={
            "title": "Upload test",
            "raw_prompt": "Test file upload",
        },
    )
    mission_id = mission_resp.json()["id"]

    resp = await client.post(
        "/api/uploads/file",
        files={"file": ("data.txt", b"test data\n", "text/plain")},
        data={"dest": "", "mission_id": mission_id},
    )
    assert resp.status_code == 200
    assert "artifact_id" in resp.json()


@pytest.mark.asyncio
async def test_upload_multiple_files(client):
    resp = await client.post(
        "/api/uploads/files",
        files=[
            ("files", ("a.txt", b"aaa", "text/plain")),
            ("files", ("b.txt", b"bbb", "text/plain")),
            ("files", ("c.txt", b"ccc", "text/plain")),
        ],
        data={"dest": "batch"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["uploaded"] == 3
    assert len(data["files"]) == 3


@pytest.mark.asyncio
async def test_upload_and_extract_zip(client):
    # Create a zip in memory
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("readme.md", "# Hello\n")
        zf.writestr("src/main.py", "print('hello')\n")
        zf.writestr("src/utils.py", "def helper(): pass\n")
    buf.seek(0)

    resp = await client.post(
        "/api/uploads/zip",
        files={"file": ("project.zip", buf.getvalue(), "application/zip")},
        data={"dest": "project"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["extracted_count"] == 3
    paths = [f["path"] for f in data["files"]]
    assert any("readme.md" in p for p in paths)
    assert any("main.py" in p for p in paths)


@pytest.mark.asyncio
async def test_zip_skips_traversal_paths(client):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("good.txt", "safe content\n")
        zf.writestr("../../../etc/evil.txt", "bad content\n")
    buf.seek(0)

    resp = await client.post(
        "/api/uploads/zip",
        files={"file": ("sneaky.zip", buf.getvalue(), "application/zip")},
        data={"dest": ""},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["extracted_count"] == 1
    assert data["skipped_count"] >= 1


@pytest.mark.asyncio
async def test_zip_with_mission(client):
    mission_resp = await client.post(
        "/api/missions?compile=false",
        json={
            "title": "Zip upload test",
            "raw_prompt": "Test zip upload",
        },
    )
    mission_id = mission_resp.json()["id"]

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("blueprint.md", "# Blueprint\n")
    buf.seek(0)

    resp = await client.post(
        "/api/uploads/zip",
        files={"file": ("blueprint.zip", buf.getvalue(), "application/zip")},
        data={"dest": "blueprints", "mission_id": mission_id},
    )
    assert resp.status_code == 200
    assert "artifact_id" in resp.json()


@pytest.mark.asyncio
async def test_reject_non_zip(client):
    resp = await client.post(
        "/api/uploads/zip",
        files={"file": ("fake.zip", b"this is not a zip", "application/zip")},
        data={"dest": ""},
    )
    assert resp.status_code == 400
    assert "not a valid zip" in resp.json()["detail"]
