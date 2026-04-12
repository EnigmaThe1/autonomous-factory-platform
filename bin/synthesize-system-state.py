#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

root = Path(__file__).resolve().parents[1]

compiler = json.loads((root / "capabilities" / "mission-compiler-state.json").read_text(encoding="utf-8"))
orch = json.loads((root / "capabilities" / "orchestrator-state.json").read_text(encoding="utf-8"))
tools = json.loads((root / "capabilities" / "tool-use-state.json").read_text(encoding="utf-8"))
policy = json.loads((root / "capabilities" / "policy-balance-state.json").read_text(encoding="utf-8"))
heuristics = json.loads((root / "capabilities" / "heuristic-state.json").read_text(encoding="utf-8"))

state_path = root / "capabilities" / "system-synthesis-state.json"
state = json.loads(state_path.read_text(encoding="utf-8"))

# Light synthesis, not hard override
state["shared_biases"]["autonomy_preservation_bias"] = round(
    max(
        state["shared_biases"].get("autonomy_preservation_bias", 0.9),
        policy.get("policy_biases", {}).get("autonomy_preservation_bias", 0.9)
    ), 2
)
state["shared_biases"]["lightweight_first_bias"] = round(
    tools.get("tool_biases", {}).get("prefer_lightweight_builtin_tools_first", 0.65), 2
)
state["shared_biases"]["specialist_escalation_sensitivity"] = round(
    orch.get("routing_biases", {}).get("specialist_escalation_sensitivity", 0.6), 2
)
state["shared_biases"]["soft_guidance_strength"] = round(
    policy.get("policy_biases", {}).get("soft_guidance_strength", 0.55), 2
)
# derive a soft evidence aggregate
weights = heuristics.get("weights", {})
if weights:
    avg = sum(weights.values()) / len(weights)
    state["shared_biases"]["evidence_weight_strength"] = round(min(1.0, avg / 5), 2)

notes = []
if state["shared_biases"]["soft_guidance_strength"] > 0.75 and state["shared_biases"]["autonomy_preservation_bias"] > 0.85:
    notes.append("guidance is strengthening while autonomy remains prioritized")
if state["shared_biases"]["lightweight_first_bias"] > 0.75:
    notes.append("system is trending toward lighter-weight tool choices by default")
if state["shared_biases"]["specialist_escalation_sensitivity"] > 0.7:
    notes.append("system is becoming more willing to route to specialists earlier")
if compiler.get("compiler_biases", {}).get("ambiguity_sensitivity", 0.6) > 0.7:
    notes.append("mission compiler is becoming more sensitive to ambiguity before execution")

state["generated_at"] = datetime.utcnow().isoformat() + "Z"
state["cross_layer_notes"] = notes
state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

print(json.dumps(state, indent=2))
