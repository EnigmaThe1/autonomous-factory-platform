#!/usr/bin/env python3
import json, sys, os
if len(sys.argv) < 3:
    print('usage: curate-source.py <source_id> <new_state>')
    sys.exit(1)
source_id, new_state = sys.argv[1], sys.argv[2]
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = os.path.join(root, 'capabilities', 'source-reviews.json')
data = json.load(open(path))
found = False
for item in data.get('reviews', []):
    if item.get('source_id') == source_id:
        item['review_state'] = new_state
        item['recommended_next_state'] = new_state
        found = True
        break
if not found:
    data.setdefault('reviews', []).append({
        'source_id': source_id,
        'review_state': new_state,
        'review_notes': 'Updated locally.',
        'recommended_next_state': new_state
    })
with open(path, 'w') as f:
    json.dump(data, f, indent=2)
print(f'updated {source_id} -> {new_state}')
