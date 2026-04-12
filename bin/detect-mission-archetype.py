#!/usr/bin/env python3
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
archetypes_path = root / "capabilities" / "mission-archetypes.json"
archetypes = json.loads(archetypes_path.read_text(encoding="utf-8")).get("known_archetypes", {})

mission = " ".join(sys.argv[1:]).lower().strip()
if not mission:
    print("usage: detect-mission-archetype.py <mission text>")
    sys.exit(1)

scores = {}
for name, meta in archetypes.items():
    score = 0
    for kw in meta.get("keywords", []):
        if kw.lower() in mission:
            score += 1
    if score:
        scores[name] = score

if not scores:
    result = {"archetype": "unknown", "confidence": "low"}
else:
    best = sorted(scores.items(), key=lambda x: (-x[1], x[0]))[0]
    confidence = "high" if best[1] >= 3 else "medium"
    result = {"archetype": best[0], "confidence": confidence, "scores": scores}

print(json.dumps(result, indent=2))
