#!/usr/bin/env python3
import json, sys
from pathlib import Path
from datetime import datetime

root = Path(__file__).resolve().parents[1]
log_path = root / "capabilities" / "proof-posture-log.jsonl"

if len(sys.argv) < 4:
    print("usage: analyze-proof-posture.py <area> <quality_label> <note> [extra...]")
    sys.exit(1)

entry = {
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "area": sys.argv[1],
    "quality_label": sys.argv[2],
    "note": sys.argv[3],
    "extra": " ".join(sys.argv[4:]).strip()
}

with log_path.open("a", encoding="utf-8") as f:
    f.write(json.dumps(entry) + "\n")

print(json.dumps(entry, indent=2))
