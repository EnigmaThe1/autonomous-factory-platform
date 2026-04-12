#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

root = Path(__file__).resolve().parents[1]
state_path = root / "capabilities" / "resource-intelligence-state.json"
log_path = root / "capabilities" / "resource-intelligence-log.jsonl"
improvement_log_path = root / "capabilities" / "resource-intelligence-improvement-log.jsonl"

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
over_explore = [e for e in entries if e.get("quality_label") in ("over_explored", "wasted_effort")]
stopped_too_early = [e for e in entries if e.get("quality_label") in ("stopped_too_early", "insufficient_depth")]
good_enough_helped = [e for e in entries if e.get("quality_label") == "good_enough_helped"]
bad_diminishing = [e for e in entries if e.get("quality_label") == "missed_diminishing_returns"]

if len(over_explore) >= 2:
    old = state["resource_biases"].get("waste_avoidance_bias", 0.8)
    new = round(min(0.98, old + 0.03), 2)
    state["resource_biases"]["waste_avoidance_bias"] = new
    adjustments.append({"area":"waste_avoidance_bias","from":old,"to":new,"reason":"repeated wasted-effort outcomes suggest stronger avoidance of low-yield extra work"})

if len(stopped_too_early) >= 2:
    old = state["resource_biases"].get("extra_depth_when_warranted_bias", 0.65)
    new = round(min(0.9, old + 0.05), 2)
    state["resource_biases"]["extra_depth_when_warranted_bias"] = new
    adjustments.append({"area":"extra_depth_when_warranted_bias","from":old,"to":new,"reason":"repeated shallow-stop outcomes suggest stronger willingness to spend extra effort when clearly warranted"})

if len(good_enough_helped) >= 2:
    old = state["resource_biases"].get("good_enough_bias", 0.7)
    new = round(min(0.95, old + 0.05), 2)
    state["resource_biases"]["good_enough_bias"] = new
    adjustments.append({"area":"good_enough_bias","from":old,"to":new,"reason":"repeated efficient-enough outcomes suggest slightly stronger good-enough commitment when quality is sufficient"})

if len(bad_diminishing) >= 2:
    old = state["resource_biases"].get("diminishing_returns_bias", 0.8)
    new = round(min(0.98, old + 0.03), 2)
    state["resource_biases"]["diminishing_returns_bias"] = new
    adjustments.append({"area":"diminishing_returns_bias","from":old,"to":new,"reason":"repeated missed-diminishing-returns outcomes suggest stronger detection of low-payoff continued effort"})

state["generated_at"] = datetime.utcnow().isoformat() + "Z"
state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

with improvement_log_path.open("a", encoding="utf-8") as f:
    for adj in adjustments:
        rec = {"timestamp": state["generated_at"], **adj}
        f.write(json.dumps(rec) + "\n")

print(json.dumps({"generated_at": state["generated_at"], "adjustments": adjustments, "resource_intelligence_state": state}, indent=2))
