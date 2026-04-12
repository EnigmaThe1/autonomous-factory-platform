#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from datetime import datetime

root = Path(__file__).resolve().parents[1]
phase_map_path = root / "capabilities" / "phase-capability-map.json"
state_path = root / "capabilities" / "phase-promotion-state.json"

phase_map = json.loads(phase_map_path.read_text(encoding="utf-8"))
state = json.loads(state_path.read_text(encoding="utf-8"))

if len(sys.argv) < 2:
    print("usage: decide-phase-promotion.py <current_phase> [next_phase]")
    sys.exit(1)

current_phase = sys.argv[1].strip()
next_phase = sys.argv[2].strip() if len(sys.argv) > 2 else ""

results = {}
for capability, phases in phase_map.get("maps", {}).items():
    if current_phase in phases:
        decision = "staged_for_activation"
        reason = "capability matches the current phase"
    elif next_phase and next_phase in phases:
        decision = "staged_for_activation"
        reason = "capability matches the next likely phase and is worth preparing"
    else:
        decision = "suggested"
        reason = "capability does not match the current or next phase strongly enough"
    results[capability] = {
        "decision": decision,
        "reason": reason,
        "current_phase": current_phase,
        "next_phase": next_phase,
        "evaluated_at": datetime.utcnow().isoformat() + "Z"
    }

state["generated_at"] = datetime.utcnow().isoformat() + "Z"
state["current_phase"] = current_phase
state["next_phase"] = next_phase or None
state["capabilities"] = results
state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
print(json.dumps(results, indent=2))
