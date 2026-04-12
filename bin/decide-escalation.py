#!/usr/bin/env python3
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
policy = json.loads((ROOT / "capabilities" / "escalation-policy.json").read_text())
graph_path = ROOT / "capabilities" / "execution-graphs.jsonl"

if not graph_path.exists() or graph_path.read_text().strip() == "":
    print(json.dumps({"decision": policy["default_mode"], "reason": "no_graph_available"}, indent=2))
    raise SystemExit(0)

lines = [json.loads(line) for line in graph_path.read_text().splitlines() if line.strip()]
graph = lines[-1]
if len(sys.argv) > 1:
    target = sys.argv[1]
    for item in reversed(lines):
        if item.get("mission_id") == target:
            graph = item
            break

cap_count = len({cap for phase in graph["phases"] for cap in phase.get("required_capabilities", [])})
branching = sum(1 for phase in graph["phases"] if len(phase.get("depends_on", [])) > 1)

decision = "single_agent"
reason = "coordination overhead likely outweighs benefit"

if cap_count >= 3:
    decision = "specialist_agents"
    reason = "multiple capability families are required"
if graph.get("execution_mode") == "agent_team" or cap_count >= 4 or branching >= 2:
    decision = "agent_team"
    reason = "mission has broader multi-domain coordination needs"

report = {
    "mission_id": graph["mission_id"],
    "recommended_mode": decision,
    "reason": reason,
    "questions": policy["mode_selection_questions"],
    "hard_limits": policy["hard_limits"]
}
print(json.dumps(report, indent=2))
