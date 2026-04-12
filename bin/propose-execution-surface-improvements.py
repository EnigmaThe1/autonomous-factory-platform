#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

root = Path(__file__).resolve().parents[1]
state_path = root / "capabilities" / "execution-surface-state.json"
log_path = root / "capabilities" / "execution-surface-log.jsonl"
improvement_log_path = root / "capabilities" / "execution-surface-improvement-log.jsonl"

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
too_noisy = [e for e in entries if e.get("quality_label") in ("too_noisy", "redundant_signal")]
missing_state = [e for e in entries if e.get("quality_label") in ("missing_state_visibility", "unclear_progress")]
hidden_controls = [e for e in entries if e.get("quality_label") == "control_too_hidden"]

if len(too_noisy) >= 2:
    old = state["surface_biases"].get("signal_density_bias", 0.45)
    new = round(max(0.2, old - 0.05), 2)
    state["surface_biases"]["signal_density_bias"] = new
    adjustments.append({
        "area": "signal_density_bias",
        "from": old,
        "to": new,
        "reason": "repeated noise outcomes suggest slightly lower signal density"
    })

if len(missing_state) >= 2:
    old = state["surface_biases"].get("state_visibility_bias", 0.7)
    new = round(min(0.95, old + 0.05), 2)
    state["surface_biases"]["state_visibility_bias"] = new
    adjustments.append({
        "area": "state_visibility_bias",
        "from": old,
        "to": new,
        "reason": "repeated visibility gaps suggest slightly stronger emphasis on high-value state visibility"
    })

if len(hidden_controls) >= 2:
    old = state["surface_biases"].get("operator_control_visibility_bias", 0.55)
    new = round(min(0.85, old + 0.05), 2)
    state["surface_biases"]["operator_control_visibility_bias"] = new
    adjustments.append({
        "area": "operator_control_visibility_bias",
        "from": old,
        "to": new,
        "reason": "repeated hidden-control outcomes suggest slightly clearer operator control visibility"
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
    "execution_surface_state": state
}, indent=2))
