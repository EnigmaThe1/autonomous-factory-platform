#!/usr/bin/env python3
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
bias_path = root / "capabilities" / "learning-bias-state.json"
report_path = root / "capabilities" / "mission-learning-report.json"

bias = json.loads(bias_path.read_text(encoding="utf-8"))
report = json.loads(report_path.read_text(encoding="utf-8"))

print("# Cross-Mission Learning Biases")
print()
print(f"Generated: {bias.get('generated_at')}")
print(f"Missions analyzed: {report.get('missions_analyzed')}")
print()
archetype_biases = bias.get("archetype_biases", {})
if not archetype_biases:
    print("No learned biases yet.")
else:
    for arch, items in sorted(archetype_biases.items()):
        print(f"## {arch}")
        for item in items:
            print(f"- {item.get('capability')}: {item.get('bias')} (count={item.get('count')})")
        print()
