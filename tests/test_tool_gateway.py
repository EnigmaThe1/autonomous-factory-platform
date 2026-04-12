"""Tool gateway tests."""

import os
import tempfile

import pytest

from af_core.models.enums import ToolCategory
from af_core.services.tool_gateway import ToolGateway, ToolPolicy


@pytest.fixture
def workspace():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        os.makedirs(os.path.join(tmpdir, "src"))
        with open(os.path.join(tmpdir, "src", "main.py"), "w") as f:
            f.write("print('hello')\n")
        with open(os.path.join(tmpdir, ".env"), "w") as f:
            f.write("SECRET=value\n")
        yield tmpdir


@pytest.fixture
def gateway(workspace):
    return ToolGateway(workspace)


class TestPathValidation:
    def test_valid_path(self, gateway):
        valid, _ = gateway.validate_path("src/main.py")
        assert valid

    def test_outside_workspace(self, gateway):
        valid, reason = gateway.validate_path("../../etc/passwd")
        assert not valid
        assert "outside workspace" in reason

    def test_protected_path(self, gateway):
        valid, reason = gateway.validate_path(".env")
        assert not valid
        assert "protected" in reason


class TestReadFile:
    @pytest.mark.asyncio
    async def test_read_existing_file(self, gateway):
        result = await gateway.read_file("src/main.py")
        assert result.success
        assert "hello" in result.output

    @pytest.mark.asyncio
    async def test_read_missing_file(self, gateway):
        result = await gateway.read_file("src/nonexistent.py")
        assert not result.success
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_read_protected_file(self, gateway):
        result = await gateway.read_file(".env")
        assert not result.success
        assert "protected" in result.error


class TestWriteFile:
    @pytest.mark.asyncio
    async def test_write_new_file(self, gateway, workspace):
        result = await gateway.write_file("src/new_file.py", "# new file\n")
        assert result.success
        assert os.path.exists(os.path.join(workspace, "src/new_file.py"))

    @pytest.mark.asyncio
    async def test_write_creates_directories(self, gateway, workspace):
        result = await gateway.write_file("src/deep/nested/file.py", "# deep\n")
        assert result.success
        assert os.path.exists(os.path.join(workspace, "src/deep/nested/file.py"))

    @pytest.mark.asyncio
    async def test_write_outside_workspace_fails(self, gateway):
        result = await gateway.write_file("../../evil.py", "bad")
        assert not result.success

    @pytest.mark.asyncio
    async def test_write_denied_by_policy(self, workspace):
        policy = ToolPolicy(allowed_categories={ToolCategory.READ_ONLY})
        gw = ToolGateway(workspace, policy)
        result = await gw.write_file("test.py", "content")
        assert not result.success
        assert "not allowed" in result.error


class TestListDirectory:
    @pytest.mark.asyncio
    async def test_list_workspace_root(self, gateway):
        result = await gateway.list_directory(".")
        assert result.success
        assert "src" in result.output

    @pytest.mark.asyncio
    async def test_list_subdirectory(self, gateway):
        result = await gateway.list_directory("src")
        assert result.success
        assert "main.py" in result.output


class TestRunCommand:
    @pytest.mark.asyncio
    async def test_run_simple_command(self, workspace):
        policy = ToolPolicy(allowed_categories={ToolCategory.READ_ONLY, ToolCategory.TERMINAL})
        gw = ToolGateway(workspace, policy)
        result = await gw.run_command(["echo", "hello"])
        assert result.success
        assert "hello" in result.output

    @pytest.mark.asyncio
    async def test_run_command_not_found(self, workspace):
        policy = ToolPolicy(allowed_categories={ToolCategory.READ_ONLY, ToolCategory.TERMINAL})
        gw = ToolGateway(workspace, policy)
        result = await gw.run_command(["nonexistent_cmd_12345"])
        assert not result.success

    @pytest.mark.asyncio
    async def test_terminal_denied_by_policy(self, gateway):
        # Default policy doesn't include TERMINAL
        result = await gateway.run_command(["echo", "hello"])
        assert not result.success
        assert "not allowed" in result.error

    @pytest.mark.asyncio
    async def test_command_timeout(self, workspace):
        policy = ToolPolicy(
            allowed_categories={ToolCategory.READ_ONLY, ToolCategory.TERMINAL},
            max_timeout_seconds=1,
        )
        gw = ToolGateway(workspace, policy)
        result = await gw.run_command(["sleep", "10"], timeout=1)
        assert not result.success
        assert "timed out" in result.error.lower()
