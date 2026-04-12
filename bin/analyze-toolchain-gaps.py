#!/usr/bin/env python3
import json, shutil, sys
from pathlib import Path

mission = " ".join(sys.argv[1:]).strip() or "unspecified mission"
root = Path(__file__).resolve().parent.parent
registry_path = root / "capabilities" / "registry.json"
registry = json.loads(registry_path.read_text()) if registry_path.exists() else {"capabilities": []}
available_bins = {name: shutil.which(name) is not None for name in ["python", "python3", "node", "npm", "git", "docker", "psql"]}
mission_l = mission.lower()

required = []
if any(x in mission_l for x in ["web", "ui", "browser", "frontend"]):
    required += ["browser-ui-pack", "coding-pack"]
if any(x in mission_l for x in ["database", "postgres", "sql", "db"]):
    required += ["data-db-pack"]
if any(x in mission_l for x in ["deploy", "docker", "ops", "infrastructure", "infra"]):
    required += ["ops-deploy-pack"]
if any(x in mission_l for x in ["research", "docs", "latest", "look up"]):
    required += ["research-pack"]
required = list(dict.fromkeys(required))

catalog = {c.get("id"): c for c in registry.get("capabilities", [])}
available = [cid for cid in required if cid in catalog]
gaps = [cid for cid in required if cid not in catalog]

recommended_expansion = []
if "browser-ui-pack" in required and not available_bins.get("node"):
    recommended_expansion.append("Node.js toolchain or browser-oriented plugin/MCP support")
if "data-db-pack" in required and not available_bins.get("psql"):
    recommended_expansion.append("Database client tooling or MCP-based DB connectivity")
if "ops-deploy-pack" in required and not available_bins.get("docker"):
    recommended_expansion.append("Container/runtime tooling or deployment-specific capability pack")

report = {
    "generated_at": None,
    "mission": mission,
    "required_capabilities": required,
    "available_registry_entries": available,
    "registry_gaps": gaps,
    "recommended_expansion": recommended_expansion,
    "deferred_optional": []
}
(root / "capabilities" / "toolchain-gap-state.json").write_text(json.dumps(report, indent=2) + "
")
print(json.dumps(report, indent=2))
