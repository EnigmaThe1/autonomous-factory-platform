#!/usr/bin/env python3
import json, pathlib, sys, datetime
root = pathlib.Path(__file__).resolve().parents[1]
state_path = root/'capabilities'/'freshness-state.json'
state = json.loads(state_path.read_text())
if len(sys.argv) < 3:
    print('Usage: update-freshness-state.py <item_id> <fresh|warning|stale|unknown> [kind=capability|source]')
    raise SystemExit(1)
item_id, freshness = sys.argv[1], sys.argv[2]
kind = 'capability'
for arg in sys.argv[3:]:
    if arg.startswith('kind='):
        kind = arg.split('=',1)[1]
today = datetime.date.today().isoformat()
state['items'][item_id] = {'kind':kind,'freshness':freshness,'last_checked':today}
state_path.write_text(json.dumps(state, indent=2) + '
')
with open(root/'capabilities'/'refresh-history.jsonl','a') as f:
    f.write(json.dumps({'ts':today,'item_id':item_id,'freshness':freshness,'kind':kind})+'\n')
print(f'Updated {item_id} -> {freshness}')
