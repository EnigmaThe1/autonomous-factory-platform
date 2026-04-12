#!/usr/bin/env python3
import json, pathlib, collections
root = pathlib.Path(__file__).resolve().parents[1]
state = json.loads((root/'capabilities'/'freshness-state.json').read_text())
counts = collections.Counter(v['freshness'] for v in state['items'].values())
print('FRESHNESS REPORT')
for k in ['fresh','warning','stale','unknown']:
    print(f'- {k}: {counts.get(k,0)}')
print('
Items needing attention:')
for key, item in state['items'].items():
    if item['freshness'] in {'warning','stale','unknown'}:
        print(f"- {key} ({item['kind']}) -> {item['freshness']}")
