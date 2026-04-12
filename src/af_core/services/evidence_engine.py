"""Evidence Engine — evaluates evidence sufficiency and controls promotion (ADR-006).

Tool failures only block when:
1. The failed tool was REQUIRED, AND
2. No substitute evidence exists

This prevents brittle overreaction to optional or environmental probe failures.
"""

import logging
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from af_core.models.enums import ToolNecessity
from af_core.models.evidence import EvidenceContract, ToolInvocation

logger = logging.getLogger(__name__)


@dataclass
class SufficiencyResult:
    """Result of evidence sufficiency evaluation."""

    sufficient: bool
    missing_required: list[str] = field(default_factory=list)
    missing_preferred: list[str] = field(default_factory=list)
    collected_count: int = 0
    required_count: int = 0
    notes: str = ""


class EvidenceEngine:
    """Evaluates whether collected evidence meets the contract requirements."""

    async def create_contract(
        self,
        work_item_id: str,
        required: list[str],
        preferred: list[str] | None = None,
        optional: list[str] | None = None,
        db: AsyncSession | None = None,
    ) -> EvidenceContract:
        """Create an evidence contract for a work item."""
        contract = EvidenceContract(
            work_item_id=work_item_id,
            required_evidence=required,
            preferred_evidence=preferred or [],
            optional_evidence=optional or [],
            collected_evidence=[],
            sufficiency_met=False,
        )
        if db:
            db.add(contract)
            await db.flush()
        return contract

    async def record_evidence(
        self,
        contract: EvidenceContract,
        evidence_type: str,
        evidence_data: dict,
        db: AsyncSession,
    ) -> EvidenceContract:
        """Record a piece of collected evidence against the contract."""
        collected = list(contract.collected_evidence or [])
        collected.append(
            {
                "type": evidence_type,
                "data": evidence_data,
            }
        )
        contract.collected_evidence = collected

        # Re-evaluate sufficiency
        result = self.evaluate_sufficiency(contract)
        contract.sufficiency_met = result.sufficient
        contract.evaluation_notes = result.notes

        await db.flush()
        return contract

    async def record_tool_invocation(
        self,
        mission_id: str,
        tool_name: str,
        tool_category: str,
        necessity: ToolNecessity,
        input_params: dict,
        success: bool,
        output_result: dict | None = None,
        error_message: str | None = None,
        duration_ms: int | None = None,
        work_item_id: str | None = None,
        db: AsyncSession | None = None,
    ) -> ToolInvocation:
        """Record a tool invocation for audit and evidence tracking."""
        invocation = ToolInvocation(
            mission_id=mission_id,
            work_item_id=work_item_id,
            tool_name=tool_name,
            tool_category=tool_category,
            necessity=necessity,
            input_params=input_params,
            output_result=output_result,
            success=success,
            error_message=error_message,
            duration_ms=duration_ms,
        )
        if db:
            db.add(invocation)
            await db.flush()
        return invocation

    def evaluate_sufficiency(self, contract: EvidenceContract) -> SufficiencyResult:
        """Evaluate whether collected evidence meets contract requirements.

        Required evidence must all be present for sufficiency.
        Preferred evidence is noted but not blocking.
        Optional evidence is ignored for sufficiency.
        """
        collected_types = {e["type"] for e in (contract.collected_evidence or [])}

        required = contract.required_evidence or []
        preferred = contract.preferred_evidence or []

        missing_required = [r for r in required if r not in collected_types]
        missing_preferred = [p for p in preferred if p not in collected_types]

        sufficient = len(missing_required) == 0

        notes_parts = []
        if sufficient:
            notes_parts.append("All required evidence collected.")
        else:
            notes_parts.append(f"Missing required evidence: {', '.join(missing_required)}")
        if missing_preferred:
            notes_parts.append(f"Missing preferred evidence: {', '.join(missing_preferred)}")

        return SufficiencyResult(
            sufficient=sufficient,
            missing_required=missing_required,
            missing_preferred=missing_preferred,
            collected_count=len(collected_types),
            required_count=len(required),
            notes=" ".join(notes_parts),
        )

    async def evaluate_tool_failure_impact(
        self,
        invocation: ToolInvocation,
        contract: EvidenceContract | None,
    ) -> str:
        """Determine if a tool failure should block, degrade, or continue.

        Per ADR-006: optional tool failures do NOT block by default.
        Only required tools with no substitute evidence cause blocking.

        Returns: "block", "degrade", or "continue"
        """
        if invocation.success:
            return "continue"

        if invocation.necessity == ToolNecessity.OPTIONAL:
            return "continue"

        if invocation.necessity == ToolNecessity.PREFERRED:
            # Check if we have alternative evidence
            if contract:
                result = self.evaluate_sufficiency(contract)
                if result.sufficient:
                    return "continue"
            return "degrade"

        # Required tool failed
        if contract:
            # Check if substitute evidence makes this non-blocking
            result = self.evaluate_sufficiency(contract)
            if result.sufficient:
                return "continue"

        return "block"
