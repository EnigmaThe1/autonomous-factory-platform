#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

root = Path(__file__).resolve().parents[1]
state_path = root / "capabilities" / "policy-balance-state.json"
log_path = root / "capabilities" / "policy-quality-log.jsonl"
improvement_log_path = root / "capabilities" / "policy-improvement-log.jsonl"

state = json.loads(state_path.read_text(encoding="utf-8"))
entries = []
if log_path.exists():
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except Exception:
            pass

adjustments = []
too_cautious = [e for e in entries if e.get("quality_label") in ("too_cautious", "unhelpful_guidance_noise")]
too_weak = [e for e in entries if e.get("quality_label") in ("too_weak", "missed_preventable_mistake")]
host_clarity = [e for e in entries if e.get("quality_label") == "host_boundary_confusing"]

if len(too_cautious) >= 2:
    old = state["policy_biases"].get("trust_caution_bias", 0.5)
    new = round(max(0.2, old - 0.05), 2)
    state["policy_biases"]["trust_caution_bias"] = new
    adjustments.append({
        "area": "trust_caution_bias",
        "from": old,
        "to": new,
        "reason": "repeated over-cautious outcomes suggest slightly less caution in project-space soft guidance"
    })

if len(too_weak) >= 2:
    old = state["policy_biases"].get("soft_guidance_strength", 0.55)
    new = round(min(0.85, old + 0.05), 2)
    state["policy_biases"]["soft_guidance_strength"] = new
    adjustments.append({
        "area": "soft_guidance_strength",
        "from": old,
        "to": new,
        "reason": "repeated preventable misses suggest slightly stronger soft guidance recommendations"
    })

if len(host_clarity) >= 2:
    old = state["policy_biases"].get("host_boundary_clarity_bias", 0.75)
    new = round(min(0.95, old + 0.05), 2)
    state["policy_biases"]["host_boundary_clarity_bias"] = new
    adjustments.append({
        "area": "host_boundary_clarity_bias",
        "from": old,
        "to": new,
        "reason": "repeated host-boundary confusion suggests clearer host-safety signaling"
    })

state["generated_at"] = datetime.utcnow().isoformat() + "Z"
state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

with improvement_log_path.open("a", encoding="utf-8") as f:
    for adj in adjustments:
        rec = {"timestamp": state["generated_at"], **adj}
        f.write(json.dumps(rec) + "\n")

print(json.dumps({
    "generated_at": state["generated_at"],
    "adjustments": adjustments,
    "policy_balance_state": state
}, indent=2))
