#!/usr/bin/env python3
import json, sys
from pathlib import Path
from datetime import datetime, timezone
if len(sys.argv) < 3:
    print('Usage: update-activation-state.py <capability_id> <new_state> [key=value ...]')
    sys.exit(1)
capability_id = sys.argv[1]
new_state = sys.argv[2]
extra = {}
for item in sys.argv[3:]:
    if '=' in item:
        k,v = item.split('=',1)
        extra[k]=v
root = Path(__file__).resolve().parents[1]
state_path = root/'capabilities'/'activation-state.json'
history_path = root/'capabilities'/'activation-history.jsonl'
state = json.loads(state_path.read_text())
allowed = state['lifecycle_states']
if new_state not in allowed:
    raise SystemExit(f'Invalid state: {new_state}')
entry = state.setdefault('capabilities', {}).setdefault(capability_id, {})
old_state = entry.get('state', 'discovered')
entry['state'] = new_state
entry['last_updated'] = datetime.now(timezone.utc).date().isoformat()
entry.update(extra)
state_path.write_text(json.dumps(state, indent=2)+'\n')
record = {
    'timestamp': datetime.now(timezone.utc).isoformat(),
    'capability': capability_id,
    'from': old_state,
    'to': new_state,
    'actor': extra.get('actor','manual'),
    'reason': extra.get('reason','state update')
}
with history_path.open('a') as f:
    f.write(json.dumps(record)+'\n')
print(json.dumps(record, indent=2))
