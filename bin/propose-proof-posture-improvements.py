#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

root = Path(__file__).resolve().parents[1]
state_path = root / "capabilities" / "proof-posture-state.json"
log_path = root / "capabilities" / "proof-posture-log.jsonl"
improvement_log_path = root / "capabilities" / "proof-posture-improvement-log.jsonl"

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
overclaim = [e for e in entries if e.get("quality_label") in ("overclaim", "inference_presented_as_fact")]
hidden_assumptions = [e for e in entries if e.get("quality_label") in ("hidden_assumption", "assumption_not_surface")]
bad_unknown = [e for e in entries if e.get("quality_label") in ("important_unknown_hidden", "uncertainty_not_surfaced")]
blocked_too_hard = [e for e in entries if e.get("quality_label") == "uncertainty_overblocked"]

if len(overclaim) >= 2:
    old = state["posture_biases"].get("overclaim_avoidance_bias", 0.85)
    new = round(min(0.98, old + 0.03), 2)
    state["posture_biases"]["overclaim_avoidance_bias"] = new
    adjustments.append({"area":"overclaim_avoidance_bias","from":old,"to":new,"reason":"repeated overclaim outcomes suggest stronger restraint against representing uncertain claims as proven"})

if len(hidden_assumptions) >= 2:
    old = state["posture_biases"].get("assumption_visibility_bias", 0.8)
    new = round(min(0.98, old + 0.03), 2)
    state["posture_biases"]["assumption_visibility_bias"] = new
    adjustments.append({"area":"assumption_visibility_bias","from":old,"to":new,"reason":"repeated hidden-assumption outcomes suggest stronger assumption surfacing"})

if len(bad_unknown) >= 2:
    old = state["posture_biases"].get("unknown_surfacing_bias", 0.75)
    new = round(min(0.95, old + 0.05), 2)
    state["posture_biases"]["unknown_surfacing_bias"] = new
    adjustments.append({"area":"unknown_surfacing_bias","from":old,"to":new,"reason":"repeated missing-uncertainty outcomes suggest stronger surfacing of important unknowns"})

if len(blocked_too_hard) >= 2:
    old = state["posture_biases"].get("acceptable_uncertainty_bias", 0.65)
    new = round(min(0.9, old + 0.05), 2)
    state["posture_biases"]["acceptable_uncertainty_bias"] = new
    adjustments.append({"area":"acceptable_uncertainty_bias","from":old,"to":new,"reason":"repeated overblocking suggests slightly better tolerance for acceptable uncertainty"})

state["generated_at"] = datetime.utcnow().isoformat() + "Z"
state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

with improvement_log_path.open("a", encoding="utf-8") as f:
    for adj in adjustments:
        rec = {"timestamp": state["generated_at"], **adj}
        f.write(json.dumps(rec) + "\n")

print(json.dumps({"generated_at": state["generated_at"], "adjustments": adjustments, "proof_posture_state": state}, indent=2))
