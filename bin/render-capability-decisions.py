#!/usr/bin/env python3
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / "capabilities" / "capability-decision-state.json"
data = json.loads(path.read_text(encoding="utf-8"))

print("# Capability Decision State")
print()
print(f"Generated: {data.get('generated_at')}")
print()
caps = data.get("capabilities", {})
if not caps:
    print("No capability decisions recorded.")
else:
    for name, info in sorted(caps.items()):
        print(f"- {name}: {info.get('decision')} (score={info.get('score')})")
        print(f"  reason: {info.get('reason')}")
