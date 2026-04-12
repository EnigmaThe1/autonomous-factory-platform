#!/usr/bin/env python3
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
state_path = root / "capabilities" / "phase-promotion-state.json"
state = json.loads(state_path.read_text(encoding="utf-8"))

print("# Phase Promotion State")
print()
print(f"Generated: {state.get('generated_at')}")
print(f"Current phase: {state.get('current_phase')}")
print(f"Next phase: {state.get('next_phase')}")
print()
caps = state.get("capabilities", {})
if not caps:
    print("No phase-aware decisions recorded.")
else:
    for name, info in sorted(caps.items()):
        print(f"- {name}: {info.get('decision')}")
        print(f"  reason: {info.get('reason')}")
