#!/usr/bin/env python3
import json, pathlib, platform

policy_path = pathlib.Path(__file__).resolve().parent.parent / "capabilities" / "host-boundary-policy.json"
policy = json.loads(policy_path.read_text())
system = platform.system().lower()
if "darwin" in system:
    key = "macos"
elif "windows" in system:
    key = "windows"
else:
    key = "linux"

print("# Host Boundary Report")
print()
print(f"- principle: {policy['principle']}")
print(f"- detected platform: {key}")
print("- protected write prefixes:")
for item in policy["platforms"][key]["protected_write_prefixes"]:
    print(f"  - {item}")
print("- sensitive read paths:")
for item in policy["platforms"][key]["sensitive_read_paths"]:
    print(f"  - {item}")
print("- destructive command patterns:")
for item in policy["destructive_command_patterns"]:
    print(f"  - {item}")
print()
print("Project-space autonomy remains broad; only host-critical actions are blocked.")
