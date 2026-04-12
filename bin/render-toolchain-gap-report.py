#!/usr/bin/env python3
import json
from pathlib import Path

p = Path(__file__).resolve().parent.parent / "capabilities" / "toolchain-gap-state.json"
if not p.exists():
    print("No toolchain gap state found.")
    raise SystemExit(0)
data = json.loads(p.read_text())
print("# Toolchain Gap Report
")
print(f"**Mission:** {data.get('mission')}
")
for key, label in [
    ("required_capabilities", "Required capabilities"),
    ("available_registry_entries", "Available registry entries"),
    ("registry_gaps", "Registry gaps"),
    ("recommended_expansion", "Recommended expansion"),
    ("deferred_optional", "Deferred optional"),
]:
    print(f"## {label}")
    vals = data.get(key) or []
    if vals:
        for v in vals:
            print(f"- {v}")
    else:
        print("- none")
    print()
