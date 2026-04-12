#!/usr/bin/env bash
set -euo pipefail
QUERY="${*:-generic mission}"
DIR="$(cd "$(dirname "$0")/.." && pwd)"
python3 "$DIR/bin/plan-capabilities.py" "$QUERY"
echo
python3 "$DIR/bin/evaluate-trust.py" "$QUERY"
echo
python3 "$DIR/bin/plan-source-ingestion.py" "$QUERY"
echo
python3 "$DIR/bin/plan-marketplace-activation.py" "$QUERY"
echo
python3 "$DIR/bin/plan-refresh-cycle.py" "$QUERY"


echo
echo "[v10] Compiling mission graph..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"${SCRIPT_DIR}/compile-mission-graph.py" "$MISSION"
echo
echo "[v10] Rendering latest mission graph..."
"${SCRIPT_DIR}/render-mission-graph.py"
echo
echo "[v10] Escalation recommendation..."
"${SCRIPT_DIR}/decide-escalation.py"

python bin/render-host-boundary-report.py || true


echo
echo "[factory] environment report"
"$(dirname "$0")/render-environment-report.py" || true

echo
echo "[factory] execution zone recommendation"
"$(dirname "$0")/recommend-execution-zone.py" || true

echo
echo "[factory] toolchain gap analysis"
"$(dirname "$0")/analyze-toolchain-gaps.py" "$MISSION" || true

echo
echo "[factory] toolchain gap report"
"$(dirname "$0")/render-toolchain-gap-report.py" || true

echo
echo "[factory] expansion plan"
"$(dirname "$0")/plan-expansion.py" || true

./bin/decide-capability-state.py "$MISSION"
./bin/render-capability-decisions.py

./bin/decide-phase-promotion.py research implementation
./bin/render-phase-promotion.py

./bin/weigh-promotion-evidence.py "$MISSION"
./bin/render-evidence-weights.py

./bin/render-live-feedback.py

./bin/detect-mission-archetype.py "$MISSION"
./bin/render-learning-biases.py

./bin/detect-heuristic-drift.py
./bin/render-heuristic-state.py

./bin/render-compiler-state.py

./bin/render-orchestrator-state.py

./bin/render-tool-use-state.py

./bin/render-policy-state.py
./bin/check-autonomy-balance.py

./bin/synthesize-system-state.py
./bin/detect-cross-layer-conflicts.py
./bin/render-system-synthesis.py

./bin/render-execution-surface-state.py

./bin/render-memory-state.py

./bin/render-goal-state.py

./bin/render-governance-state.py

./bin/render-research-state.py

./bin/render-validation-state.py

./bin/render-execution-strategy-state.py

./bin/render-collaboration-state.py

./bin/render-operator-interaction-state.py

./bin/render-proof-posture-state.py

./bin/render-rollback-containment-state.py

./bin/render-resource-intelligence-state.py
