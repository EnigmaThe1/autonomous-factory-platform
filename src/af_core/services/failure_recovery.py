"""Failure classification and recovery routing.

Classifies failures by cause, evaluates whether they matter (via evidence
sufficiency), and decides the recovery action: continue, retry, replan, block, or escalate.
"""

import logging
from dataclasses import dataclass

from af_core.models.enums import FailureClass, RecoveryAction, ToolNecessity
from af_core.services.evidence_engine import EvidenceEngine

logger = logging.getLogger(__name__)


@dataclass
class FailureReport:
    """Result of failure classification and recovery routing."""

    failure_class: FailureClass
    recovery_action: RecoveryAction
    reason: str
    should_block: bool
    retry_recommended: bool


class FailureClassifier:
    """Classifies failures and determines recovery actions."""

    # Keywords that suggest transient failures
    TRANSIENT_PATTERNS = [
        "timeout",
        "timed out",
        "connection reset",
        "connection refused",
        "temporary",
        "retry",
        "rate limit",
        "429",
        "503",
        "502",
    ]

    ENVIRONMENTAL_PATTERNS = [
        "not found",
        "no such file",
        "command not found",
        "permission denied",
        "disk full",
        "out of memory",
        "oom",
    ]

    SCOPE_PATTERNS = [
        "outside workspace",
        "protected path",
        "unauthorized",
        "access denied",
        "forbidden",
    ]

    POLICY_PATTERNS = [
        "policy violation",
        "not allowed",
        "blocked by policy",
        "requires approval",
    ]

    def classify(self, error_message: str) -> FailureClass:
        """Classify a failure based on error message content."""
        msg_lower = error_message.lower()

        if any(p in msg_lower for p in self.POLICY_PATTERNS):
            return FailureClass.POLICY_VIOLATION

        if any(p in msg_lower for p in self.SCOPE_PATTERNS):
            return FailureClass.SCOPE_VIOLATION

        if any(p in msg_lower for p in self.TRANSIENT_PATTERNS):
            return FailureClass.TRANSIENT

        if any(p in msg_lower for p in self.ENVIRONMENTAL_PATTERNS):
            return FailureClass.ENVIRONMENTAL

        return FailureClass.UNKNOWN


class RecoveryRouter:
    """Decides recovery actions based on failure class and evidence state."""

    def __init__(self) -> None:
        self.classifier = FailureClassifier()
        self.evidence_engine = EvidenceEngine()

    def route(
        self,
        error_message: str,
        necessity: ToolNecessity = ToolNecessity.OPTIONAL,
        retry_count: int = 0,
        max_retries: int = 3,
        has_substitute_evidence: bool = False,
    ) -> FailureReport:
        """Classify failure and determine recovery action."""
        failure_class = self.classifier.classify(error_message)

        # Decision matrix
        if failure_class == FailureClass.POLICY_VIOLATION:
            return FailureReport(
                failure_class=failure_class,
                recovery_action=RecoveryAction.ESCALATE,
                reason="Policy violation requires operator intervention",
                should_block=True,
                retry_recommended=False,
            )

        if failure_class == FailureClass.SCOPE_VIOLATION:
            return FailureReport(
                failure_class=failure_class,
                recovery_action=RecoveryAction.BLOCK,
                reason="Scope violation — cannot proceed without scope change",
                should_block=True,
                retry_recommended=False,
            )

        if necessity == ToolNecessity.OPTIONAL:
            return FailureReport(
                failure_class=failure_class,
                recovery_action=RecoveryAction.CONTINUE,
                reason="Optional tool failure — continuing without blocking",
                should_block=False,
                retry_recommended=False,
            )

        if has_substitute_evidence:
            return FailureReport(
                failure_class=failure_class,
                recovery_action=RecoveryAction.CONTINUE,
                reason="Substitute evidence available — continuing",
                should_block=False,
                retry_recommended=False,
            )

        if failure_class == FailureClass.TRANSIENT and retry_count < max_retries:
            return FailureReport(
                failure_class=failure_class,
                recovery_action=RecoveryAction.RETRY,
                reason=f"Transient failure, retry {retry_count + 1}/{max_retries}",
                should_block=False,
                retry_recommended=True,
            )

        if failure_class == FailureClass.ENVIRONMENTAL:
            return FailureReport(
                failure_class=failure_class,
                recovery_action=RecoveryAction.REPLAN,
                reason="Environmental failure — replanning recommended",
                should_block=False,
                retry_recommended=False,
            )

        # Required tool, no substitute, not transient
        if necessity == ToolNecessity.REQUIRED:
            return FailureReport(
                failure_class=failure_class,
                recovery_action=RecoveryAction.BLOCK,
                reason="Required tool failed with no substitute evidence",
                should_block=True,
                retry_recommended=retry_count < max_retries,
            )

        # Preferred tool — degrade
        return FailureReport(
            failure_class=failure_class,
            recovery_action=RecoveryAction.CONTINUE,
            reason="Preferred tool failed — degraded continuation",
            should_block=False,
            retry_recommended=retry_count < max_retries,
        )
