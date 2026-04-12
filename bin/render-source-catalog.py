#!/usr/bin/env python3
import json, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
reg = json.load(open(os.path.join(root, 'capabilities', 'sources', 'registry.json')))
print('# Source Catalog\n')
for src in reg.get('sources', []):
    print(f'## {src["id"]}')
    print(f'- type: {src.get("type")}')
    print(f'- provider: {src.get("provider")}')
    print(f'- status: {src.get("status")}')
    print(f'- default_action: {src.get("default_action")}')
    print(f'- notes: {src.get("notes", "")}')
    print()
