#!/usr/bin/env python3
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
graphs_path = ROOT / "capabilities" / "execution-graphs.jsonl"
if not graphs_path.exists() or graphs_path.read_text().strip() == "":
    print("No mission graphs recorded.")
    raise SystemExit(0)

lines = [json.loads(line) for line in graphs_path.read_text().splitlines() if line.strip()]
graph = lines[-1]
if len(sys.argv) > 1:
    target = sys.argv[1]
    for item in reversed(lines):
        if item.get("mission_id") == target:
            graph = item
            break

print(f"Mission: {graph['mission_id']}")
print(f"Summary: {graph['summary']}")
print(f"Execution mode: {graph['execution_mode']}")
print("")
print("Phases:")
for phase in graph["phases"]:
    deps = ", ".join(phase.get("depends_on", [])) or "-"
    caps = ", ".join(phase.get("required_capabilities", [])) or "-"
    print(f"- {phase['id']} [{phase['type']}] status={phase['status']}")
    print(f"  name: {phase['name']}")
    print(f"  depends_on: {deps}")
    print(f"  capabilities: {caps}")
