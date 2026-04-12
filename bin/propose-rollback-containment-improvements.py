#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

root = Path(__file__).resolve().parents[1]
state_path = root / "capabilities" / "rollback-containment-state.json"
log_path = root / "capabilities" / "rollback-containment-log.jsonl"
improvement_log_path = root / "capabilities" / "rollback-containment-improvement-log.jsonl"

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
broad_revert = [e for e in entries if e.get("quality_label") in ("full_revert_unnecessary", "broad_rollback")]
spread = [e for e in entries if e.get("quality_label") in ("blast_radius_too_wide", "failure_spread")]
unsafe_promotion = [e for e in entries if e.get("quality_label") == "unsafe_promotion"]
good_scoped = [e for e in entries if e.get("quality_label") == "scoped_rollback_helped"]

if len(broad_revert) >= 2:
    old = state["containment_biases"].get("scoped_rollback_bias", 0.8)
    new = round(min(0.98, old + 0.03), 2)
    state["containment_biases"]["scoped_rollback_bias"] = new
    adjustments.append({"area":"scoped_rollback_bias","from":old,"to":new,"reason":"repeated excessive-rollback outcomes suggest stronger preference for scoped revert"})

if len(spread) >= 2:
    old = state["containment_biases"].get("blast_radius_restraint_bias", 0.8)
    new = round(min(0.98, old + 0.03), 2)
    state["containment_biases"]["blast_radius_restraint_bias"] = new
    adjustments.append({"area":"blast_radius_restraint_bias","from":old,"to":new,"reason":"repeated spread outcomes suggest stronger containment before changes propagate"})

if len(unsafe_promotion) >= 2:
    old = state["containment_biases"].get("promotion_caution_bias", 0.65)
    new = round(min(0.95, old + 0.05), 2)
    state["containment_biases"]["promotion_caution_bias"] = new
    adjustments.append({"area":"promotion_caution_bias","from":old,"to":new,"reason":"repeated unsafe-promotion outcomes suggest stronger caution before broad promotion"})

if len(good_scoped) >= 2:
    old = state["containment_biases"].get("preserve_valid_work_bias", 0.85)
    new = round(min(0.98, old + 0.03), 2)
    state["containment_biases"]["preserve_valid_work_bias"] = new
    adjustments.append({"area":"preserve_valid_work_bias","from":old,"to":new,"reason":"repeated scoped-recovery gains suggest stronger preservation of valid work during recovery"})

state["generated_at"] = datetime.utcnow().isoformat() + "Z"
state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

with improvement_log_path.open("a", encoding="utf-8") as f:
    for adj in adjustments:
        rec = {"timestamp": state["generated_at"], **adj}
        f.write(json.dumps(rec) + "\n")

print(json.dumps({"generated_at": state["generated_at"], "adjustments": adjustments, "rollback_containment_state": state}, indent=2))
