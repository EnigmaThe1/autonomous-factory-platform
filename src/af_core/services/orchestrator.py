"""Mission Orchestrator / Controller — owns mission lifecycle (ADR-004).

The orchestrator is NOT an agent. It supervises and arbitrates:
- Seeds work items from the compiled contract
- Manages the work-item state machine
- Dispatches agent tasks
- Handles approvals
- Routes recovery
- Decides completion, block, or cancellation
"""

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from af_core.models.approval import ApprovalRequest
from af_core.models.enums import (
    AgentRole,
    ApprovalStatus,
    EventSeverity,
    MissionStatus,
    WorkItemStatus,
)
from af_core.models.event import MissionEvent
from af_core.models.mission import Mission
from af_core.models.work_item import WorkItem
from af_core.services.event_bus import event_bus

logger = logging.getLogger(__name__)


class Orchestrator:
    """Central mission controller — supervises the full mission lifecycle."""

    async def start_mission(self, mission: Mission, db: AsyncSession) -> Mission:
        """Transition a compiled mission to queued and seed initial work items."""
        if mission.status != MissionStatus.COMPILED:
            raise ValueError(
                f"Cannot start mission in {mission.status.value} state; must be compiled"
            )

        # Seed work items from the compiled contract
        work_items = self._seed_work_items(mission)
        for wi in work_items:
            db.add(wi)

        mission.status = MissionStatus.QUEUED
        await db.flush()

        await self._emit_event(
            db,
            mission.id,
            "orchestrator",
            "mission.queued",
            {"work_item_count": len(work_items)},
        )

        await event_bus.emit(
            "mission.queued",
            {
                "mission_id": mission.id,
                "status": mission.status.value,
                "work_item_count": len(work_items),
            },
        )

        return mission

    async def advance_mission(self, mission: Mission, db: AsyncSession) -> Mission:
        """Evaluate mission state and advance to the next phase.

        This is the core orchestration loop step:
        1. Find ready work items
        2. Check for blockers
        3. Determine if mission is complete
        """
        query = select(WorkItem).where(WorkItem.mission_id == mission.id)
        result = await db.execute(query)
        work_items = list(result.scalars().all())

        if not work_items:
            return mission

        # Check for pending approvals
        approval_query = select(ApprovalRequest).where(
            ApprovalRequest.mission_id == mission.id,
            ApprovalRequest.status == ApprovalStatus.PENDING,
        )
        approval_result = await db.execute(approval_query)
        pending_approvals = list(approval_result.scalars().all())

        if pending_approvals:
            if mission.status != MissionStatus.BLOCKED:
                mission.status = MissionStatus.BLOCKED
                await self._emit_event(
                    db,
                    mission.id,
                    "orchestrator",
                    "mission.blocked",
                    {"reason": "pending_approval", "count": len(pending_approvals)},
                )
            return mission

        # Update dependency readiness
        completed_ids = {wi.id for wi in work_items if wi.status == WorkItemStatus.COMPLETED}
        for wi in work_items:
            if wi.status == WorkItemStatus.PENDING:
                deps = wi.dependencies or []
                if all(dep_id in completed_ids for dep_id in deps):
                    wi.status = WorkItemStatus.READY

        # Check completion
        all_terminal = all(
            wi.status in (WorkItemStatus.COMPLETED, WorkItemStatus.SKIPPED) for wi in work_items
        )
        any_failed = any(wi.status == WorkItemStatus.FAILED for wi in work_items)
        any_blocked = any(wi.status == WorkItemStatus.BLOCKED for wi in work_items)

        if all_terminal:
            mission.status = MissionStatus.COMPLETED
            mission.completed_at = datetime.now(UTC)
            mission.final_verdict = "completed"
            await self._emit_event(
                db,
                mission.id,
                "orchestrator",
                "mission.completed",
                {},
            )
            await event_bus.emit(
                "mission.completed",
                {
                    "mission_id": mission.id,
                    "status": "completed",
                },
            )
        elif any_failed:
            mission.status = MissionStatus.FAILED
            mission.final_verdict = "failed"
            failed_items = [wi.title for wi in work_items if wi.status == WorkItemStatus.FAILED]
            await self._emit_event(
                db,
                mission.id,
                "orchestrator",
                "mission.failed",
                {"failed_items": failed_items},
            )
        elif any_blocked:
            mission.status = MissionStatus.BLOCKED
        elif mission.status == MissionStatus.QUEUED:
            # Transition to running if there are ready items
            ready_items = [wi for wi in work_items if wi.status == WorkItemStatus.READY]
            if ready_items:
                mission.status = MissionStatus.RUNNING
                await self._emit_event(
                    db,
                    mission.id,
                    "orchestrator",
                    "mission.running",
                    {"ready_count": len(ready_items)},
                )

        await db.flush()
        return mission

    async def get_next_work_item(self, mission_id: str, db: AsyncSession) -> WorkItem | None:
        """Get the next ready work item for dispatch."""
        query = (
            select(WorkItem)
            .where(
                WorkItem.mission_id == mission_id,
                WorkItem.status == WorkItemStatus.READY,
            )
            .order_by(WorkItem.created_at)
            .limit(1)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def start_work_item(self, work_item: WorkItem, db: AsyncSession) -> WorkItem:
        """Mark a work item as running."""
        if work_item.status != WorkItemStatus.READY:
            raise ValueError(f"Work item not ready: {work_item.status.value}")

        work_item.status = WorkItemStatus.RUNNING
        await db.flush()

        await self._emit_event(
            db,
            work_item.mission_id,
            "orchestrator",
            "work_item.started",
            {"work_item_id": work_item.id, "role": work_item.role.value},
        )
        return work_item

    async def complete_work_item(
        self, work_item: WorkItem, output: dict, db: AsyncSession
    ) -> WorkItem:
        """Mark a work item as completed with output."""
        work_item.status = WorkItemStatus.COMPLETED
        work_item.output = output
        await db.flush()

        await self._emit_event(
            db,
            work_item.mission_id,
            "orchestrator",
            "work_item.completed",
            {"work_item_id": work_item.id, "role": work_item.role.value},
        )
        return work_item

    async def fail_work_item(self, work_item: WorkItem, reason: str, db: AsyncSession) -> WorkItem:
        """Mark a work item as failed."""
        if work_item.retry_count < work_item.max_retries:
            work_item.retry_count += 1
            work_item.status = WorkItemStatus.READY
            await self._emit_event(
                db,
                work_item.mission_id,
                "orchestrator",
                "work_item.retrying",
                {
                    "work_item_id": work_item.id,
                    "retry_count": work_item.retry_count,
                    "reason": reason,
                },
            )
        else:
            work_item.status = WorkItemStatus.FAILED
            work_item.output = {"error": reason}
            await self._emit_event(
                db,
                work_item.mission_id,
                "orchestrator",
                "work_item.failed",
                {"work_item_id": work_item.id, "reason": reason},
            )

        await db.flush()
        return work_item

    async def request_approval(
        self,
        mission_id: str,
        reason: str,
        db: AsyncSession,
        work_item_id: str | None = None,
        context: str | None = None,
    ) -> ApprovalRequest:
        """Create an approval request that blocks the mission."""
        approval = ApprovalRequest(
            mission_id=mission_id,
            work_item_id=work_item_id,
            reason=reason,
            context=context,
        )
        db.add(approval)
        await db.flush()

        await self._emit_event(
            db,
            mission_id,
            "orchestrator",
            "approval.requested",
            {"approval_id": approval.id, "reason": reason},
        )

        await event_bus.emit(
            "approval.requested",
            {
                "mission_id": mission_id,
                "approval_id": approval.id,
                "reason": reason,
            },
        )

        return approval

    def _seed_work_items(self, mission: Mission) -> list[WorkItem]:
        """Create initial work items from the compiled contract.

        The canonical five-agent flow: Plan -> Research -> Implement -> Review -> Validate.
        Dependencies enforce ordering.
        """
        contract = mission.contract
        if not contract:
            return []

        objective = contract.normalized_objective
        items = []

        plan = WorkItem(
            mission_id=mission.id,
            role=AgentRole.PLANNER,
            title=f"Plan: {objective}",
            status=WorkItemStatus.READY,
            step_contract={"objective": objective, "scope": contract.normalized_scope},
            expected_deliverables=["execution_plan"],
            dependencies=[],
        )
        items.append(plan)

        research = WorkItem(
            mission_id=mission.id,
            role=AgentRole.RESEARCHER,
            title=f"Research: {objective}",
            status=WorkItemStatus.PENDING,
            step_contract={"objective": objective, "inputs": contract.normalized_inputs},
            expected_deliverables=["research_findings"],
            dependencies=[],  # Will be set after flush
        )
        items.append(research)

        implement = WorkItem(
            mission_id=mission.id,
            role=AgentRole.IMPLEMENTER,
            title=f"Implement: {objective}",
            status=WorkItemStatus.PENDING,
            step_contract={
                "objective": objective,
                "outputs": contract.normalized_outputs,
                "scope": contract.normalized_scope,
            },
            expected_deliverables=["implementation_artifacts"],
            dependencies=[],
        )
        items.append(implement)

        review = WorkItem(
            mission_id=mission.id,
            role=AgentRole.REVIEWER,
            title=f"Review: {objective}",
            status=WorkItemStatus.PENDING,
            step_contract={
                "objective": objective,
                "success_criteria": contract.success_criteria,
            },
            expected_deliverables=["review_report"],
            dependencies=[],
        )
        items.append(review)

        validate = WorkItem(
            mission_id=mission.id,
            role=AgentRole.VALIDATOR,
            title=f"Validate: {objective}",
            status=WorkItemStatus.PENDING,
            step_contract={
                "objective": objective,
                "success_criteria": contract.success_criteria,
            },
            expected_deliverables=["validation_verdict"],
            dependencies=[],
        )
        items.append(validate)

        return items

    async def link_work_item_dependencies(self, mission_id: str, db: AsyncSession) -> None:
        """Set up sequential dependencies: Plan -> Research -> Implement -> Review -> Validate."""
        query = (
            select(WorkItem).where(WorkItem.mission_id == mission_id).order_by(WorkItem.created_at)
        )
        result = await db.execute(query)
        items = list(result.scalars().all())

        role_order = [
            AgentRole.PLANNER,
            AgentRole.RESEARCHER,
            AgentRole.IMPLEMENTER,
            AgentRole.REVIEWER,
            AgentRole.VALIDATOR,
        ]
        by_role = {wi.role: wi for wi in items}

        for i in range(1, len(role_order)):
            current_role = role_order[i]
            prev_role = role_order[i - 1]
            if current_role in by_role and prev_role in by_role:
                by_role[current_role].dependencies = [by_role[prev_role].id]

        await db.flush()

    async def _emit_event(
        self,
        db: AsyncSession,
        mission_id: str,
        component: str,
        event_type: str,
        payload: dict,
        severity: EventSeverity = EventSeverity.INFO,
    ) -> None:
        event = MissionEvent(
            mission_id=mission_id,
            component=component,
            event_type=event_type,
            severity=severity,
            payload=payload,
        )
        db.add(event)
        await db.flush()
