#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from datetime import datetime

root = Path(__file__).resolve().parents[1]
log_path = root / "capabilities" / "heuristic-adjustment-log.jsonl"

if len(sys.argv) < 4:
    print("usage: record-heuristic-adjustment.py <area> <old_value> <new_value> [reason...]")
    sys.exit(1)

entry = {
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "area": sys.argv[1],
    "old_value": sys.argv[2],
    "new_value": sys.argv[3],
    "reason": " ".join(sys.argv[4:]).strip()
}
with log_path.open("a", encoding="utf-8") as f:
    f.write(json.dumps(entry) + "\n")
print(json.dumps(entry, indent=2))
