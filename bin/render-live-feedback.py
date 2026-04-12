#!/usr/bin/env python3
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
state_path = root / "capabilities" / "live-feedback-state.json"
state = json.loads(state_path.read_text(encoding="utf-8"))

print("# Live Feedback State")
print()
print(f"Generated: {state.get('generated_at')}")
print()
signals = state.get("signals", [])
if not signals:
    print("No live feedback recorded.")
else:
    for entry in signals[-20:]:
        print(f"- {entry.get('timestamp')} | {entry.get('capability')} | {entry.get('signal_type')} -> {entry.get('direction')}")
        if entry.get("note"):
            print(f"  note: {entry.get('note')}")
