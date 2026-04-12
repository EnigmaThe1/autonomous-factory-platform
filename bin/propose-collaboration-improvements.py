#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

root = Path(__file__).resolve().parents[1]
state_path = root / "capabilities" / "collaboration-pattern-state.json"
log_path = root / "capabilities" / "collaboration-pattern-log.jsonl"
improvement_log_path = root / "capabilities" / "collaboration-pattern-improvement-log.jsonl"

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
unnecessary_fanout = [e for e in entries if e.get("quality_label") in ("unnecessary_fanout", "coordination_overhead")]
missing_specialist = [e for e in entries if e.get("quality_label") in ("missing_specialist", "solo_overstretched")]
pair_helped = [e for e in entries if e.get("quality_label") == "pair_collaboration_helped"]
bad_simultaneous = [e for e in entries if e.get("quality_label") in ("premature_simultaneous_collaboration", "team_started_too_early")]

if len(unnecessary_fanout) >= 2:
    old = state["collaboration_biases"].get("team_fanout_restraint_bias", 0.7)
    new = round(min(0.95, old + 0.05), 2)
    state["collaboration_biases"]["team_fanout_restraint_bias"] = new
    adjustments.append({"area": "team_fanout_restraint_bias", "from": old, "to": new, "reason": "repeated coordination-overhead outcomes suggest slightly stronger restraint before broad fan-out"})

if len(missing_specialist) >= 2:
    old = state["collaboration_biases"].get("specialist_activation_bias", 0.6)
    new = round(min(0.9, old + 0.05), 2)
    state["collaboration_biases"]["specialist_activation_bias"] = new
    adjustments.append({"area": "specialist_activation_bias", "from": old, "to": new, "reason": "repeated overstretched-solo outcomes suggest slightly stronger readiness to involve a specialist"})

if len(pair_helped) >= 2:
    old = state["collaboration_biases"].get("pair_collaboration_bias", 0.55)
    new = round(min(0.9, old + 0.05), 2)
    state["collaboration_biases"]["pair_collaboration_bias"] = new
    adjustments.append({"area": "pair_collaboration_bias", "from": old, "to": new, "reason": "repeated pair-collaboration gains suggest slightly stronger bias toward pair-style work where helpful"})

if len(bad_simultaneous) >= 2:
    old = state["collaboration_biases"].get("phased_collaboration_bias", 0.65)
    new = round(min(0.95, old + 0.05), 2)
    state["collaboration_biases"]["phased_collaboration_bias"] = new
    adjustments.append({"area": "phased_collaboration_bias", "from": old, "to": new, "reason": "repeated premature-simultaneous outcomes suggest slightly stronger preference for phased collaboration"})

state["generated_at"] = datetime.utcnow().isoformat() + "Z"
state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

with improvement_log_path.open("a", encoding="utf-8") as f:
    for adj in adjustments:
        rec = {"timestamp": state["generated_at"], **adj}
        f.write(json.dumps(rec) + "\n")

print(json.dumps({"generated_at": state["generated_at"], "adjustments": adjustments, "collaboration_pattern_state": state}, indent=2))
