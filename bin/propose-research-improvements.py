#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

root = Path(__file__).resolve().parents[1]
state_path = root / "capabilities" / "research-layer-state.json"
log_path = root / "capabilities" / "research-quality-log.jsonl"
improvement_log_path = root / "capabilities" / "research-improvement-log.jsonl"

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
stale = [e for e in entries if e.get("quality_label") in ("stale_sources", "freshness_too_weak")]
overbrowse = [e for e in entries if e.get("quality_label") in ("over_browsed", "too_broad_research")]
poor_handoff = [e for e in entries if e.get("quality_label") in ("weak_handoff", "research_not_actionable")]
good_auth = [e for e in entries if e.get("quality_label") == "authoritative_sources_helped"]

if len(stale) >= 2:
    old = state["research_biases"].get("freshness_sensitivity_bias", 0.65)
    new = round(min(0.95, old + 0.05), 2)
    state["research_biases"]["freshness_sensitivity_bias"] = new
    adjustments.append({
        "area": "freshness_sensitivity_bias",
        "from": old,
        "to": new,
        "reason": "repeated stale-source outcomes suggest slightly stronger freshness sensitivity"
    })

if len(overbrowse) >= 2:
    old = state["research_biases"].get("over_browsing_avoidance_bias", 0.8)
    new = round(min(0.98, old + 0.03), 2)
    state["research_biases"]["over_browsing_avoidance_bias"] = new
    adjustments.append({
        "area": "over_browsing_avoidance_bias",
        "from": old,
        "to": new,
        "reason": "repeated over-browsing outcomes suggest slightly stronger restraint on unnecessary research expansion"
    })

if len(poor_handoff) >= 2:
    old = state["research_biases"].get("research_handoff_bias", 0.75)
    new = round(min(0.95, old + 0.05), 2)
    state["research_biases"]["research_handoff_bias"] = new
    adjustments.append({
        "area": "research_handoff_bias",
        "from": old,
        "to": new,
        "reason": "repeated weak-handoff outcomes suggest stronger research-to-action handoff emphasis"
    })

if len(good_auth) >= 2:
    old = state["research_biases"].get("authoritative_source_bias", 0.8)
    new = round(min(0.98, old + 0.03), 2)
    state["research_biases"]["authoritative_source_bias"] = new
    adjustments.append({
        "area": "authoritative_source_bias",
        "from": old,
        "to": new,
        "reason": "repeated authoritative-source gains suggest slightly stronger preference for high-trust sources"
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
    "research_layer_state": state
}, indent=2))
