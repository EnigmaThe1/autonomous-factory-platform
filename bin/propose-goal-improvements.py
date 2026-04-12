#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

root = Path(__file__).resolve().parents[1]
state_path = root / "capabilities" / "goal-formation-state.json"
log_path = root / "capabilities" / "goal-quality-log.jsonl"
improvement_log_path = root / "capabilities" / "goal-improvement-log.jsonl"

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
too_vague = [e for e in entries if e.get("quality_label") in ("too_vague", "weak_intent_shaping")]
over_narrow = [e for e in entries if e.get("quality_label") == "over_narrowed"]
bad_clarify = [e for e in entries if e.get("quality_label") == "too_many_clarifications"]

if len(too_vague) >= 2:
    old = state["goal_biases"].get("intent_sharpening_bias", 0.7)
    new = round(min(0.95, old + 0.05), 2)
    state["goal_biases"]["intent_sharpening_bias"] = new
    adjustments.append({
        "area": "intent_sharpening_bias",
        "from": old,
        "to": new,
        "reason": "repeated weak goal-shaping outcomes suggest slightly stronger early intent sharpening"
    })

if len(over_narrow) >= 2:
    old = state["goal_biases"].get("over_narrowing_avoidance_bias", 0.85)
    new = round(min(0.98, old + 0.03), 2)
    state["goal_biases"]["over_narrowing_avoidance_bias"] = new
    adjustments.append({
        "area": "over_narrowing_avoidance_bias",
        "from": old,
        "to": new,
        "reason": "repeated over-narrowing outcomes suggest stronger protection against collapsing solution space too early"
    })

if len(bad_clarify) >= 2:
    old = state["goal_biases"].get("clarification_restraint_bias", 0.8)
    new = round(min(0.98, old + 0.03), 2)
    state["goal_biases"]["clarification_restraint_bias"] = new
    adjustments.append({
        "area": "clarification_restraint_bias",
        "from": old,
        "to": new,
        "reason": "repeated over-clarification outcomes suggest slightly stronger restraint before asking questions"
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
    "goal_formation_state": state
}, indent=2))
