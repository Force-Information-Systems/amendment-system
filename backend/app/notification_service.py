"""
Notification Service for QA system.

Handles creation of in-app notifications and triggering email notifications.
"""

from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from .models import Amendment, QADefect, QATestExecution, Employee
from . import crud, schemas
from .email_service import email_service


class NotificationService:
    """
    Service for creating and managing QA notifications.

    Creates both in-app notifications and sends email notifications.
    """

    @staticmethod
    def notify_qa_assigned(
        db: Session,
        amendment: Amendment,
        assigned_to: Employee,
        assigned_by: Employee,
    ) -> bool:
        """
        Send notification when QA is assigned to a tester.

        Args:
            db: Database session
            amendment: Amendment object
            assigned_to: Employee who was assigned
            assigned_by: Employee who made the assignment

        Returns:
            bool: True if notification created successfully
        """
        try:
            # Create in-app notification
            notification = schemas.QANotificationCreate(
                employee_id=assigned_to.employee_id,
                notification_type="QA Assigned",
                title=f"QA Assigned: {amendment.amendment_reference}",
                message=f"You have been assigned to test amendment {amendment.amendment_reference}. Assigned by {assigned_by.employee_name}.",
                amendment_id=amendment.amendment_id,
                defect_id=None,
                is_email_sent=False,
            )

            db_notification = crud.create_notification(db, notification)

            # Send email if enabled and employee has email
            if assigned_to.email:
                email_sent = email_service.send_qa_assigned_email(
                    employee_email=assigned_to.email,
                    employee_name=assigned_to.employee_name,
                    amendment_reference=amendment.amendment_reference,
                    amendment_description=amendment.description,
                )

                # Update notification to mark email as sent
                if email_sent:
                    db_notification.is_email_sent = True
                    db.commit()

            return True

        except Exception as e:
            print(f"Error creating QA assignment notification: {e}")
            return False

    @staticmethod
    def notify_status_changed(
        db: Session,
        amendment: Amendment,
        old_status: str,
        new_status: str,
        changed_by: Optional[Employee] = None,
    ) -> bool:
        """
        Send notification when QA status changes.

        Args:
            db: Database session
            amendment: Amendment object
            old_status: Previous QA status
            new_status: New QA status
            changed_by: Employee who changed the status

        Returns:
            bool: True if notification created successfully
        """
        # Don't notify if no QA tester assigned
        if not amendment.qa_assigned_id:
            return False

        try:
            # Create in-app notification
            notification = schemas.QANotificationCreate(
                employee_id=amendment.qa_assigned_id,
                notification_type="Status Changed",
                title=f"QA Status Changed: {amendment.amendment_reference}",
                message=f"Status changed from {old_status} to {new_status}" + (
                    f" by {changed_by.employee_name}" if changed_by else ""
                ),
                amendment_id=amendment.amendment_id,
                defect_id=None,
                is_email_sent=False,
            )

            db_notification = crud.create_notification(db, notification)

            # Get assigned tester
            assigned_tester = db.query(Employee).filter(
                Employee.employee_id == amendment.qa_assigned_id
            ).first()

            # Send email if enabled and employee has email
            if assigned_tester and assigned_tester.email:
                email_sent = email_service.send_qa_status_changed_email(
                    employee_email=assigned_tester.email,
                    employee_name=assigned_tester.employee_name,
                    amendment_reference=amendment.amendment_reference,
                    old_status=old_status,
                    new_status=new_status,
                )

                # Update notification to mark email as sent
                if email_sent:
                    db_notification.is_email_sent = True
                    db.commit()

            return True

        except Exception as e:
            print(f"Error creating status change notification: {e}")
            return False

    @staticmethod
    def notify_test_failed(
        db: Session,
        execution: QATestExecution,
    ) -> bool:
        """
        Send notification when a test fails.

        Args:
            db: Database session
            execution: Test execution object

        Returns:
            bool: True if notification created successfully
        """
        # Get amendment
        amendment = execution.amendment

        # Notify QA tester if assigned
        if not amendment.qa_assigned_id:
            return False

        try:
            # Create in-app notification
            notification = schemas.QANotificationCreate(
                employee_id=amendment.qa_assigned_id,
                notification_type="Test Failed",
                title=f"Test Failed: {execution.test_case.test_case_number}",
                message=f"Test case {execution.test_case.test_case_number} failed for amendment {amendment.amendment_reference}",
                amendment_id=amendment.amendment_id,
                defect_id=None,
                is_email_sent=False,
            )

            crud.create_notification(db, notification)

            return True

        except Exception as e:
            print(f"Error creating test failed notification: {e}")
            return False

    @staticmethod
    def notify_defect_created(
        db: Session,
        defect: QADefect,
    ) -> bool:
        """
        Send notification when a defect is created.

        Args:
            db: Database session
            defect: Defect object

        Returns:
            bool: True if notification created successfully
        """
        # Notify assigned developer if assigned
        if not defect.assigned_to_id:
            return False

        try:
            # Create in-app notification
            notification = schemas.QANotificationCreate(
                employee_id=defect.assigned_to_id,
                notification_type="Defect Created",
                title=f"New Defect: {defect.defect_number}",
                message=f"Defect {defect.defect_number} ({defect.severity}) has been assigned to you: {defect.title}",
                amendment_id=defect.amendment_id,
                defect_id=defect.defect_id,
                is_email_sent=False,
            )

            db_notification = crud.create_notification(db, notification)

            # Get amendment and assigned developer
            amendment = defect.amendment
            assigned_developer = defect.assigned_to

            # Send email if enabled and developer has email
            if assigned_developer and assigned_developer.email:
                email_sent = email_service.send_defect_created_email(
                    developer_email=assigned_developer.email,
                    developer_name=assigned_developer.employee_name,
                    defect_number=defect.defect_number,
                    defect_title=defect.title,
                    severity=defect.severity,
                    amendment_reference=amendment.amendment_reference,
                )

                # Update notification to mark email as sent
                if email_sent:
                    db_notification.is_email_sent = True
                    db.commit()

            return True

        except Exception as e:
            print(f"Error creating defect notification: {e}")
            return False

    @staticmethod
    def check_and_notify_overdue(db: Session) -> int:
        """
        Check for overdue QA tasks and send notifications.

        This should be run as a scheduled task (e.g., daily cron job).

        Args:
            db: Database session

        Returns:
            int: Number of notifications sent
        """
        # Find overdue amendments
        overdue_amendments = crud.check_overdue_qa(db)

        if not overdue_amendments:
            return 0

        # Group by QA tester
        amendments_by_tester = {}
        for amendment in overdue_amendments:
            if not amendment.qa_assigned_id:
                continue

            if amendment.qa_assigned_id not in amendments_by_tester:
                amendments_by_tester[amendment.qa_assigned_id] = []

            amendments_by_tester[amendment.qa_assigned_id].append(amendment)

        notifications_sent = 0

        # Send notification to each tester
        for tester_id, amendments in amendments_by_tester.items():
            tester = db.query(Employee).filter(Employee.employee_id == tester_id).first()
            if not tester:
                continue

            # Create in-app notification for each overdue amendment
            for amendment in amendments:
                try:
                    notification = schemas.QANotificationCreate(
                        employee_id=tester_id,
                        notification_type="Overdue",
                        title=f"Overdue QA: {amendment.amendment_reference}",
                        message=f"Amendment {amendment.amendment_reference} is overdue. Due date was {amendment.qa_due_date.strftime('%Y-%m-%d')}.",
                        amendment_id=amendment.amendment_id,
                        defect_id=None,
                        is_email_sent=False,
                    )

                    crud.create_notification(db, notification)
                    notifications_sent += 1

                except Exception as e:
                    print(f"Error creating overdue notification for {amendment.amendment_reference}: {e}")

            # Send one email summary to tester if they have email
            if tester.email:
                amendments_data = [
                    {
                        "reference": a.amendment_reference,
                        "description": a.description[:100] + "..." if len(a.description) > 100 else a.description,
                        "due_date": a.qa_due_date.strftime("%Y-%m-%d %H:%M") if a.qa_due_date else "N/A",
                    }
                    for a in amendments
                ]

                email_service.send_qa_overdue_email(
                    employee_email=tester.email,
                    employee_name=tester.employee_name,
                    amendments=amendments_data,
                )

        return notifications_sent

    @staticmethod
    def notify_sla_breach(
        db: Session,
        amendment: Amendment,
    ) -> bool:
        """
        Send notification when SLA is breached.

        Args:
            db: Database session
            amendment: Amendment object

        Returns:
            bool: True if notification created successfully
        """
        # Notify QA tester if assigned
        if not amendment.qa_assigned_id:
            return False

        try:
            # Create in-app notification
            notification = schemas.QANotificationCreate(
                employee_id=amendment.qa_assigned_id,
                notification_type="SLA Breach",
                title=f"SLA Breach: {amendment.amendment_reference}",
                message=f"Amendment {amendment.amendment_reference} has breached the SLA ({amendment.qa_sla_hours} hours)",
                amendment_id=amendment.amendment_id,
                defect_id=None,
                is_email_sent=False,
            )

            crud.create_notification(db, notification)

            return True

        except Exception as e:
            print(f"Error creating SLA breach notification: {e}")
            return False


# Global notification service instance
notification_service = NotificationService()
