#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "capabilities" / "registry.json"

def classify(text: str):
    t = text.lower()
    scores = {
        "research-pack": 0,
        "coding-pack": 0,
        "browser-ui-pack": 0,
        "data-db-pack": 0,
        "ops-deploy-pack": 0,
    }
    keywords = {
        "research-pack": ["research", "docs", "spec", "standards", "latest", "api"],
        "coding-pack": ["code", "implement", "bug", "feature", "refactor", "test"],
        "browser-ui-pack": ["browser", "ui", "frontend", "page", "visual", "playwright"],
        "data-db-pack": ["database", "sql", "postgres", "query", "metrics", "schema"],
        "ops-deploy-pack": ["deploy", "docker", "infra", "kubernetes", "runtime", "logs", "server"],
    }
    for cap, words in keywords.items():
        for w in words:
            if w in t:
                scores[cap] += 1
    return scores

def main():
    if len(sys.argv) < 2:
        print("Usage: plan-capabilities.py '<mission text>'", file=sys.stderr)
        sys.exit(1)
    mission = " ".join(sys.argv[1:])
    registry = json.loads(REGISTRY.read_text())
    scores = classify(mission)
    selected = [k for k,v in scores.items() if v > 0]
    deferred = [k for k,v in scores.items() if v == 0]
    out = {
        "mission": mission,
        "kernel_only_default": registry["always_on_kernel"],
        "required_now": selected,
        "useful_later": deferred,
        "note": "Heuristic starter output only. Final selection should be reviewed by the capability-selector agent."
    }
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
