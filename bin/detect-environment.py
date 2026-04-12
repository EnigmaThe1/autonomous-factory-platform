#!/usr/bin/env python3
import json, os, platform, shutil
from pathlib import Path

report = {
    "os": platform.system(),
    "platform": platform.platform(),
    "python_version": platform.python_version(),
    "cwd": str(Path.cwd()),
    "workspace_detected": (Path.cwd() / ".git").exists() or (Path.cwd() / "package.json").exists() or (Path.cwd() / "pyproject.toml").exists(),
    "container_signals": {
        "docker_env": Path("/.dockerenv").exists(),
        "container_env_var": any(k in os.environ for k in ["container", "CONTAINER", "DEVCONTAINER"]),
    },
    "ci": any(k in os.environ for k in ["CI", "GITHUB_ACTIONS", "GITLAB_CI", "BUILD_ID"]),
    "remote_session": any(k in os.environ for k in ["SSH_CONNECTION", "SSH_CLIENT", "SSH_TTY"]),
    "runtimes": {
        "python": shutil.which("python") or shutil.which("python3"),
        "node": shutil.which("node"),
        "npm": shutil.which("npm"),
        "pnpm": shutil.which("pnpm"),
        "yarn": shutil.which("yarn"),
        "git": shutil.which("git")
    }
}
print(json.dumps(report, indent=2))
