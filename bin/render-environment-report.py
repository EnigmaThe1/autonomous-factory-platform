#!/usr/bin/env python3
import os, platform, shutil
from pathlib import Path

report = {
    "OS": platform.system(),
    "Platform": platform.platform(),
    "Current working directory": str(Path.cwd()),
    "Workspace detected": (Path.cwd() / ".git").exists() or (Path.cwd() / "package.json").exists() or (Path.cwd() / "pyproject.toml").exists(),
    "Container": Path("/.dockerenv").exists() or any(k in os.environ for k in ["container", "CONTAINER", "DEVCONTAINER"]),
    "CI": any(k in os.environ for k in ["CI", "GITHUB_ACTIONS", "GITLAB_CI", "BUILD_ID"]),
    "Remote session": any(k in os.environ for k in ["SSH_CONNECTION", "SSH_CLIENT", "SSH_TTY"]),
    "Python": shutil.which("python") or shutil.which("python3"),
    "Node": shutil.which("node"),
    "Git": shutil.which("git")
}
print("# Environment Report
")
for k, v in report.items():
    print(f"- **{k}:** {v}")
