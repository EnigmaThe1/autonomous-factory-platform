#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

root = Path(__file__).resolve().parents[1]
state_path = root / "capabilities" / "execution-strategy-state.json"
log_path = root / "capabilities" / "execution-strategy-log.jsonl"
improvement_log_path = root / "capabilities" / "execution-strategy-improvement-log.jsonl"

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
too_much_planning = [e for e in entries if e.get("quality_label") in ("over_planned", "too_slow_to_start")]
too_little_planning = [e for e in entries if e.get("quality_label") in ("under_planned", "structure_missing")]
bad_parallel = [e for e in entries if e.get("quality_label") in ("premature_parallelism", "parallel_overhead")]
good_restrategy = [e for e in entries if e.get("quality_label") == "mid_mission_restrategy_helped"]

if len(too_much_planning) >= 2:
    old = state["strategy_biases"].get("iterative_execution_bias", 0.7)
    new = round(min(0.95, old + 0.05), 2)
    state["strategy_biases"]["iterative_execution_bias"] = new
    adjustments.append({
        "area": "iterative_execution_bias",
        "from": old,
        "to": new,
        "reason": "repeated over-planning outcomes suggest slightly stronger bias toward earlier iterative execution"
    })

if len(too_little_planning) >= 2:
    old = state["strategy_biases"].get("deep_design_bias", 0.55)
    new = round(min(0.9, old + 0.05), 2)
    state["strategy_biases"]["deep_design_bias"] = new
    adjustments.append({
        "area": "deep_design_bias",
        "from": old,
        "to": new,
        "reason": "repeated under-planning outcomes suggest slightly stronger bias toward deeper design when needed"
    })

if len(bad_parallel) >= 2:
    old = state["strategy_biases"].get("parallelism_restraint_bias", 0.65)
    new = round(min(0.95, old + 0.05), 2)
    state["strategy_biases"]["parallelism_restraint_bias"] = new
    adjustments.append({
        "area": "parallelism_restraint_bias",
        "from": old,
        "to": new,
        "reason": "repeated premature-parallelism outcomes suggest slightly stronger restraint before fan-out"
    })

if len(good_restrategy) >= 2:
    old = state["strategy_biases"].get("mid_mission_restrategy_bias", 0.75)
    new = round(min(0.98, old + 0.03), 2)
    state["strategy_biases"]["mid_mission_restrategy_bias"] = new
    adjustments.append({
        "area": "mid_mission_restrategy_bias",
        "from": old,
        "to": new,
        "reason": "repeated re-strategy benefits suggest slightly stronger willingness to adapt mid-mission"
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
    "execution_strategy_state": state
}, indent=2))
