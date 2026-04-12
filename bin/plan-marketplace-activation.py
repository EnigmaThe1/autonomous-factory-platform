#!/usr/bin/env python3
import json, sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
registry = json.loads((root/'capabilities'/'registry.json').read_text())
state = json.loads((root/'capabilities'/'activation-state.json').read_text())
query = ' '.join(sys.argv[1:]).lower()
terms = set(query.split())
rows = []
for cap in registry.get('capabilities', []):
    cid = cap.get('id')
    text = ' '.join([cid, cap.get('summary',''), ' '.join(cap.get('domains',[])), ' '.join(cap.get('triggers',[]))]).lower()
    if not terms or any(t in text for t in terms):
        current = state.get('capabilities', {}).get(cid, {}).get('state', 'discovered')
        recommended = 'reviewed' if current == 'discovered' else ('approved' if current == 'reviewed' else ('activated' if current in {'approved','mirrored'} else current))
        rows.append((cid, current, recommended, cap.get('type','unknown')))
print('MARKETPLACE ACTIVATION PLAN')
for cid, current, recommended, ctype in rows:
    print(f'- {cid}: {ctype} | current={current} | recommended_next={recommended}')
