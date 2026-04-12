#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

root = Path(__file__).resolve().parents[1]
report_path = root / "capabilities" / "autonomy-balance-report.json"
log_path = root / "capabilities" / "policy-quality-log.jsonl"

entries = []
if log_path.exists():
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except Exception:
            pass

signals = []
status = "aligned"

too_cautious = sum(1 for e in entries if e.get("quality_label") in ("too_cautious", "unhelpful_guidance_noise"))
host_confusing = sum(1 for e in entries if e.get("quality_label") == "host_boundary_confusing")

if too_cautious >= 3:
    status = "watch"
    signals.append("soft guidance may be drifting toward unnecessary project-space caution")
if host_confusing >= 2:
    status = "watch"
    signals.append("host-boundary signaling may be too unclear")

report = {
    "version": "v24",
    "generated_at": datetime.utcnow().isoformat() + "Z",
    "status": status,
    "signals": signals
}
report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
