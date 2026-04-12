#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

root = Path(__file__).resolve().parents[1]
state_path = root / "capabilities" / "operator-interaction-state.json"
log_path = root / "capabilities" / "operator-interaction-log.jsonl"
improvement_log_path = root / "capabilities" / "operator-interaction-improvement-log.jsonl"

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
full_restart = [e for e in entries if e.get("quality_label") in ("unnecessary_full_restart", "poor_salvage")]
vague_redirect = [e for e in entries if e.get("quality_label") in ("vague_redirect_handled_poorly", "operator_intent_misread")]
good_adapt = [e for e in entries if e.get("quality_label") == "adaptive_recovery_helped"]
too_many_clarifications = [e for e in entries if e.get("quality_label") == "over_clarified_redirect"]

if len(full_restart) >= 2:
    old = state["interaction_biases"].get("salvage_bias", 0.75)
    new = round(min(0.95, old + 0.05), 2)
    state["interaction_biases"]["salvage_bias"] = new
    adjustments.append({
        "area": "salvage_bias",
        "from": old,
        "to": new,
        "reason": "repeated restart-heavy outcomes suggest slightly stronger preference for salvaging valid work"
    })

if len(vague_redirect) >= 2:
    old = state["interaction_biases"].get("intent_interpretation_bias", 0.7)
    new = round(min(0.95, old + 0.05), 2)
    state["interaction_biases"]["intent_interpretation_bias"] = new
    adjustments.append({
        "area": "intent_interpretation_bias",
        "from": old,
        "to": new,
        "reason": "repeated weak redirect handling suggests slightly stronger operator-intent interpretation"
    })

if len(good_adapt) >= 2:
    old = state["interaction_biases"].get("adaptive_redirect_bias", 0.75)
    new = round(min(0.98, old + 0.03), 2)
    state["interaction_biases"]["adaptive_redirect_bias"] = new
    adjustments.append({
        "area": "adaptive_redirect_bias",
        "from": old,
        "to": new,
        "reason": "repeated adaptive-recovery gains suggest slightly stronger willingness to adapt instead of reset"
    })

if len(too_many_clarifications) >= 2:
    old = state["interaction_biases"].get("clarification_restraint_bias", 0.8)
    new = round(min(0.98, old + 0.03), 2)
    state["interaction_biases"]["clarification_restraint_bias"] = new
    adjustments.append({
        "area": "clarification_restraint_bias",
        "from": old,
        "to": new,
        "reason": "repeated over-clarification during redirects suggests slightly stronger restraint before asking follow-ups"
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
    "operator_interaction_state": state
}, indent=2))
