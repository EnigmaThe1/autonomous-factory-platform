#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

root = Path(__file__).resolve().parents[1]

policy = json.loads((root / "capabilities" / "policy-balance-state.json").read_text(encoding="utf-8"))
tools = json.loads((root / "capabilities" / "tool-use-state.json").read_text(encoding="utf-8"))
orch = json.loads((root / "capabilities" / "orchestrator-state.json").read_text(encoding="utf-8"))
compiler = json.loads((root / "capabilities" / "mission-compiler-state.json").read_text(encoding="utf-8"))

conflicts = []
dups = []

if policy.get("policy_biases", {}).get("trust_caution_bias", 0.5) < 0.35 and tools.get("tool_biases", {}).get("mcp_activation_value_bias", 0.55) > 0.75:
    conflicts.append("very low trust caution combined with high MCP activation bias may over-encourage optional external surfaces")

if orch.get("routing_biases", {}).get("prefer_single_agent_for_simple_work", 0.7) > 0.8 and orch.get("routing_biases", {}).get("specialist_escalation_sensitivity", 0.6) > 0.8:
    conflicts.append("strong single-agent preference and strong early specialist sensitivity are pulling in opposite directions")

if compiler.get("compiler_biases", {}).get("constraint_extraction_strength", 0.6) > 0.8 and policy.get("policy_biases", {}).get("soft_guidance_strength", 0.55) > 0.8:
    dups.append("compiler and policy layers may both be strengthening guidance in overlapping ways")

report = {
    "version": "v25",
    "generated_at": datetime.utcnow().isoformat() + "Z",
    "conflicts": conflicts,
    "duplications": dups
}
(root / "capabilities" / "cross-layer-conflicts.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
