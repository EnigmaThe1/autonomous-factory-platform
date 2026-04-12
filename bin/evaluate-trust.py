#!/usr/bin/env python3
import json, sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
registry = json.loads((root / 'capabilities' / 'registry.json').read_text())
query = ' '.join(sys.argv[1:]).lower()

matches = []
for cap in registry.get('capabilities', []):
    hay = ' '.join([
        cap.get('id',''), cap.get('summary',''), ' '.join(cap.get('domains',[])), ' '.join(cap.get('triggers',[]))
    ]).lower()
    score = sum(1 for token in query.split() if token and token in hay)
    if score:
        matches.append((score, cap))

matches.sort(key=lambda x: (-x[0], x[1].get('risk_level','medium')))
print(json.dumps([
    {
        'id': cap['id'],
        'trust_tier': cap.get('trust_tier','unknown'),
        'risk_level': cap.get('risk_level','unknown'),
        'approval_mode': cap.get('approval_mode','ask'),
        'activation_mode': cap.get('activation_mode','on_demand'),
        'summary': cap.get('summary','')
    }
    for _, cap in matches[:10]
], indent=2))
