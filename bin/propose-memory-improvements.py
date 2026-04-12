#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

root = Path(__file__).resolve().parents[1]
state_path = root / "capabilities" / "memory-layer-state.json"
log_path = root / "capabilities" / "memory-quality-log.jsonl"
improvement_log_path = root / "capabilities" / "memory-improvement-log.jsonl"

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
too_verbose = [e for e in entries if e.get("quality_label") in ("too_verbose", "low_value_retention")]
missing_recall = [e for e in entries if e.get("quality_label") in ("missing_recall", "useful_fact_not_retained")]
stale_memory = [e for e in entries if e.get("quality_label") == "stale_memory"]
poor_surfacing = [e for e in entries if e.get("quality_label") == "poor_memory_surfacing"]

if len(too_verbose) >= 2:
    old = state["memory_biases"].get("summary_compression_bias", 0.7)
    new = round(min(0.95, old + 0.05), 2)
    state["memory_biases"]["summary_compression_bias"] = new
    adjustments.append({
        "area": "summary_compression_bias",
        "from": old,
        "to": new,
        "reason": "repeated verbose-memory outcomes suggest slightly stronger compression"
    })

if len(missing_recall) >= 2:
    old = state["memory_biases"].get("cross_mission_reuse_bias", 0.75)
    new = round(min(0.95, old + 0.05), 2)
    state["memory_biases"]["cross_mission_reuse_bias"] = new
    adjustments.append({
        "area": "cross_mission_reuse_bias",
        "from": old,
        "to": new,
        "reason": "repeated missing-recall outcomes suggest slightly stronger retention of reusable cross-mission facts"
    })

if len(stale_memory) >= 2:
    old = state["memory_biases"].get("forget_stale_bias", 0.65)
    new = round(min(0.95, old + 0.05), 2)
    state["memory_biases"]["forget_stale_bias"] = new
    adjustments.append({
        "area": "forget_stale_bias",
        "from": old,
        "to": new,
        "reason": "repeated stale-memory outcomes suggest slightly stronger forgetting of old low-value detail"
    })

if len(poor_surfacing) >= 2:
    old = state["memory_biases"].get("surfacing_relevance_bias", 0.7)
    new = round(min(0.95, old + 0.05), 2)
    state["memory_biases"]["surfacing_relevance_bias"] = new
    adjustments.append({
        "area": "surfacing_relevance_bias",
        "from": old,
        "to": new,
        "reason": "repeated surfacing problems suggest slightly stronger relevance filtering for surfaced memory"
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
    "memory_layer_state": state
}, indent=2))
