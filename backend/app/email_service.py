"""
Email Service for sending QA notifications.

Supports SMTP email sending for:
- QA assignment notifications
- Status change notifications
- Overdue notifications
- Defect notifications
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from datetime import datetime


class EmailService:
    """
    Service for sending email notifications.

    Configuration via environment variables:
    - EMAIL_ENABLED: Set to 'true' to enable email sending
    - SMTP_SERVER: SMTP server address (e.g., smtp.gmail.com)
    - SMTP_PORT: SMTP server port (e.g., 587)
    - SMTP_USERNAME: SMTP username
    - SMTP_PASSWORD: SMTP password or app password
    - FROM_EMAIL: Email address to send from
    """

    def __init__(self):
        self.enabled = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@amendmentsystem.com")

    def is_enabled(self) -> bool:
        """Check if email service is enabled and configured."""
        return (
            self.enabled
            and self.smtp_server
            and self.smtp_username
            and self.smtp_password
        )

    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
    ) -> bool:
        """
        Send an email.

        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            body_html: HTML body content
            body_text: Optional plain text body (fallback)

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.is_enabled():
            print("Email service is not enabled or configured")
            return False

        if not to_emails:
            print("No recipients specified")
            return False

        # Filter out None/empty emails
        to_emails = [email for email in to_emails if email]
        if not to_emails:
            print("No valid email addresses")
            return False

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = ", ".join(to_emails)
            msg["Date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")

            # Add plain text and HTML parts
            if body_text:
                part1 = MIMEText(body_text, "plain")
                msg.attach(part1)

            part2 = MIMEText(body_html, "html")
            msg.attach(part2)

            # Connect to SMTP server and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            print(f"✓ Email sent to {', '.join(to_emails)}: {subject}")
            return True

        except Exception as e:
            print(f"✗ Failed to send email: {e}")
            return False

    def send_qa_assigned_email(
        self, employee_email: str, employee_name: str, amendment_reference: str, amendment_description: str
    ) -> bool:
        """
        Send QA assignment notification email.

        Args:
            employee_email: QA tester's email
            employee_name: QA tester's name
            amendment_reference: Amendment reference number
            amendment_description: Amendment description

        Returns:
            bool: True if sent successfully
        """
        subject = f"QA Assignment: {amendment_reference}"

        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #2563eb;">QA Assignment Notification</h2>

            <p>Hi {employee_name},</p>

            <p>You have been assigned to test the following amendment:</p>

            <div style="background-color: #f3f4f6; padding: 15px; border-left: 4px solid #2563eb; margin: 20px 0;">
                <p style="margin: 5px 0;"><strong>Amendment:</strong> {amendment_reference}</p>
                <p style="margin: 5px 0;"><strong>Description:</strong> {amendment_description}</p>
            </div>

            <p>Please review the amendment and begin testing when ready.</p>

            <p>
                <a href="http://localhost:3000/amendments/{amendment_reference}"
                   style="background-color: #2563eb; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    View Amendment
                </a>
            </p>

            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">

            <p style="font-size: 12px; color: #6b7280;">
                This is an automated notification from the Amendment Tracking System.
            </p>
        </body>
        </html>
        """

        body_text = f"""
QA Assignment Notification

Hi {employee_name},

You have been assigned to test the following amendment:

Amendment: {amendment_reference}
Description: {amendment_description}

Please review the amendment and begin testing when ready.

View Amendment: http://localhost:3000/amendments/{amendment_reference}

---
This is an automated notification from the Amendment Tracking System.
        """

        return self.send_email([employee_email], subject, body_html, body_text)

    def send_qa_status_changed_email(
        self,
        employee_email: str,
        employee_name: str,
        amendment_reference: str,
        old_status: str,
        new_status: str,
    ) -> bool:
        """
        Send QA status change notification email.

        Args:
            employee_email: QA tester's email
            employee_name: QA tester's name
            amendment_reference: Amendment reference number
            old_status: Previous QA status
            new_status: New QA status

        Returns:
            bool: True if sent successfully
        """
        subject = f"QA Status Changed: {amendment_reference} → {new_status}"

        # Choose emoji based on status
        status_emoji = {
            "Assigned": "📋",
            "In Testing": "🧪",
            "Blocked": "🚫",
            "Passed": "✅",
            "Failed": "❌",
        }.get(new_status, "📝")

        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #2563eb;">QA Status Changed</h2>

            <p>Hi {employee_name},</p>

            <p>The QA status for amendment <strong>{amendment_reference}</strong> has been updated:</p>

            <div style="background-color: #f3f4f6; padding: 15px; border-left: 4px solid #2563eb; margin: 20px 0;">
                <p style="margin: 5px 0;">
                    <strong>Status Change:</strong>
                    <span style="color: #6b7280;">{old_status}</span>
                    →
                    <span style="color: #2563eb; font-weight: bold;">{status_emoji} {new_status}</span>
                </p>
            </div>

            <p>
                <a href="http://localhost:3000/amendments/{amendment_reference}"
                   style="background-color: #2563eb; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    View Amendment
                </a>
            </p>

            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">

            <p style="font-size: 12px; color: #6b7280;">
                This is an automated notification from the Amendment Tracking System.
            </p>
        </body>
        </html>
        """

        body_text = f"""
QA Status Changed

Hi {employee_name},

The QA status for amendment {amendment_reference} has been updated:

Status Change: {old_status} → {new_status}

View Amendment: http://localhost:3000/amendments/{amendment_reference}

---
This is an automated notification from the Amendment Tracking System.
        """

        return self.send_email([employee_email], subject, body_html, body_text)

    def send_qa_overdue_email(
        self, employee_email: str, employee_name: str, amendments: List[dict]
    ) -> bool:
        """
        Send overdue QA notification email.

        Args:
            employee_email: QA tester's email
            employee_name: QA tester's name
            amendments: List of overdue amendments (dicts with reference, description, due_date)

        Returns:
            bool: True if sent successfully
        """
        if not amendments:
            return False

        count = len(amendments)
        subject = f"⚠️ Overdue QA Notifications ({count} amendment{'s' if count > 1 else ''})"

        # Build list of overdue amendments
        amendments_html = ""
        amendments_text = ""

        for amend in amendments:
            amendments_html += f"""
            <div style="background-color: #fff; padding: 10px; margin: 10px 0; border-left: 3px solid #ef4444;">
                <p style="margin: 5px 0;"><strong>{amend['reference']}</strong></p>
                <p style="margin: 5px 0; font-size: 14px; color: #6b7280;">{amend['description']}</p>
                <p style="margin: 5px 0; font-size: 12px; color: #ef4444;">Due: {amend['due_date']}</p>
            </div>
            """

            amendments_text += f"\n- {amend['reference']}: {amend['description']}\n  Due: {amend['due_date']}\n"

        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #ef4444;">⚠️ Overdue QA Notifications</h2>

            <p>Hi {employee_name},</p>

            <p>You have <strong>{count}</strong> overdue QA assignment{'s' if count > 1 else ''}:</p>

            <div style="background-color: #fef2f2; padding: 15px; border-left: 4px solid #ef4444; margin: 20px 0;">
                {amendments_html}
            </div>

            <p>Please review and prioritize these amendments.</p>

            <p>
                <a href="http://localhost:3000/qa/dashboard"
                   style="background-color: #ef4444; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    View QA Dashboard
                </a>
            </p>

            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">

            <p style="font-size: 12px; color: #6b7280;">
                This is an automated notification from the Amendment Tracking System.
            </p>
        </body>
        </html>
        """

        body_text = f"""
⚠️ Overdue QA Notifications

Hi {employee_name},

You have {count} overdue QA assignment{'s' if count > 1 else ''}:
{amendments_text}

Please review and prioritize these amendments.

View QA Dashboard: http://localhost:3000/qa/dashboard

---
This is an automated notification from the Amendment Tracking System.
        """

        return self.send_email([employee_email], subject, body_html, body_text)

    def send_defect_created_email(
        self,
        developer_email: str,
        developer_name: str,
        defect_number: str,
        defect_title: str,
        severity: str,
        amendment_reference: str,
    ) -> bool:
        """
        Send defect creation notification email.

        Args:
            developer_email: Developer's email
            developer_name: Developer's name
            defect_number: Defect number
            defect_title: Defect title
            severity: Defect severity
            amendment_reference: Amendment reference

        Returns:
            bool: True if sent successfully
        """
        subject = f"New Defect: {defect_number} - {severity}"

        # Severity colors
        severity_color = {
            "Critical": "#dc2626",
            "High": "#ea580c",
            "Medium": "#ca8a04",
            "Low": "#65a30d",
        }.get(severity, "#6b7280")

        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #2563eb;">New Defect Reported</h2>

            <p>Hi {developer_name},</p>

            <p>A new defect has been reported for amendment <strong>{amendment_reference}</strong>:</p>

            <div style="background-color: #f3f4f6; padding: 15px; border-left: 4px solid {severity_color}; margin: 20px 0;">
                <p style="margin: 5px 0;"><strong>Defect:</strong> {defect_number}</p>
                <p style="margin: 5px 0;"><strong>Title:</strong> {defect_title}</p>
                <p style="margin: 5px 0;">
                    <strong>Severity:</strong>
                    <span style="color: {severity_color}; font-weight: bold;">{severity}</span>
                </p>
            </div>

            <p>Please review the defect and begin working on a fix.</p>

            <p>
                <a href="http://localhost:3000/defects/{defect_number}"
                   style="background-color: #2563eb; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    View Defect
                </a>
            </p>

            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">

            <p style="font-size: 12px; color: #6b7280;">
                This is an automated notification from the Amendment Tracking System.
            </p>
        </body>
        </html>
        """

        body_text = f"""
New Defect Reported

Hi {developer_name},

A new defect has been reported for amendment {amendment_reference}:

Defect: {defect_number}
Title: {defect_title}
Severity: {severity}

Please review the defect and begin working on a fix.

View Defect: http://localhost:3000/defects/{defect_number}

---
This is an automated notification from the Amendment Tracking System.
        """

        return self.send_email([developer_email], subject, body_html, body_text)


# Global email service instance
email_service = EmailService()
