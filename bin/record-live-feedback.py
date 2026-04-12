#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from datetime import datetime

root = Path(__file__).resolve().parents[1]
state_path = root / "capabilities" / "live-feedback-state.json"
state = json.loads(state_path.read_text(encoding="utf-8"))

if len(sys.argv) < 4:
    print("usage: record-live-feedback.py <capability> <signal_type> <direction> [note...]")
    sys.exit(1)

capability = sys.argv[1]
signal_type = sys.argv[2]
direction = sys.argv[3]
note = " ".join(sys.argv[4:]).strip()

entry = {
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "capability": capability,
    "signal_type": signal_type,
    "direction": direction,
    "note": note
}

state["generated_at"] = entry["timestamp"]
state.setdefault("signals", []).append(entry)
state.setdefault("capabilities", {}).setdefault(capability, []).append(entry)
state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
print(json.dumps(entry, indent=2))
