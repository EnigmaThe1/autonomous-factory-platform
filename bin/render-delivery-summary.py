#!/usr/bin/env python3
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
state = json.loads((root/"capabilities/delivery-state.json").read_text())

print("# Delivery Summary\n")
for k,v in state["status"].items():
    print(f"{k.upper()}: {len(v)} items")
