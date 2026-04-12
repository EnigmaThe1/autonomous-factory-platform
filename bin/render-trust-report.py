#!/usr/bin/env python3
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
trust = json.loads((root / 'capabilities' / 'trust-policy.json').read_text())
registry = json.loads((root / 'capabilities' / 'registry.json').read_text())

caps = registry.get('capabilities', [])
by_tier = {}
for c in caps:
    by_tier.setdefault(c.get('trust_tier','unknown'), []).append(c)

print('# Capability Trust Report
')
print('## Activation policy')
for k, v in trust.get('activation_policy', {}).items():
    print(f'- {k}: {v}')
print('
## Capabilities by trust tier')
for tier, items in sorted(by_tier.items()):
    print(f'
### {tier}')
    for item in items:
        print(f"- {item['id']} ({item.get('risk_level','unknown')}, {item.get('approval_mode','ask')})")
