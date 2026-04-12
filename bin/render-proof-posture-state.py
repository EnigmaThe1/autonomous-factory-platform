#!/usr/bin/env python3
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
state = json.loads((root / "capabilities" / "proof-posture-state.json").read_text(encoding="utf-8"))

print("# Proof Posture State")
print()
print(f"Generated: {state.get('generated_at')}")
print()
for k, v in state.get("posture_biases", {}).items():
    print(f"- {k}: {v}")
