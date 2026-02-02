"""
QA Workflow Validation Engine.

This module enforces strict QA workflow rules and state transitions.
Ensures quality gates are met before status changes.
"""

from typing import Tuple, List, Optional
from .models import Amendment, QAStatus


class QAWorkflowValidator:
    """
    Validator for QA workflow state transitions and business rules.

    Enforces:
    - Valid status transitions (no skipping steps)
    - Completion requirements (checklist, tests, etc.)
    - Assignment requirements
    """

    # Valid status transitions
    VALID_TRANSITIONS = {
        QAStatus.NOT_STARTED: [QAStatus.ASSIGNED],
        QAStatus.ASSIGNED: [QAStatus.IN_TESTING],
        QAStatus.IN_TESTING: [QAStatus.BLOCKED, QAStatus.PASSED, QAStatus.FAILED],
        QAStatus.BLOCKED: [QAStatus.IN_TESTING, QAStatus.FAILED],
        QAStatus.PASSED: [QAStatus.IN_TESTING],  # Allow re-testing if needed
        QAStatus.FAILED: [QAStatus.IN_TESTING],  # Allow re-testing after fixes
    }

    @staticmethod
    def can_transition(from_status: str, to_status: str) -> bool:
        """
        Check if a status transition is allowed.

        Args:
            from_status: Current QA status
            to_status: Desired QA status

        Returns:
            bool: True if transition is allowed
        """
        # Convert strings to enums
        try:
            from_enum = QAStatus(from_status)
            to_enum = QAStatus(to_status)
        except ValueError:
            return False

        # Allow staying in same status
        if from_enum == to_enum:
            return True

        # Check if transition is valid
        allowed_transitions = QAWorkflowValidator.VALID_TRANSITIONS.get(from_enum, [])
        return to_enum in allowed_transitions

    @staticmethod
    def validate_transition(
        amendment: Amendment, new_status: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a QA status transition with business rules.

        Args:
            amendment: Amendment object
            new_status: Desired new status

        Returns:
            Tuple of (is_valid, error_message)
        """
        current_status = amendment.qa_status

        # Check basic transition validity
        if not QAWorkflowValidator.can_transition(current_status, new_status):
            return (
                False,
                f"Invalid status transition: {current_status} → {new_status}. "
                f"Follow the workflow: Not Started → Assigned → In Testing → Passed/Failed/Blocked",
            )

        # Validate specific transition requirements
        error = QAWorkflowValidator._validate_transition_requirements(
            amendment, new_status
        )
        if error:
            return (False, error)

        return (True, None)

    @staticmethod
    def _validate_transition_requirements(
        amendment: Amendment, new_status: str
    ) -> Optional[str]:
        """
        Validate specific requirements for each status transition.

        Args:
            amendment: Amendment object
            new_status: Desired new status

        Returns:
            Error message if validation fails, None if successful
        """
        new_status_enum = QAStatus(new_status)

        # ASSIGNED: Must have a QA tester assigned
        if new_status_enum == QAStatus.ASSIGNED:
            if not amendment.qa_assigned_id:
                return "Cannot assign QA: No QA tester assigned. Please assign a QA tester first."

        # IN_TESTING: Must be assigned and have QA assigned date
        if new_status_enum == QAStatus.IN_TESTING:
            if not amendment.qa_assigned_id:
                return "Cannot start testing: No QA tester assigned."
            if not amendment.qa_assigned_date:
                return "Cannot start testing: QA assignment date not set."

        # PASSED: Must complete checklist and have testing done
        if new_status_enum == QAStatus.PASSED:
            blockers = QAWorkflowValidator._check_completion_blockers(amendment)
            if blockers:
                return (
                    f"Cannot mark as Passed. The following requirements must be met:\n"
                    + "\n".join(f"  • {blocker}" for blocker in blockers)
                )

        # BLOCKED: Must have a reason
        if new_status_enum == QAStatus.BLOCKED:
            if not amendment.qa_blocked_reason or not amendment.qa_blocked_reason.strip():
                return "Cannot mark as Blocked: Please provide a reason for blocking."

        return None

    @staticmethod
    def _check_completion_blockers(amendment: Amendment) -> List[str]:
        """
        Check for any blockers preventing QA completion.

        Args:
            amendment: Amendment object

        Returns:
            List of blocker messages
        """
        blockers = []

        # Check checklist completion
        if not amendment.qa_test_plan_check:
            blockers.append("Test plan must be checked")

        if not amendment.qa_test_release_notes_check:
            blockers.append("Release notes must be checked")

        # Check if QA was actually started
        if not amendment.qa_started_date:
            blockers.append("QA testing must be started before marking as Passed")

        # Check if at least some testing was done (has QA notes or test executions)
        # This would require checking test_executions relationship
        # For now, we'll check if QA notes exist
        if not amendment.qa_notes or not amendment.qa_notes.strip():
            blockers.append(
                "QA notes are required (document what was tested and results)"
            )

        return blockers

    @staticmethod
    def can_complete_qa(amendment: Amendment) -> Tuple[bool, List[str]]:
        """
        Check if QA can be marked as complete (Passed).

        Args:
            amendment: Amendment object

        Returns:
            Tuple of (can_complete, list of blockers)
        """
        blockers = QAWorkflowValidator._check_completion_blockers(amendment)
        return (len(blockers) == 0, blockers)

    @staticmethod
    def get_next_allowed_statuses(current_status: str) -> List[str]:
        """
        Get list of allowed next statuses from current status.

        Args:
            current_status: Current QA status

        Returns:
            List of allowed status strings
        """
        try:
            status_enum = QAStatus(current_status)
        except ValueError:
            return []

        allowed = QAWorkflowValidator.VALID_TRANSITIONS.get(status_enum, [])
        return [status.value for status in allowed]

    @staticmethod
    def get_workflow_help() -> dict:
        """
        Get human-readable workflow documentation.

        Returns:
            dict: Workflow documentation
        """
        return {
            "workflow": "Not Started → Assigned → In Testing → Passed/Failed/Blocked",
            "status_descriptions": {
                "Not Started": "QA has not been initiated",
                "Assigned": "QA tester has been assigned",
                "In Testing": "QA testing is actively in progress",
                "Blocked": "QA is blocked and cannot proceed",
                "Passed": "QA testing completed successfully",
                "Failed": "QA testing found issues, changes needed",
            },
            "requirements": {
                "Assigned": ["Must have qa_assigned_id set"],
                "In Testing": ["Must be assigned", "Must have qa_assigned_date"],
                "Passed": [
                    "Test plan must be checked",
                    "Release notes must be checked",
                    "QA must be started (qa_started_date)",
                    "QA notes must be provided",
                ],
                "Blocked": ["Must provide qa_blocked_reason"],
            },
            "allowed_transitions": {
                status.value: [s.value for s in transitions]
                for status, transitions in QAWorkflowValidator.VALID_TRANSITIONS.items()
            },
        }

    @staticmethod
    def validate_qa_assignment(
        amendment: Amendment, qa_assigned_id: Optional[int]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate QA assignment.

        Args:
            amendment: Amendment object
            qa_assigned_id: Employee ID to assign

        Returns:
            Tuple of (is_valid, error_message)
        """
        if qa_assigned_id is None:
            # Unassigning is allowed if not in testing or completed
            if amendment.qa_status in ["In Testing", "Passed"]:
                return (
                    False,
                    f"Cannot unassign QA: Amendment is in '{amendment.qa_status}' status",
                )

        return (True, None)

    @staticmethod
    def validate_checklist_update(
        amendment: Amendment, field_name: str, new_value: bool
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate checklist field updates.

        Args:
            amendment: Amendment object
            field_name: Checklist field name
            new_value: New value for the field

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Allow updating checklist at any time during In Testing or earlier
        # Don't allow unchecking after Passed
        if amendment.qa_status == "Passed" and not new_value:
            return (
                False,
                f"Cannot uncheck {field_name}: QA has already passed",
            )

        return (True, None)

    @staticmethod
    def validate_defect_resolution(
        amendment: Amendment, has_open_defects: bool
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate if QA can be marked as passed with open defects.

        Args:
            amendment: Amendment object
            has_open_defects: Whether there are open defects

        Returns:
            Tuple of (is_valid, warning_message)
        """
        if has_open_defects and amendment.qa_status == "Passed":
            return (
                False,
                "Warning: There are open defects. Consider resolving all defects before marking QA as Passed, "
                "or document why defects are acceptable in QA notes.",
            )

        return (True, None)


# Convenience functions for direct use

def validate_qa_status_change(
    amendment: Amendment, new_status: str
) -> Tuple[bool, Optional[str]]:
    """
    Convenience function to validate a QA status change.

    Args:
        amendment: Amendment object
        new_status: Desired new status

    Returns:
        Tuple of (is_valid, error_message)
    """
    return QAWorkflowValidator.validate_transition(amendment, new_status)


def can_mark_qa_passed(amendment: Amendment) -> Tuple[bool, List[str]]:
    """
    Convenience function to check if QA can be marked as passed.

    Args:
        amendment: Amendment object

    Returns:
        Tuple of (can_pass, list of blockers)
    """
    return QAWorkflowValidator.can_complete_qa(amendment)


def get_allowed_qa_statuses(current_status: str) -> List[str]:
    """
    Convenience function to get allowed next statuses.

    Args:
        current_status: Current QA status

    Returns:
        List of allowed status strings
    """
    return QAWorkflowValidator.get_next_allowed_statuses(current_status)
