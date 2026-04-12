#!/usr/bin/env bash
set -euo pipefail

echo "Autonomous Factory Hybrid Pack bootstrap"
echo
echo "Claude entry points:"
echo "  - CLAUDE.md"
echo "  - .claude/settings.json"
echo
echo "Codex entry points:"
echo "  - AGENTS.md"
echo "  - .codex/config.toml"
echo
echo "Shared framework:"
echo "  - agents/"
echo "  - skills/"
echo "  - capabilities/"
echo "  - templates/"
echo "  - bin/"
echo
echo "Claude first prompt:"
echo "Read CLAUDE.md and inspect the agents, skills, capabilities, templates, and helper scripts in this project. Explain how you will use this autonomy system on the task."
echo
echo "Codex first prompt:"
echo "Read AGENTS.md and inspect the agents, skills, capabilities, templates, and helper scripts in this project. Explain how you will use this autonomy system on the task."
