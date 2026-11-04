from typing import Dict, Set
from app.investigation.contracts import InvestigationStatus


class InvalidStateTransitionError(Exception):
    """Raised when an investigation transition violates the lifecycle state machine."""
    pass


class InvestigationStateMachine:
    """Formal deterministic lifecycle state machine for investigations (Phase 7)."""

    VALID_TRANSITIONS: Dict[str, Set[str]] = {
        "created": {"queued", "initializing", "investigating", "cancelled"},
        "queued": {"initializing", "investigating", "cancelled"},
        "initializing": {"investigating", "failed", "cancelled"},
        "investigating": {
            "awaiting_review",
            "paused",
            "blocked",
            "completed",
            "closed",
            "failed",
            "cancelled",
        },
        "awaiting_review": {
            "investigating",
            "completed",
            "closed",
            "cancelled",
        },
        "paused": {"investigating", "cancelled"},
        "blocked": {"investigating", "failed", "cancelled"},
        "completed": {"closed", "investigating"},
        "closed": set(),  # Terminal state
        "failed": set(),  # Terminal state
        "cancelled": set(),  # Terminal state
    }

    @classmethod
    def can_transition(cls, current_status: str, target_status: str) -> bool:
        """Checks if a transition between two statuses is permitted."""
        allowed = cls.VALID_TRANSITIONS.get(current_status.lower(), set())
        return target_status.lower() in allowed

    @classmethod
    def validate_transition(cls, current_status: str, target_status: str) -> None:
        """Validates that target_status is a valid successor of current_status, raising an error otherwise."""
        if not cls.can_transition(current_status, target_status):
            allowed = list(cls.VALID_TRANSITIONS.get(current_status.lower(), set()))
            raise InvalidStateTransitionError(
                f"Cannot transition investigation from '{current_status}' to '{target_status}'. "
                f"Allowed target states: {allowed}."
            )


state_machine_instance = InvestigationStateMachine()
