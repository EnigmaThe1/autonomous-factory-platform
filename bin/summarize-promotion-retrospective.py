#!/usr/bin/env python3
import json
from pathlib import Path
from collections import Counter

root = Path(__file__).resolve().parents[1]
state_path = root / "capabilities" / "live-feedback-state.json"
state = json.loads(state_path.read_text(encoding="utf-8"))

counter = Counter()
for entry in state.get("signals", []):
    counter[(entry.get("capability"), entry.get("direction"))] += 1

print("# Promotion Retrospective Summary")
print()
if not counter:
    print("No retrospective signals recorded.")
else:
    for (cap, direction), count in sorted(counter.items()):
        print(f"- {cap}: {direction} x{count}")
