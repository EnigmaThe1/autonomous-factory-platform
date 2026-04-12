"""Evidence engine and failure/recovery tests."""

import pytest

from af_core.models.enums import FailureClass, RecoveryAction, ToolNecessity
from af_core.models.evidence import EvidenceContract, ToolInvocation
from af_core.services.evidence_engine import EvidenceEngine
from af_core.services.failure_recovery import FailureClassifier, RecoveryRouter


class TestEvidenceSufficiency:
    def setup_method(self):
        self.engine = EvidenceEngine()

    def _make_contract(self, required, preferred=None, optional=None, collected=None):
        return EvidenceContract(
            required_evidence=required,
            preferred_evidence=preferred or [],
            optional_evidence=optional or [],
            collected_evidence=collected or [],
        )

    def test_empty_required_is_sufficient(self):
        contract = self._make_contract(required=[])
        result = self.engine.evaluate_sufficiency(contract)
        assert result.sufficient

    def test_all_required_collected_is_sufficient(self):
        contract = self._make_contract(
            required=["test_results", "code_review"],
            collected=[
                {"type": "test_results", "data": {"passed": True}},
                {"type": "code_review", "data": {"approved": True}},
            ],
        )
        result = self.engine.evaluate_sufficiency(contract)
        assert result.sufficient
        assert result.missing_required == []

    def test_missing_required_is_insufficient(self):
        contract = self._make_contract(
            required=["test_results", "code_review"],
            collected=[{"type": "test_results", "data": {}}],
        )
        result = self.engine.evaluate_sufficiency(contract)
        assert not result.sufficient
        assert "code_review" in result.missing_required

    def test_missing_preferred_still_sufficient(self):
        contract = self._make_contract(
            required=["test_results"],
            preferred=["performance_benchmark"],
            collected=[{"type": "test_results", "data": {}}],
        )
        result = self.engine.evaluate_sufficiency(contract)
        assert result.sufficient
        assert "performance_benchmark" in result.missing_preferred


class TestToolFailureImpact:
    def setup_method(self):
        self.engine = EvidenceEngine()

    def _make_invocation(self, necessity, success):
        return ToolInvocation(
            mission_id="test",
            tool_name="test_tool",
            tool_category="validation",
            necessity=necessity,
            input_params={},
            success=success,
        )

    @pytest.mark.asyncio
    async def test_optional_failure_continues(self):
        inv = self._make_invocation(ToolNecessity.OPTIONAL, success=False)
        result = await self.engine.evaluate_tool_failure_impact(inv, None)
        assert result == "continue"

    @pytest.mark.asyncio
    async def test_required_failure_without_evidence_blocks(self):
        inv = self._make_invocation(ToolNecessity.REQUIRED, success=False)
        contract = EvidenceContract(
            required_evidence=["test_results"],
            collected_evidence=[],
        )
        result = await self.engine.evaluate_tool_failure_impact(inv, contract)
        assert result == "block"

    @pytest.mark.asyncio
    async def test_required_failure_with_substitute_continues(self):
        inv = self._make_invocation(ToolNecessity.REQUIRED, success=False)
        contract = EvidenceContract(
            required_evidence=["test_results"],
            collected_evidence=[{"type": "test_results", "data": {"manual": True}}],
        )
        result = await self.engine.evaluate_tool_failure_impact(inv, contract)
        assert result == "continue"

    @pytest.mark.asyncio
    async def test_success_always_continues(self):
        inv = self._make_invocation(ToolNecessity.REQUIRED, success=True)
        result = await self.engine.evaluate_tool_failure_impact(inv, None)
        assert result == "continue"


class TestFailureClassifier:
    def setup_method(self):
        self.classifier = FailureClassifier()

    def test_transient_timeout(self):
        assert self.classifier.classify("Connection timed out") == FailureClass.TRANSIENT

    def test_transient_rate_limit(self):
        assert self.classifier.classify("429 rate limit exceeded") == FailureClass.TRANSIENT

    def test_environmental_not_found(self):
        assert self.classifier.classify("No such file or directory") == FailureClass.ENVIRONMENTAL

    def test_scope_violation(self):
        assert self.classifier.classify("Path outside workspace") == FailureClass.SCOPE_VIOLATION

    def test_policy_violation(self):
        assert self.classifier.classify("Blocked by policy") == FailureClass.POLICY_VIOLATION

    def test_unknown(self):
        assert self.classifier.classify("Something unexpected happened") == FailureClass.UNKNOWN


class TestRecoveryRouter:
    def setup_method(self):
        self.router = RecoveryRouter()

    def test_optional_failure_continues(self):
        report = self.router.route("some error", ToolNecessity.OPTIONAL)
        assert report.recovery_action == RecoveryAction.CONTINUE
        assert not report.should_block

    def test_transient_retries(self):
        report = self.router.route("Connection timed out", ToolNecessity.REQUIRED, retry_count=0)
        assert report.recovery_action == RecoveryAction.RETRY
        assert report.retry_recommended

    def test_transient_exhausted_retries_blocks(self):
        report = self.router.route(
            "Connection timed out", ToolNecessity.REQUIRED, retry_count=3, max_retries=3
        )
        assert report.recovery_action == RecoveryAction.BLOCK
        assert report.should_block

    def test_policy_violation_escalates(self):
        report = self.router.route("Blocked by policy", ToolNecessity.REQUIRED)
        assert report.recovery_action == RecoveryAction.ESCALATE
        assert report.should_block

    def test_scope_violation_blocks(self):
        report = self.router.route("Outside workspace", ToolNecessity.REQUIRED)
        assert report.recovery_action == RecoveryAction.BLOCK

    def test_environmental_replans(self):
        report = self.router.route("No such file or directory", ToolNecessity.REQUIRED)
        assert report.recovery_action == RecoveryAction.REPLAN

    def test_substitute_evidence_continues(self):
        report = self.router.route(
            "Connection timed out",
            ToolNecessity.REQUIRED,
            has_substitute_evidence=True,
        )
        assert report.recovery_action == RecoveryAction.CONTINUE
        assert not report.should_block
