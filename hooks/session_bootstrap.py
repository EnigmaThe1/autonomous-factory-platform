#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

root = Path(__file__).resolve().parent.parent
out_root = root / ".claude-task-output"
out_root.mkdir(exist_ok=True)

session_id = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
session_dir = out_root / session_id
session_dir.mkdir(exist_ok=True)

(session_dir / "session_bootstrap.json").write_text(json.dumps({
    "created_at_utc": session_id,
    "purpose": "Bootstrap output folder for task artifacts.",
    "kernel_mode": "small-core-lazy-capability-activation"
}, indent=2))

print(json.dumps({
    "decision": "allow",
    "message": f"Session output folder prepared at {session_dir}"
}))
