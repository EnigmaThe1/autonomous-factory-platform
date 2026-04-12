#!/usr/bin/env python3
import json, pathlib, sys
root = pathlib.Path(__file__).resolve().parents[1]
policy = json.loads((root/'capabilities'/'refresh-policy.json').read_text())
fresh = json.loads((root/'capabilities'/'freshness-state.json').read_text())
query = ' '.join(sys.argv[1:]).strip() or 'generic mission'
print('REFRESH CYCLE PLAN')
print(f'Mission context: {query}')
print('
Policy highlights:')
print(f"- Never auto-activate on refresh: {policy['never_auto_activate_on_refresh']}")
print(f"- Stage refresh updates to review queue: {policy['refresh_updates_stage_to_review_queue']}")
print('
Candidates:')
for key, item in fresh['items'].items():
    if item['freshness'] in {'warning','stale','unknown'}:
        print(f"- {key}: {item['freshness']} (next review due {item.get('next_review_due','unknown')})")
print('
Recommended flow: metadata refresh -> review queue -> trust review -> activation decision only if separately approved')
