#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from datetime import datetime

root = Path(__file__).resolve().parents[1]
state_path = root / "capabilities" / "mission-compiler-state.json"
log_path = root / "capabilities" / "contract-quality-log.jsonl"

if len(sys.argv) < 3:
    print("usage: analyze-contract-quality.py <raw_mission> <quality_label> [note...]")
    sys.exit(1)

raw_mission = sys.argv[1]
quality_label = sys.argv[2]
note = " ".join(sys.argv[3:]).strip()

entry = {
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "raw_mission": raw_mission,
    "quality_label": quality_label,
    "note": note
}

with log_path.open("a", encoding="utf-8") as f:
    f.write(json.dumps(entry) + "\n")

print(json.dumps(entry, indent=2))
