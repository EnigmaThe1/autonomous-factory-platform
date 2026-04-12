#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from datetime import datetime

root = Path(__file__).resolve().parents[1]
weights_path = root / "capabilities" / "evidence-channel-weights.json"
state_path = root / "capabilities" / "evidence-weight-state.json"
weights = json.loads(weights_path.read_text(encoding="utf-8")).get("weights", {})
state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {"version": "v17", "generated_at": None, "capabilities": {}}

mission = " ".join(sys.argv[1:]).lower().strip()
if not mission:
    print("usage: weigh-promotion-evidence.py <mission text>")
    sys.exit(1)

capabilities = {
    "research_pack": {
        "mission_contract": 1 if any(k in mission for k in ["research", "docs", "latest", "investigate"]) else 0,
        "environment_fit": 1,
        "execution_friction": 1 if "unknown" in mission or "figure out" in mission else 0,
        "fallback_weakness": 0,
        "validation_leverage": 1,
        "trust_source_confidence": 1
    },
    "coding_pack": {
        "mission_contract": 1 if any(k in mission for k in ["build", "code", "python", "app", "implement"]) else 0,
        "environment_fit": 1,
        "execution_friction": 1 if any(k in mission for k in ["refactor", "fix", "integrate"]) else 0,
        "fallback_weakness": 1 if "manual" in mission else 0,
        "validation_leverage": 1,
        "trust_source_confidence": 1
    },
    "browser_ui_pack": {
        "mission_contract": 1 if any(k in mission for k in ["browser", "ui", "frontend", "visual"]) else 0,
        "environment_fit": 1 if any(k in mission for k in ["browser", "ui", "frontend"]) else 0,
        "execution_friction": 1 if any(k in mission for k in ["test", "regression", "acceptance"]) else 0,
        "fallback_weakness": 1 if "manual qa" in mission else 0,
        "validation_leverage": 1,
        "trust_source_confidence": 1
    },
    "data_db_pack": {
        "mission_contract": 1 if any(k in mission for k in ["db", "database", "postgres", "sql"]) else 0,
        "environment_fit": 1 if any(k in mission for k in ["db", "database", "postgres"]) else 0,
        "execution_friction": 1 if any(k in mission for k in ["schema", "query", "data"]) else 0,
        "fallback_weakness": 1 if "csv" in mission or "manual query" in mission else 0,
        "validation_leverage": 1,
        "trust_source_confidence": 1
    },
    "ops_deploy_pack": {
        "mission_contract": 1 if any(k in mission for k in ["deploy", "docker", "runtime", "infra", "prod"]) else 0,
        "environment_fit": 1 if any(k in mission for k in ["docker", "runtime", "infra"]) else 0,
        "execution_friction": 1 if any(k in mission for k in ["logs", "diagnostic", "healthcheck"]) else 0,
        "fallback_weakness": 1 if "manual ssh" in mission else 0,
        "validation_leverage": 1,
        "trust_source_confidence": 1
    }
}

results = {}
for cap, channels in capabilities.items():
    score = sum(weights.get(ch, 1) * val for ch, val in channels.items())
    if score >= 8:
        strength = "strong"
        decision = "staged_for_activation"
    elif score >= 4:
        strength = "moderate"
        decision = "suggested"
    else:
        strength = "weak"
        decision = "defer_until_trigger"
    results[cap] = {
        "score": score,
        "evidence_strength": strength,
        "weighted_decision": decision,
        "channels": channels,
        "evaluated_at": datetime.utcnow().isoformat() + "Z"
    }

state["generated_at"] = datetime.utcnow().isoformat() + "Z"
state["capabilities"] = results
state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
print(json.dumps(results, indent=2))
