"""Mission Compiler — transforms raw operator intent into a compiled mission contract.

Per ADR-005, no mission executes without compilation. The compiler:
1. Normalizes paths and scope
2. Separates inputs from outputs
3. Classifies ambiguities
4. Generates compiler findings
5. Produces an authoritative mission contract
"""

import logging
import os
import re
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from af_core.models.enums import FindingSeverity, MissionStatus
from af_core.models.mission import CompilerFinding, Mission, MissionContract
from af_core.services.event_bus import event_bus

logger = logging.getLogger(__name__)


@dataclass
class CompilationResult:
    success: bool
    contract: MissionContract | None = None
    findings: list[CompilerFinding] = field(default_factory=list)
    blocking: bool = False


class MissionCompiler:
    """Stateless compiler that analyzes raw mission text and produces a contract."""

    # Patterns for path detection
    _PATH_PATTERN = re.compile(r"(?:^|\s)([./~][\w./\-*]+)", re.MULTILINE)
    _URL_PATTERN = re.compile(r"https?://\S+")

    # Keywords that indicate inputs vs outputs
    _INPUT_KEYWORDS = {
        "read",
        "analyze",
        "inspect",
        "check",
        "review",
        "look at",
        "examine",
        "scan",
        "search",
        "find",
        "investigate",
        "understand",
    }
    _OUTPUT_KEYWORDS = {
        "create",
        "write",
        "build",
        "generate",
        "implement",
        "add",
        "modify",
        "update",
        "change",
        "fix",
        "refactor",
        "delete",
        "remove",
        "deploy",
        "install",
        "configure",
    }

    async def compile(
        self, mission: Mission, db: AsyncSession, workspace_root: str = "."
    ) -> CompilationResult:
        """Compile a mission from raw prompt into an authoritative contract."""
        mission.status = MissionStatus.COMPILING
        await db.flush()

        await event_bus.emit(
            "mission.compiling",
            {
                "mission_id": mission.id,
                "title": mission.title,
            },
        )

        findings: list[CompilerFinding] = []
        raw = mission.raw_prompt

        # Step 1: Extract and normalize paths
        paths = self._extract_paths(raw)
        path_corrections = self._normalize_paths(paths, workspace_root)
        for correction in path_corrections:
            findings.append(
                CompilerFinding(
                    mission_id=mission.id,
                    severity=FindingSeverity.INFO,
                    category="path_correction",
                    message=(
                        f"Path corrected: {correction['original']}"
                        f" -> {correction['corrected']}"
                    ),
                    details=correction,
                )
            )

        # Step 2: Separate inputs from outputs
        normalized_inputs = self._classify_inputs(raw)
        normalized_outputs = self._classify_outputs(raw)

        # Step 3: Classify ambiguities
        ambiguities = self._detect_ambiguities(raw, normalized_inputs, normalized_outputs)
        for amb in ambiguities:
            severity = (
                FindingSeverity.WARNING if amb["level"] == "warning" else FindingSeverity.ERROR
            )
            findings.append(
                CompilerFinding(
                    mission_id=mission.id,
                    severity=severity,
                    category="ambiguity",
                    message=amb["message"],
                    details=amb,
                )
            )

        # Step 4: Extract scope
        scope = self._extract_scope(raw, paths, workspace_root)

        # Step 5: Extract success criteria
        success_criteria = self._extract_success_criteria(raw)

        # Step 6: Check for blocking findings
        blocking_findings = [f for f in findings if f.severity == FindingSeverity.BLOCKING]
        has_blocking = len(blocking_findings) > 0

        if has_blocking:
            findings.append(
                CompilerFinding(
                    mission_id=mission.id,
                    severity=FindingSeverity.BLOCKING,
                    category="compilation",
                    message="Mission compilation blocked due to unresolvable issues",
                )
            )

        # Step 7: Generate the normalized objective
        objective = self._normalize_objective(mission.title, raw)

        # Build contract
        contract = MissionContract(
            mission_id=mission.id,
            normalized_objective=objective,
            normalized_scope=scope,
            normalized_inputs=normalized_inputs,
            normalized_outputs=normalized_outputs,
            path_corrections=path_corrections,
            success_criteria=success_criteria,
            policy_binding={},
            unresolved_ambiguities=ambiguities,
        )

        # Persist
        for finding in findings:
            db.add(finding)
        db.add(contract)

        if has_blocking:
            mission.status = MissionStatus.BLOCKED
        else:
            mission.status = MissionStatus.COMPILED

        await db.flush()

        await event_bus.emit(
            "mission.compiled",
            {
                "mission_id": mission.id,
                "status": mission.status.value,
                "findings_count": len(findings),
                "blocking": has_blocking,
            },
        )

        return CompilationResult(
            success=not has_blocking,
            contract=contract,
            findings=findings,
            blocking=has_blocking,
        )

    def _extract_paths(self, text: str) -> list[str]:
        """Extract file/directory paths from mission text."""
        paths = self._PATH_PATTERN.findall(text)
        # Filter out things that look like URLs
        urls = set(self._URL_PATTERN.findall(text))
        return [p.strip() for p in paths if not any(p in u for u in urls)]

    def _normalize_paths(self, paths: list[str], workspace_root: str) -> list[dict]:
        """Check paths against workspace and suggest corrections."""
        corrections = []
        for path in paths:
            original = path
            # Expand ~ to home
            expanded = os.path.expanduser(path)
            # Make relative to workspace if absolute
            if os.path.isabs(expanded) and workspace_root != ".":
                try:
                    expanded = os.path.relpath(expanded, workspace_root)
                except ValueError:
                    pass

            if expanded != original:
                corrections.append(
                    {
                        "original": original,
                        "corrected": expanded,
                        "exists": os.path.exists(
                            os.path.join(workspace_root, expanded)
                            if not os.path.isabs(expanded)
                            else expanded
                        ),
                    }
                )
        return corrections

    def _classify_inputs(self, text: str) -> dict:
        """Identify input references in the mission text."""
        text_lower = text.lower()
        detected = []
        for kw in self._INPUT_KEYWORDS:
            if kw in text_lower:
                detected.append(kw)
        paths = self._extract_paths(text)
        return {"keywords": detected, "paths": paths}

    def _classify_outputs(self, text: str) -> dict:
        """Identify output/mutation references in the mission text."""
        text_lower = text.lower()
        detected = []
        for kw in self._OUTPUT_KEYWORDS:
            if kw in text_lower:
                detected.append(kw)
        return {"keywords": detected, "artifacts": []}

    def _detect_ambiguities(self, text: str, inputs: dict, outputs: dict) -> list[dict]:
        """Detect ambiguities that could affect execution quality."""
        ambiguities = []

        # No clear output action
        if not outputs.get("keywords"):
            ambiguities.append(
                {
                    "level": "warning",
                    "type": "no_clear_output",
                    "message": "No clear output/mutation action detected in mission text. "
                    "The mission may be research-only or underspecified.",
                }
            )

        # Very short prompt
        if len(text.split()) < 5:
            ambiguities.append(
                {
                    "level": "warning",
                    "type": "underspecified",
                    "message": "Mission text is very short. Consider providing more detail "
                    "for better planning and execution.",
                }
            )

        # Both read and write on same paths — potential conflict
        input_paths = set(inputs.get("paths", []))
        if input_paths and outputs.get("keywords"):
            for kw in ("delete", "remove"):
                if kw in (outputs.get("keywords") or []):
                    ambiguities.append(
                        {
                            "level": "warning",
                            "type": "destructive_action",
                            "message": f"Destructive action '{kw}' detected. "
                            "This may require approval.",
                        }
                    )

        return ambiguities

    def _extract_scope(self, text: str, paths: list[str], workspace_root: str) -> dict:
        """Determine the scope of the mission."""
        return {
            "workspace_root": workspace_root,
            "referenced_paths": paths,
            "estimated_breadth": "narrow" if len(paths) <= 3 else "broad",
        }

    def _extract_success_criteria(self, text: str) -> list[str]:
        """Extract explicit or implied success criteria."""
        criteria = []
        # Look for explicit criteria markers
        for marker in ("should", "must", "ensure", "verify", "make sure", "expect"):
            for line in text.split("\n"):
                if marker in line.lower():
                    criteria.append(line.strip())
                    break

        if not criteria:
            criteria.append("Mission objective completed as described")

        return criteria

    def _normalize_objective(self, title: str, raw_prompt: str) -> str:
        """Create a normalized single-statement objective."""
        # Use title if it's meaningful, otherwise derive from prompt
        if title and len(title.split()) >= 3:
            return title

        # Take first sentence of prompt
        first_line = raw_prompt.strip().split("\n")[0]
        if len(first_line) > 200:
            first_line = first_line[:200] + "..."
        return first_line
