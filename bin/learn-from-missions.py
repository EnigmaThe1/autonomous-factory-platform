#!/usr/bin/env python3
import json
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

root = Path(__file__).resolve().parents[1]
history_path = root / "capabilities" / "mission-history.jsonl"
bias_path = root / "capabilities" / "learning-bias-state.json"
report_path = root / "capabilities" / "mission-learning-report.json"

archetype_cap_counter = defaultdict(Counter)
archetype_outcome_counter = defaultdict(Counter)
records = []

if history_path.exists():
    for line in history_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            records.append(rec)
        except Exception:
            continue

for rec in records:
    arch = rec.get("archetype", "unknown")
    outcome = rec.get("outcome", "unknown")
    archetype_outcome_counter[arch][outcome] += 1
    for cap in rec.get("capabilities", []):
        archetype_cap_counter[arch][cap] += 1

bias_state = {
    "version": "v19",
    "generated_at": datetime.utcnow().isoformat() + "Z",
    "archetype_biases": {},
    "capability_biases": {}
}
patterns = []

for arch, caps in archetype_cap_counter.items():
    top_caps = caps.most_common()
    if not top_caps:
        continue
    recommended = []
    for cap, count in top_caps:
        if count >= 2:
            recommended.append({
                "capability": cap,
                "bias": "earlier_suggestion" if count < 4 else "stronger_staging_bias",
                "count": count
            })
            patterns.append({
                "archetype": arch,
                "capability": cap,
                "count": count,
                "recommended_bias": "earlier_suggestion" if count < 4 else "stronger_staging_bias"
            })
    if recommended:
        bias_state["archetype_biases"][arch] = recommended

report = {
    "version": "v19",
    "generated_at": datetime.utcnow().isoformat() + "Z",
    "patterns": patterns,
    "missions_analyzed": len(records)
}

bias_path.write_text(json.dumps(bias_state, indent=2) + "\n", encoding="utf-8")
report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
