#!/usr/bin/env python3
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
state_path = ROOT / "capabilities" / "mission-runtime-state.json"
state = json.loads(state_path.read_text())

if len(sys.argv) < 3:
    print("Usage: update-runtime-state.py <mission_id> <status> [current_phase] [note=...] [actor=...]")
    raise SystemExit(1)

mission_id = sys.argv[1]
status = sys.argv[2]
current_phase = sys.argv[3] if len(sys.argv) > 3 and "=" not in sys.argv[3] else None
extras = {}
for arg in sys.argv[4:] if current_phase else sys.argv[3:]:
    if "=" in arg:
        k, v = arg.split("=", 1)
        extras[k] = v

missions = state.setdefault("missions", [])
found = None
for mission in missions:
    if mission.get("mission_id") == mission_id:
        found = mission
        break

if found is None:
    found = {"mission_id": mission_id, "current_phase": current_phase, "status": status, "blocked_by": [], "notes": []}
    missions.append(found)

found["status"] = status
if current_phase:
    found["current_phase"] = current_phase
if "note" in extras:
    found.setdefault("notes", []).append(extras["note"])
if "blocked_by" in extras:
    found["blocked_by"] = [x for x in extras["blocked_by"].split(",") if x]
if "actor" in extras:
    state["last_updated_by"] = extras["actor"]
state["active_mission"] = mission_id

state_path.write_text(json.dumps(state, indent=2))
print(json.dumps(found, indent=2))
