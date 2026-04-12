#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

root = Path(__file__).resolve().parents[1]
state_path = root / "capabilities" / "adaptation-governance-state.json"
maturity_path = root / "capabilities" / "adaptation-maturity-state.json"
log_path = root / "capabilities" / "governance-improvement-log.jsonl"

state = json.loads(state_path.read_text(encoding="utf-8"))
maturity = json.loads(maturity_path.read_text(encoding="utf-8"))

labels = []
for _, entries in maturity.get("adaptations", {}).items():
    for e in entries:
        labels.append(e.get("maturity_label"))

adjustments = []
tentative_count = sum(1 for x in labels if x == "tentative")
rollback_count = sum(1 for x in labels if x == "rollback")
established_count = sum(1 for x in labels if x == "established_soft_default")
dampen_count = sum(1 for x in labels if x == "dampen")

if rollback_count >= 2 or dampen_count >= 2:
    old = state["governance_biases"].get("overreaction_damping_bias", 0.7)
    new = round(min(0.95, old + 0.05), 2)
    state["governance_biases"]["overreaction_damping_bias"] = new
    adjustments.append({
        "area": "overreaction_damping_bias",
        "from": old,
        "to": new,
        "reason": "multiple rollback/dampen outcomes suggest stronger anti-overreaction damping"
    })

if tentative_count >= 3 and established_count == 0:
    old = state["governance_biases"].get("tentative_retention_bias", 0.75)
    new = round(min(0.95, old + 0.05), 2)
    state["governance_biases"]["tentative_retention_bias"] = new
    adjustments.append({
        "area": "tentative_retention_bias",
        "from": old,
        "to": new,
        "reason": "many tentative outcomes suggest maintaining cautious maturity progression"
    })

if established_count >= 3:
    old = state["governance_biases"].get("soft_default_promotion_threshold", 0.7)
    new = round(max(0.45, old - 0.03), 2)
    state["governance_biases"]["soft_default_promotion_threshold"] = new
    adjustments.append({
        "area": "soft_default_promotion_threshold",
        "from": old,
        "to": new,
        "reason": "multiple established outcomes suggest strong patterns can graduate slightly sooner"
    })

state["generated_at"] = datetime.utcnow().isoformat() + "Z"
state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

with log_path.open("a", encoding="utf-8") as f:
    for adj in adjustments:
        rec = {"timestamp": state["generated_at"], **adj}
        f.write(json.dumps(rec) + "\n")

print(json.dumps({
    "generated_at": state["generated_at"],
    "adjustments": adjustments,
    "governance_state": state
}, indent=2))
