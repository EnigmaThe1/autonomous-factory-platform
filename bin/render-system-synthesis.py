#!/usr/bin/env python3
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
state = json.loads((root / "capabilities" / "system-synthesis-state.json").read_text(encoding="utf-8"))
conf = json.loads((root / "capabilities" / "cross-layer-conflicts.json").read_text(encoding="utf-8"))

print("# System Synthesis State")
print()
print(f"Generated: {state.get('generated_at')}")
print()
print("## Shared biases")
for k, v in state.get("shared_biases", {}).items():
    print(f"- {k}: {v}")
print()
print("## Cross-layer notes")
for note in state.get("cross_layer_notes", []):
    print(f"- {note}")
if not state.get("cross_layer_notes"):
    print("- none")
print()
print("## Conflicts")
for item in conf.get("conflicts", []):
    print(f"- {item}")
if not conf.get("conflicts"):
    print("- none")
print()
print("## Duplications")
for item in conf.get("duplications", []):
    print(f"- {item}")
if not conf.get("duplications"):
    print("- none")
