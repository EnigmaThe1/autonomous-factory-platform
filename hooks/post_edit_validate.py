#!/usr/bin/env python3
import json, os, pathlib, subprocess, sys

def run(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        return {"cmd": cmd, "code": result.returncode, "stdout": result.stdout[-4000:], "stderr": result.stderr[-4000:]}
    except Exception as e:
        return {"cmd": cmd, "code": -1, "stdout": "", "stderr": str(e)}

root = pathlib.Path(".")
checks = []

if (root / "package.json").exists():
    checks.append(run("npm run -s lint"))
    checks.append(run("npm test -- --runInBand"))

if (root / "pytest.ini").exists() or (root / "tests").exists():
    checks.append(run("pytest -q"))

outdir = root / ".claude-task-output" / "latest"
outdir.mkdir(parents=True, exist_ok=True)
(outdir / "post_edit_validation.json").write_text(json.dumps(checks, indent=2), encoding="utf-8")

print(json.dumps({
    "decision": "allow",
    "reason": "Post-edit validation attempted.",
    "continue": True
}))
