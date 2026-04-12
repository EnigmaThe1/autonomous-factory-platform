#!/usr/bin/env python3
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
heuristics_path = root / "capabilities" / "heuristic-state.json"
drift_path = root / "capabilities" / "drift-state.json"

heuristics = json.loads(heuristics_path.read_text(encoding="utf-8"))
drift = json.loads(drift_path.read_text(encoding="utf-8"))

print("# Heuristic State")
print()
print(f"Generated: {heuristics.get('generated_at')}")
print()
print("## Weights")
for k, v in heuristics.get("weights", {}).items():
    print(f"- {k}: {v}")
print()
print("## Phase sensitivity")
for k, v in heuristics.get("phase_sensitivity", {}).items():
    print(f"- {k}: {v}")
print()
print("## Bias strength")
for k, v in heuristics.get("bias_strength", {}).items():
    print(f"- {k}: {v}")
print()
print(f"## Drift status: {drift.get('status')}")
for s in drift.get("signals", []):
    print(f"- {s}")
