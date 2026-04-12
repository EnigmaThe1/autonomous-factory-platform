"""Tool Gateway — executes tools behind policy and evidence gates.

All tool invocations are mediated through this gateway. It enforces:
- Scope boundaries (workspace containment)
- Tool category policy
- Timeout/resource limits
- Evidence recording
"""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

from af_core.models.enums import ToolCategory

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    """Result of a tool execution."""

    success: bool
    output: str = ""
    error: str | None = None
    duration_ms: int = 0
    tool_name: str = ""
    category: ToolCategory = ToolCategory.READ_ONLY


@dataclass
class ToolPolicy:
    """Policy constraints for tool execution."""

    allowed_categories: set[ToolCategory] = field(
        default_factory=lambda: {
            ToolCategory.READ_ONLY,
            ToolCategory.BOUNDED_WRITE,
            ToolCategory.VALIDATION,
        }
    )
    max_timeout_seconds: int = 300
    max_output_bytes: int = 10 * 1024 * 1024  # 10MB
    protected_paths: list[str] = field(
        default_factory=lambda: [".env", ".git/config", "credentials"]
    )


class ToolGateway:
    """Mediates all tool invocations with policy enforcement."""

    def __init__(self, workspace_root: str, policy: ToolPolicy | None = None) -> None:
        self.workspace_root = os.path.abspath(workspace_root)
        self.policy = policy or ToolPolicy()

    def validate_path(self, path: str) -> tuple[bool, str]:
        """Check if a path is within the workspace and not protected."""
        abs_path = os.path.abspath(os.path.join(self.workspace_root, path))

        # Must be within workspace
        if not abs_path.startswith(self.workspace_root):
            return False, f"Path {path} is outside workspace"

        # Check protected paths
        rel_path = os.path.relpath(abs_path, self.workspace_root)
        for protected in self.policy.protected_paths:
            if rel_path.startswith(protected) or protected in rel_path:
                return False, f"Path {path} is protected"

        return True, ""

    async def read_file(self, path: str) -> ToolResult:
        """Read a file within the workspace."""
        valid, reason = self.validate_path(path)
        if not valid:
            return ToolResult(
                success=False,
                error=reason,
                tool_name="read_file",
                category=ToolCategory.READ_ONLY,
            )

        abs_path = os.path.join(self.workspace_root, path)
        try:
            content = Path(abs_path).read_text(encoding="utf-8", errors="replace")
            if len(content) > self.policy.max_output_bytes:
                content = content[: self.policy.max_output_bytes]
            return ToolResult(
                success=True,
                output=content,
                tool_name="read_file",
                category=ToolCategory.READ_ONLY,
            )
        except FileNotFoundError:
            return ToolResult(
                success=False,
                error=f"File not found: {path}",
                tool_name="read_file",
                category=ToolCategory.READ_ONLY,
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                tool_name="read_file",
                category=ToolCategory.READ_ONLY,
            )

    async def write_file(self, path: str, content: str) -> ToolResult:
        """Write a file within the workspace."""
        if ToolCategory.BOUNDED_WRITE not in self.policy.allowed_categories:
            return ToolResult(
                success=False,
                error="Write operations not allowed by policy",
                tool_name="write_file",
                category=ToolCategory.BOUNDED_WRITE,
            )

        valid, reason = self.validate_path(path)
        if not valid:
            return ToolResult(
                success=False,
                error=reason,
                tool_name="write_file",
                category=ToolCategory.BOUNDED_WRITE,
            )

        abs_path = os.path.join(self.workspace_root, path)
        try:
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            Path(abs_path).write_text(content, encoding="utf-8")
            return ToolResult(
                success=True,
                output=f"Written {len(content)} bytes to {path}",
                tool_name="write_file",
                category=ToolCategory.BOUNDED_WRITE,
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                tool_name="write_file",
                category=ToolCategory.BOUNDED_WRITE,
            )

    async def list_directory(self, path: str = ".") -> ToolResult:
        """List files in a directory within the workspace."""
        valid, reason = self.validate_path(path)
        if not valid:
            return ToolResult(
                success=False,
                error=reason,
                tool_name="list_directory",
                category=ToolCategory.READ_ONLY,
            )

        abs_path = os.path.join(self.workspace_root, path)
        try:
            entries = sorted(os.listdir(abs_path))
            output = "\n".join(entries)
            return ToolResult(
                success=True,
                output=output,
                tool_name="list_directory",
                category=ToolCategory.READ_ONLY,
            )
        except FileNotFoundError:
            return ToolResult(
                success=False,
                error=f"Directory not found: {path}",
                tool_name="list_directory",
                category=ToolCategory.READ_ONLY,
            )

    async def run_command(
        self,
        command: list[str],
        timeout: int | None = None,
        cwd: str | None = None,
    ) -> ToolResult:
        """Run a bounded terminal command within the workspace."""
        if ToolCategory.TERMINAL not in self.policy.allowed_categories:
            return ToolResult(
                success=False,
                error="Terminal operations not allowed by policy",
                tool_name="run_command",
                category=ToolCategory.TERMINAL,
            )

        effective_timeout = min(
            timeout or self.policy.max_timeout_seconds,
            self.policy.max_timeout_seconds,
        )

        work_dir = self.workspace_root
        if cwd:
            valid, reason = self.validate_path(cwd)
            if not valid:
                return ToolResult(
                    success=False,
                    error=reason,
                    tool_name="run_command",
                    category=ToolCategory.TERMINAL,
                )
            work_dir = os.path.join(self.workspace_root, cwd)

        try:
            proc = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=work_dir,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=effective_timeout)

            output = stdout.decode("utf-8", errors="replace")
            err = stderr.decode("utf-8", errors="replace")

            if len(output) > self.policy.max_output_bytes:
                output = output[: self.policy.max_output_bytes] + "\n...[truncated]"

            return ToolResult(
                success=proc.returncode == 0,
                output=output,
                error=err if proc.returncode != 0 else None,
                tool_name="run_command",
                category=ToolCategory.TERMINAL,
            )
        except TimeoutError:
            return ToolResult(
                success=False,
                error=f"Command timed out after {effective_timeout}s",
                tool_name="run_command",
                category=ToolCategory.TERMINAL,
            )
        except FileNotFoundError:
            return ToolResult(
                success=False,
                error=f"Command not found: {command[0]}",
                tool_name="run_command",
                category=ToolCategory.TERMINAL,
            )

    async def run_validation(self, command: list[str], timeout: int | None = None) -> ToolResult:
        """Run a validation/test command."""
        if ToolCategory.VALIDATION not in self.policy.allowed_categories:
            return ToolResult(
                success=False,
                error="Validation operations not allowed by policy",
                tool_name="run_validation",
                category=ToolCategory.VALIDATION,
            )

        result = await self.run_command(command, timeout=timeout)
        result.tool_name = "run_validation"
        result.category = ToolCategory.VALIDATION
        return result
