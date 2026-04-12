#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

root = Path(__file__).resolve().parents[1]
state_path = root / "capabilities" / "mission-compiler-state.json"
log_path = root / "capabilities" / "contract-quality-log.jsonl"
improvement_log_path = root / "capabilities" / "compiler-improvement-log.jsonl"

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

poor = [e for e in entries if e.get("quality_label") in ("poor", "too_vague", "too_rigid", "missed_dependencies")]
adjustments = []

if len(poor) >= 2:
    old = state["compiler_biases"].get("constraint_extraction_strength", 0.6)
    new = round(min(0.9, old + 0.05), 2)
    state["compiler_biases"]["constraint_extraction_strength"] = new
    adjustments.append({
        "area": "constraint_extraction_strength",
        "from": old,
        "to": new,
        "reason": "multiple weak contract outcomes suggest stronger constraint extraction"
    })

if len(poor) >= 3:
    old = state["compiler_biases"].get("ambiguity_sensitivity", 0.6)
    new = round(min(0.9, old + 0.05), 2)
    state["compiler_biases"]["ambiguity_sensitivity"] = new
    adjustments.append({
        "area": "ambiguity_sensitivity",
        "from": old,
        "to": new,
        "reason": "repeated low-quality contracts suggest earlier ambiguity detection"
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
    "compiler_state": state
}, indent=2))
