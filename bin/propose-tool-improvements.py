#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

root = Path(__file__).resolve().parents[1]
state_path = root / "capabilities" / "tool-use-state.json"
log_path = root / "capabilities" / "tool-use-log.jsonl"
improvement_log_path = root / "capabilities" / "tool-improvement-log.jsonl"

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
heavy_overuse = [e for e in entries if e.get("quality_label") in ("heavy_tool_overkill", "too_complex_combo")]
missing_optional = [e for e in entries if e.get("quality_label") in ("missing_mcp_help", "missing_plugin_help")]
good_validation = [e for e in entries if e.get("quality_label") == "validation_combo_helped"]

if len(heavy_overuse) >= 2:
    old = state["tool_biases"].get("prefer_lightweight_builtin_tools_first", 0.65)
    new = round(min(0.9, old + 0.05), 2)
    state["tool_biases"]["prefer_lightweight_builtin_tools_first"] = new
    adjustments.append({
        "area": "prefer_lightweight_builtin_tools_first",
        "from": old,
        "to": new,
        "reason": "repeated heavy-tool overuse suggests slightly stronger preference for lightweight tools first"
    })

if len(missing_optional) >= 2:
    old = state["tool_biases"].get("mcp_activation_value_bias", 0.55)
    new = round(min(0.9, old + 0.05), 2)
    state["tool_biases"]["mcp_activation_value_bias"] = new
    adjustments.append({
        "area": "mcp_activation_value_bias",
        "from": old,
        "to": new,
        "reason": "repeated missed-help outcomes suggest slightly stronger readiness to use helpful MCP/plugin surfaces"
    })

if len(good_validation) >= 2:
    old = state["tool_biases"].get("validation_tool_priority", 0.6)
    new = round(min(0.9, old + 0.05), 2)
    state["tool_biases"]["validation_tool_priority"] = new
    adjustments.append({
        "area": "validation_tool_priority",
        "from": old,
        "to": new,
        "reason": "repeated validation gains suggest slightly stronger priority for useful validation tools"
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
    "tool_use_state": state
}, indent=2))
