#!/usr/bin/env python3
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
state_path = root / "capabilities" / "collaboration-pattern-state.json"
state = json.loads(state_path.read_text(encoding="utf-8"))

print("# Collaboration Pattern State")
print()
print(f"Generated: {state.get('generated_at')}")
print()
for k, v in state.get("collaboration_biases", {}).items():
    print(f"- {k}: {v}")
