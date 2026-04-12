#!/usr/bin/env python3
import json
from pathlib import Path
from collections import Counter

root = Path(__file__).resolve().parents[1]
maturity_path = root / "capabilities" / "adaptation-maturity-state.json"
maturity = json.loads(maturity_path.read_text(encoding="utf-8"))

counter = Counter()
count = 0
for _, entries in maturity.get("adaptations", {}).items():
    for e in entries:
        counter[e.get("maturity_label", "unknown")] += 1
        count += 1

print("# Governance Learning Summary")
print()
print(f"Entries: {count}")
print()
if not counter:
    print("No adaptation-maturity data recorded.")
else:
    for k, v in sorted(counter.items()):
        print(f"- {k}: {v}")
