#!/usr/bin/env python3
import json, sys, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
reg = json.load(open(os.path.join(root, 'capabilities', 'sources', 'registry.json')))
query = ' '.join(sys.argv[1:]).strip() or 'unspecified mission'
print(f'# Source Ingestion Plan\n')
print(f'Mission context: {query}\n')
for src in reg.get('sources', []):
    print(f'- {src["id"]}: status={src["status"]}, default_action={src["default_action"]}, scope={", ".join(src.get("scope", []))}')
print('\nSuggested next step: review only the smallest source set needed for the mission.')
