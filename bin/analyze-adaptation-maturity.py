#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from datetime import datetime

root = Path(__file__).resolve().parents[1]
state_path = root / "capabilities" / "adaptation-maturity-state.json"

if len(sys.argv) < 4:
    print("usage: analyze-adaptation-maturity.py <adaptation_area> <maturity_label> <note> [extra...]")
    sys.exit(1)

entry = {
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "adaptation_area": sys.argv[1],
    "maturity_label": sys.argv[2],
    "note": sys.argv[3],
    "extra": " ".join(sys.argv[4:]).strip()
}

state = json.loads(state_path.read_text(encoding="utf-8"))
state["generated_at"] = entry["timestamp"]
state.setdefault("adaptations", {}).setdefault(entry["adaptation_area"], []).append(entry)
state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
print(json.dumps(entry, indent=2))
