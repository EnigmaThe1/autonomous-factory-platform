#!/usr/bin/env python3
import json, sys, re, pathlib, platform

raw = sys.stdin.read().strip()
try:
    obj = json.loads(raw) if raw else {}
except Exception:
    obj = {}

tool_name = obj.get("tool_name", "")
tool_input = obj.get("tool_input", {}) or {}
command = ""
path_text = ""

if isinstance(tool_input, dict):
    command = str(tool_input.get("command", "") or "")
    path_text = json.dumps(tool_input)
else:
    path_text = str(tool_input)

lower = (command + "\n" + path_text).lower()

policy_path = pathlib.Path(__file__).resolve().parent.parent / "capabilities" / "host-boundary-policy.json"
policy = json.loads(policy_path.read_text())

system = platform.system().lower()
if "darwin" in system:
    platform_key = "macos"
elif "windows" in system:
    platform_key = "windows"
else:
    platform_key = "linux"

protected_write_prefixes = [p.lower() for p in policy["platforms"][platform_key]["protected_write_prefixes"]]
sensitive_read_paths = [p.lower() for p in policy["platforms"][platform_key]["sensitive_read_paths"]]

pattern_map = [
    r"\brm\s+-rf\s+/\s*$",
    r"\brm\s+-rf\s+/\*",
    r"\bmkfs(\.\w+)?\b",
    r"\bfdisk\b",
    r"\bdd\s+if=",
    r"\bdiskpart\b",
    r"\bformat\b",
    r"\bbcdedit\b",
    r"\bshutdown\b",
    r"\breboot\b",
    r"\bhalt\b",
    r"\bpoweroff\b",
    r"\bsudo\b",
    r"\bdoas\b",
]

def emit(decision, reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason
        }
    }))

# Only enforce host-safety and machine-integrity boundaries.
if tool_name in {"Edit", "Write"}:
    if any(prefix in lower for prefix in protected_write_prefixes):
        emit("deny", "Blocked: write/edit attempt on host-critical system path.")
        raise SystemExit(0)

if tool_name in {"Read"}:
    if any(path in lower for path in sensitive_read_paths):
        emit("deny", "Blocked: read attempt on host-sensitive path.")
        raise SystemExit(0)

if tool_name == "Bash":
    for pat in pattern_map:
        if re.search(pat, lower):
            emit("deny", "Blocked: host-destructive or machine-integrity-threatening command.")
            raise SystemExit(0)

emit("allow", "Allowed: broad autonomy preserved in project/task space; only host-critical actions are blocked.")
