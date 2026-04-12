#!/usr/bin/env python3
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
state_path = root / "capabilities" / "adaptation-governance-state.json"
maturity_path = root / "capabilities" / "adaptation-maturity-state.json"

state = json.loads(state_path.read_text(encoding="utf-8"))
maturity = json.loads(maturity_path.read_text(encoding="utf-8"))

print("# Self-Improvement Governance State")
print()
print(f"Generated: {state.get('generated_at')}")
print()
print("## Governance biases")
for k, v in state.get("governance_biases", {}).items():
    print(f"- {k}: {v}")
print()
print("## Adaptation areas tracked")
for k, v in maturity.get("adaptations", {}).items():
    print(f"- {k}: {len(v)} observations")
if not maturity.get("adaptations"):
    print("- none")
