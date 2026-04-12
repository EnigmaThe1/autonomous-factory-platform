#!/usr/bin/env python3
import json
from pathlib import Path

p = Path(__file__).resolve().parent.parent / "capabilities" / "toolchain-gap-state.json"
if not p.exists():
    print(json.dumps({"error": "run analyze-toolchain-gaps.py first"}, indent=2))
    raise SystemExit(1)
data = json.loads(p.read_text())
plan = {
    "mission": data.get("mission"),
    "immediate": data.get("recommended_expansion", [])[:2],
    "triggered": data.get("registry_gaps", []),
    "deferred": data.get("deferred_optional", []),
    "principle": "Expand only as much as the mission requires."
}
print(json.dumps(plan, indent=2))
