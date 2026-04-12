#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from datetime import datetime

root = Path(__file__).resolve().parents[1]
history_path = root / "capabilities" / "mission-history.jsonl"

if len(sys.argv) < 4:
    print("usage: record-mission-outcome.py <mission_text> <archetype> <outcome> [capability1,capability2,...]")
    sys.exit(1)

mission_text = sys.argv[1]
archetype = sys.argv[2]
outcome = sys.argv[3]
capabilities = []
if len(sys.argv) > 4 and sys.argv[4].strip():
    capabilities = [c.strip() for c in sys.argv[4].split(",") if c.strip()]

record = {
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "mission_text": mission_text,
    "archetype": archetype,
    "outcome": outcome,
    "capabilities": capabilities
}

with history_path.open("a", encoding="utf-8") as f:
    f.write(json.dumps(record) + "\n")

print(json.dumps(record, indent=2))
