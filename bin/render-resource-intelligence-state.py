#!/usr/bin/env python3
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
state = json.loads((root / "capabilities" / "resource-intelligence-state.json").read_text(encoding="utf-8"))

print("# Resource Intelligence State")
print()
print(f"Generated: {state.get('generated_at')}")
print()
for k, v in state.get("resource_biases", {}).items():
    print(f"- {k}: {v}")
