#!/usr/bin/env python3
import json
from pathlib import Path
from collections import Counter

root = Path(__file__).resolve().parents[1]
log_path = root / "capabilities" / "memory-quality-log.jsonl"

counter = Counter()
entries = []
if log_path.exists():
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
            entries.append(e)
            counter[e.get("quality_label", "unknown")] += 1
        except Exception:
            pass

print("# Memory Learning Summary")
print()
print(f"Entries: {len(entries)}")
print()
if not counter:
    print("No memory-quality data recorded.")
else:
    for k, v in sorted(counter.items()):
        print(f"- {k}: {v}")
