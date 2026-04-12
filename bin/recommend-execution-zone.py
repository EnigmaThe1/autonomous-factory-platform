#!/usr/bin/env python3
import os
from pathlib import Path

zones = []
if Path("/.dockerenv").exists() or any(k in os.environ for k in ["container", "CONTAINER", "DEVCONTAINER"]):
    zones.append(("container/devcontainer", "Available and generally preferable for riskier or dependency-heavy work."))
if any(k in os.environ for k in ["CI", "GITHUB_ACTIONS", "GITLAB_CI", "BUILD_ID"]):
    zones.append(("ci", "Useful for repeatable validation and automation runs."))
zones.append(("workspace", "Default for normal project work when no safer isolated zone is needed."))

print("# Recommended Execution Zone
")
for name, note in zones:
    print(f"- **{name}** — {note}")
