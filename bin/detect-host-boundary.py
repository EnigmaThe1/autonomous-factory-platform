#!/usr/bin/env python3
import json, platform, pathlib

system = platform.system().lower()
if "darwin" in system:
    key = "macos"
elif "windows" in system:
    key = "windows"
else:
    key = "linux"

policy_path = pathlib.Path(__file__).resolve().parent.parent / "capabilities" / "host-boundary-policy.json"
policy = json.loads(policy_path.read_text())
result = {
    "detected_platform": key,
    "protected_write_prefixes": policy["platforms"][key]["protected_write_prefixes"],
    "sensitive_read_paths": policy["platforms"][key]["sensitive_read_paths"],
    "destructive_command_patterns": policy["destructive_command_patterns"],
    "principle": policy["principle"]
}
print(json.dumps(result, indent=2))
