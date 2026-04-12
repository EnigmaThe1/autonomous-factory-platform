"""Domain enumerations — canonical status values per the blueprint state model."""

import enum


class MissionStatus(enum.StrEnum):
    """Mission lifecycle states."""

    PENDING = "pending"
    COMPILING = "compiling"
    COMPILED = "compiled"
    QUEUED = "queued"
    RUNNING = "running"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkItemStatus(enum.StrEnum):
    """Work-item lifecycle states."""

    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class AgentRole(enum.StrEnum):
    """The canonical five-agent model (ADR-003)."""

    PLANNER = "planner"
    RESEARCHER = "researcher"
    IMPLEMENTER = "implementer"
    REVIEWER = "reviewer"
    VALIDATOR = "validator"


class ToolNecessity(enum.StrEnum):
    """How necessary a tool invocation is for evidence sufficiency (ADR-006)."""

    REQUIRED = "required"
    PREFERRED = "preferred"
    OPTIONAL = "optional"


class ToolCategory(enum.StrEnum):
    """Tool risk categories for isolation policy."""

    READ_ONLY = "read_only"
    BOUNDED_WRITE = "bounded_write"
    VALIDATION = "validation"
    TERMINAL = "terminal"
    NETWORK = "network"
    PROTECTED = "protected"


class FailureClass(enum.StrEnum):
    """Failure classification for recovery routing."""

    TRANSIENT = "transient"
    ENVIRONMENTAL = "environmental"
    LOGICAL = "logical"
    SCOPE_VIOLATION = "scope_violation"
    POLICY_VIOLATION = "policy_violation"
    UNKNOWN = "unknown"


class RecoveryAction(enum.StrEnum):
    """Recovery decisions after failure classification."""

    CONTINUE = "continue"
    RETRY = "retry"
    REPLAN = "replan"
    BLOCK = "block"
    ESCALATE = "escalate"


class ApprovalStatus(enum.StrEnum):
    """Approval request states."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class EventSeverity(enum.StrEnum):
    """Event severity for observability."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class FindingSeverity(enum.StrEnum):
    """Compiler finding severity."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    BLOCKING = "blocking"
