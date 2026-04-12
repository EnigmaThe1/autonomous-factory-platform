#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from datetime import datetime

root = Path(__file__).resolve().parents[1]
registry_path = root / "capabilities" / "registry.json"
state_path = root / "capabilities" / "capability-decision-state.json"

registry = {}
if registry_path.exists():
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except Exception:
        registry = {}

state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {"version": "v15", "generated_at": None, "capabilities": {}}

mission = " ".join(sys.argv[1:]).strip().lower()
if not mission:
    print("usage: decide-capability-state.py <mission text>")
    sys.exit(1)

keyword_map = {
    "browser": "browser_ui_pack",
    "ui": "browser_ui_pack",
    "playwright": "browser_ui_pack",
    "database": "data_db_pack",
    "db": "data_db_pack",
    "postgres": "data_db_pack",
    "deploy": "ops_deploy_pack",
    "docker": "ops_deploy_pack",
    "infra": "ops_deploy_pack",
    "research": "research_pack",
    "docs": "research_pack",
    "code": "coding_pack",
    "python": "coding_pack",
    "javascript": "coding_pack"
}

hits = {}
for token, capability in keyword_map.items():
    if token in mission:
        hits.setdefault(capability, 0)
        hits[capability] += 1

results = {}
for capability, score in sorted(hits.items()):
    if score >= 2 or capability in ("coding_pack", "research_pack") and score >= 1:
        decision = "staged_for_activation"
        why = "mission text shows direct near-term need"
    else:
        decision = "suggested"
        why = "capability may help but evidence is not yet strong enough for staging"
    results[capability] = {
        "decision": decision,
        "score": score,
        "reason": why,
        "evaluated_at": datetime.utcnow().isoformat() + "Z"
    }
    state["capabilities"][capability] = results[capability]

state["generated_at"] = datetime.utcnow().isoformat() + "Z"
state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
print(json.dumps(results, indent=2))
