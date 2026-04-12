#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

root = Path(__file__).resolve().parents[1]
learning_report_path = root / "capabilities" / "mission-learning-report.json"
heuristics_path = root / "capabilities" / "heuristic-state.json"

learning = json.loads(learning_report_path.read_text(encoding="utf-8"))
heuristics = json.loads(heuristics_path.read_text(encoding="utf-8"))

patterns = learning.get("patterns", [])
adjustments = []

counts = {}
for p in patterns:
    cap = p.get("capability")
    bias = p.get("recommended_bias")
    counts.setdefault((cap, bias), 0)
    counts[(cap, bias)] += 1

if sum(counts.values()) >= 3:
    current = heuristics["bias_strength"].get("earlier_suggestion", 0.4)
    heuristics["bias_strength"]["earlier_suggestion"] = round(min(0.8, current + 0.05), 2)
    adjustments.append({
        "area": "bias_strength.earlier_suggestion",
        "from": current,
        "to": heuristics["bias_strength"]["earlier_suggestion"],
        "reason": "repeated cross-mission patterns suggest slightly earlier soft suggestions are useful"
    })

if len(patterns) >= 5:
    current = heuristics["phase_sensitivity"].get("next_phase_match", 0.8)
    heuristics["phase_sensitivity"]["next_phase_match"] = round(min(1.0, current + 0.05), 2)
    adjustments.append({
        "area": "phase_sensitivity.next_phase_match",
        "from": current,
        "to": heuristics["phase_sensitivity"]["next_phase_match"],
        "reason": "larger mission sample supports slightly earlier preparation for likely next-phase needs"
    })

heuristics["generated_at"] = datetime.utcnow().isoformat() + "Z"
heuristics_path.write_text(json.dumps(heuristics, indent=2) + "\n", encoding="utf-8")
print(json.dumps({
    "generated_at": heuristics["generated_at"],
    "adjustments": adjustments,
    "heuristic_state": heuristics
}, indent=2))
