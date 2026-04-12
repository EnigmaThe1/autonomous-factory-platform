#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

root = Path(__file__).resolve().parents[1]
state_path = root / "capabilities" / "validation-layer-state.json"
log_path = root / "capabilities" / "validation-quality-log.jsonl"
improvement_log_path = root / "capabilities" / "validation-improvement-log.jsonl"

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
over_validated = [e for e in entries if e.get("quality_label") in ("over_validated", "redundant_checks")]
under_validated = [e for e in entries if e.get("quality_label") in ("under_validated", "insufficient_proof")]
good_signals = [e for e in entries if e.get("quality_label") == "confidence_signal_helped"]
wasted_effort = [e for e in entries if e.get("quality_label") == "wasted_validation_effort"]

if len(over_validated) >= 2 or len(wasted_effort) >= 2:
    old = state["validation_biases"].get("over_validation_avoidance_bias", 0.75)
    new = round(min(0.95, old + 0.05), 2)
    state["validation_biases"]["over_validation_avoidance_bias"] = new
    adjustments.append({
        "area": "over_validation_avoidance_bias",
        "from": old,
        "to": new,
        "reason": "repeated excessive-validation outcomes suggest slightly stronger proof-efficiency preference"
    })

if len(under_validated) >= 2:
    old = state["validation_biases"].get("under_validation_detection_bias", 0.7)
    new = round(min(0.95, old + 0.05), 2)
    state["validation_biases"]["under_validation_detection_bias"] = new
    adjustments.append({
        "area": "under_validation_detection_bias",
        "from": old,
        "to": new,
        "reason": "repeated weak-proof outcomes suggest slightly stronger under-validation detection"
    })

if len(good_signals) >= 2:
    old = state["validation_biases"].get("confidence_signal_bias", 0.7)
    new = round(min(0.95, old + 0.05), 2)
    state["validation_biases"]["confidence_signal_bias"] = new
    adjustments.append({
        "area": "confidence_signal_bias",
        "from": old,
        "to": new,
        "reason": "repeated confidence-signal gains suggest slightly stronger reliance on proven confidence indicators"
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
    "validation_layer_state": state
}, indent=2))
