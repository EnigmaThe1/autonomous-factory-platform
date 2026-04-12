#!/usr/bin/env python3
import json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
state = json.loads((root/'capabilities'/'activation-state.json').read_text())
print('ACTIVATION STATE SUMMARY')
for cid, meta in sorted(state.get('capabilities', {}).items()):
    print(f"- {cid}: state={meta.get('state')} source={meta.get('source','n/a')} mirror={meta.get('mirror','n/a')}")
