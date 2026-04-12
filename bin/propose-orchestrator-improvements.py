#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

root = Path(__file__).resolve().parents[1]
state_path = root / "capabilities" / "orchestrator-state.json"
log_path = root / "capabilities" / "routing-quality-log.jsonl"
improvement_log_path = root / "capabilities" / "orchestrator-improvement-log.jsonl"

state = json.loads(state_path.read_text(encoding="utf-8"))
entries = []
if log_path.exists():
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except Exception:
            pass

adjustments = []
too_late = [e for e in entries if e.get("quality_label") in ("late_escalation", "missed_specialist")]
too_early = [e for e in entries if e.get("quality_label") in ("unnecessary_escalation", "over_routed")]
good_validation = [e for e in entries if e.get("quality_label") == "validation_helped"]

if len(too_late) >= 2:
    old = state["routing_biases"].get("specialist_escalation_sensitivity", 0.6)
    new = round(min(0.9, old + 0.05), 2)
    state["routing_biases"]["specialist_escalation_sensitivity"] = new
    adjustments.append({
        "area": "specialist_escalation_sensitivity",
        "from": old,
        "to": new,
        "reason": "repeated late-escalation outcomes suggest slightly earlier specialist escalation"
    })

if len(too_early) >= 2:
    old = state["routing_biases"].get("prefer_single_agent_for_simple_work", 0.7)
    new = round(min(0.9, old + 0.05), 2)
    state["routing_biases"]["prefer_single_agent_for_simple_work"] = new
    adjustments.append({
        "area": "prefer_single_agent_for_simple_work",
        "from": old,
        "to": new,
        "reason": "repeated over-routing outcomes suggest staying single-agent slightly longer for simpler work"
    })

if len(good_validation) >= 2:
    old = state["routing_biases"].get("validation_routing_bias", 0.6)
    new = round(min(0.9, old + 0.05), 2)
    state["routing_biases"]["validation_routing_bias"] = new
    adjustments.append({
        "area": "validation_routing_bias",
        "from": old,
        "to": new,
        "reason": "repeated validation benefits suggest slightly stronger validation-oriented routing bias"
    })

state["generated_at"] = datetime.utcnow().isoformat() + "Z"
state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

with improvement_log_path.open("a", encoding="utf-8") as f:
    for adj in adjustments:
        rec = {"timestamp": state["generated_at"], **adj}
        f.write(json.dumps(rec) + "\n")

print(json.dumps({
    "generated_at": state["generated_at"],
    "adjustments": adjustments,
    "orchestrator_state": state
}, indent=2))
