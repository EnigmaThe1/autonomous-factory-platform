#!/usr/bin/env python3
import json, sys, uuid, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
policy = json.loads((ROOT / "capabilities" / "runtime-orchestration-policy.json").read_text())

prompt = " ".join(sys.argv[1:]).strip() or "unspecified mission"
mission_id = f"mission-{uuid.uuid4().hex[:8]}"

keywords = prompt.lower()
needed = []
if any(k in keywords for k in ["browser", "ui", "frontend", "playwright"]):
    needed.append("browser-ui")
if any(k in keywords for k in ["database", "postgres", "sql", "db"]):
    needed.append("data-db")
if any(k in keywords for k in ["deploy", "infra", "docker", "ops"]):
    needed.append("ops-deploy")
if any(k in keywords for k in ["api", "code", "backend", "web app", "app"]):
    needed.append("coding")
if any(k in keywords for k in ["research", "docs", "investigate"]):
    needed.append("research")

execution_mode = "single_agent"
if len(set(needed)) >= 3:
    execution_mode = "specialist_agents"
if len(set(needed)) >= 4 and ("browser-ui" in needed or "ops-deploy" in needed):
    execution_mode = "agent_team"

graph = {
    "mission_id": mission_id,
    "summary": prompt,
    "execution_mode": execution_mode,
    "phases": [
        {
            "id": "discover",
            "name": "Discover project truth",
            "type": "discover",
            "depends_on": [],
            "required_capabilities": [],
            "status": "planned",
            "exit_criteria": ["Relevant project truth has been identified"]
        },
        {
            "id": "plan",
            "name": "Compile mission and plan",
            "type": "plan",
            "depends_on": ["discover"],
            "required_capabilities": [],
            "status": "planned",
            "exit_criteria": ["Execution contract and minimal plan are complete"]
        },
        {
            "id": "activate",
            "name": "Activate minimum required capabilities",
            "type": "activate",
            "depends_on": ["plan"],
            "required_capabilities": sorted(set(needed)),
            "status": "planned",
            "exit_criteria": ["Required capabilities are available or intentionally deferred"]
        },
        {
            "id": "implement",
            "name": "Execute bounded implementation",
            "type": "implement",
            "depends_on": ["activate"],
            "required_capabilities": sorted(set(needed)),
            "status": "planned",
            "exit_criteria": ["Implementation is complete"]
        },
        {
            "id": "validate",
            "name": "Validate and review",
            "type": "validate",
            "depends_on": ["implement"],
            "required_capabilities": [],
            "status": "planned",
            "exit_criteria": ["Validation and review have completed"]
        },
        {
            "id": "report",
            "name": "Report outcome and update records",
            "type": "report",
            "depends_on": ["validate"],
            "required_capabilities": [],
            "status": "planned",
            "exit_criteria": ["Final report and state update are complete"]
        }
    ],
    "checkpoints": [
        {"id": "checkpoint-plan", "after_phase": "plan", "required": True, "kind": "review"},
        {"id": "checkpoint-activate", "after_phase": "activate", "required": False, "kind": "approval"},
        {"id": "checkpoint-close", "after_phase": "validate", "required": True, "kind": "review"}
    ]
}

# append to graphs log
graphs_path = ROOT / "capabilities" / "execution-graphs.jsonl"
with graphs_path.open("a", encoding="utf-8") as fh:
    fh.write(json.dumps(graph) + "\n")

print(json.dumps(graph, indent=2))
