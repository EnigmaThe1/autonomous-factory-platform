#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from datetime import datetime

root = Path(__file__).resolve().parents[1]
log_path = root / "capabilities" / "tool-use-log.jsonl"

if len(sys.argv) < 5:
    print("usage: analyze-tool-use.py <mission_archetype> <quality_label> <tool_combo> <note> [extra...]")
    sys.exit(1)

entry = {
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "mission_archetype": sys.argv[1],
    "quality_label": sys.argv[2],
    "tool_combo": sys.argv[3],
    "note": sys.argv[4],
    "extra": " ".join(sys.argv[5:]).strip()
}

with log_path.open("a", encoding="utf-8") as f:
    f.write(json.dumps(entry) + "\n")

print(json.dumps(entry, indent=2))
