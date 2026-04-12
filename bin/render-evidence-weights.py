#!/usr/bin/env python3
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / "capabilities" / "evidence-weight-state.json"
state = json.loads(path.read_text(encoding="utf-8"))

print("# Evidence Weight State")
print()
print(f"Generated: {state.get('generated_at')}")
print()
caps = state.get("capabilities", {})
if not caps:
    print("No evidence-weighted decisions recorded.")
else:
    for name, info in sorted(caps.items()):
        print(f"- {name}: {info.get('weighted_decision')} [{info.get('evidence_strength')}] score={info.get('score')}")
