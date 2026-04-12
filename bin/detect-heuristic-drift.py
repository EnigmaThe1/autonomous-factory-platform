#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

root = Path(__file__).resolve().parents[1]
drift_path = root / "capabilities" / "drift-state.json"
feedback_path = root / "capabilities" / "live-feedback-state.json"
learning_path = root / "capabilities" / "mission-learning-report.json"

feedback = json.loads(feedback_path.read_text(encoding="utf-8"))
learning = json.loads(learning_path.read_text(encoding="utf-8"))

promote_count = 0
demote_count = 0
for entry in feedback.get("signals", []):
    if entry.get("direction") == "promote":
        promote_count += 1
    elif entry.get("direction") in ("demote", "retire"):
        demote_count += 1

status = "clear"
signals = []
if demote_count > promote_count and demote_count >= 3:
    status = "watch"
    signals.append("recent execution feedback shows more demotion/retirement than promotion")
if len(learning.get("patterns", [])) == 0:
    signals.append("insufficient cross-mission evidence for confident tuning")

drift_state = {
    "version": "v20",
    "generated_at": datetime.utcnow().isoformat() + "Z",
    "signals": signals,
    "status": status
}
drift_path.write_text(json.dumps(drift_state, indent=2) + "\n", encoding="utf-8")
print(json.dumps(drift_state, indent=2))
