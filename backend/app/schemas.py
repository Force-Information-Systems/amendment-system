"""
Pydantic schemas for request/response validation.

These schemas handle data validation, serialization, and documentation
for the Amendment System API.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, ConfigDict

from .models import (
    AmendmentType,
    AmendmentStatus,
    DevelopmentStatus,
    Priority,
    LinkType,
    DocumentType,
    QAStatus,
    ExecutionStatus,
    DefectStatus,
    DefectSeverity,
    NotificationType,
)


# ============================================================================
# Base Schemas with Common Fields
# ============================================================================


class AuditInfo(BaseModel):
    """Audit information for tracking creation and modification."""

    created_by: Optional[str] = None
    created_on: datetime
    modified_by: Optional[str] = None
    modified_on: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# AmendmentProgress Schemas
# ============================================================================


class AmendmentProgressBase(BaseModel):
    """Base schema for amendment progress entries."""

    start_date: Optional[datetime] = None
    description: str = Field(..., min_length=1, description="Progress description")
    notes: Optional[str] = None


class AmendmentProgressCreate(AmendmentProgressBase):
    """Schema for creating a new progress entry."""

    created_by: Optional[str] = None


class AmendmentProgressUpdate(BaseModel):
    """Schema for updating an existing progress entry."""

    start_date: Optional[datetime] = None
    description: Optional[str] = Field(None, min_length=1)
    notes: Optional[str] = None
    modified_by: Optional[str] = None


class AmendmentProgressResponse(AmendmentProgressBase):
    """Schema for progress entry responses."""

    amendment_progress_id: int
    amendment_id: int
    created_by: Optional[str] = None
    created_on: datetime
    modified_by: Optional[str] = None
    modified_on: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# AmendmentApplication Schemas
# ============================================================================


class AmendmentApplicationBase(BaseModel):
    """Base schema for amendment applications."""

    application_name: str = Field(..., min_length=1, max_length=100)
    application_id: Optional[int] = None
    reported_version: Optional[str] = Field(None, max_length=50)
    applied_version: Optional[str] = Field(None, max_length=50)
    development_status: Optional[DevelopmentStatus] = None


class AmendmentApplicationCreate(AmendmentApplicationBase):
    """Schema for creating an amendment application link."""

    pass


class AmendmentApplicationResponse(AmendmentApplicationBase):
    """Schema for amendment application responses."""

    id: int
    amendment_id: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# AmendmentLink Schemas
# ============================================================================


class AmendmentLinkBase(BaseModel):
    """Base schema for amendment links."""

    linked_amendment_id: int
    link_type: LinkType = LinkType.RELATED


class AmendmentLinkCreate(AmendmentLinkBase):
    """Schema for creating an amendment link."""

    pass


class AmendmentLinkResponse(AmendmentLinkBase):
    """Schema for amendment link responses."""

    amendment_link_id: int
    amendment_id: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Amendment Schemas
# ============================================================================


class AmendmentBase(BaseModel):
    """Base schema for amendments with common fields."""

    amendment_type: AmendmentType
    description: str = Field(..., min_length=1, description="Amendment description")
    amendment_status: AmendmentStatus = AmendmentStatus.OPEN
    development_status: DevelopmentStatus = DevelopmentStatus.NOT_STARTED
    priority: Priority = Priority.MEDIUM
    force: Optional[str] = Field(None, max_length=50)
    application: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    reported_by: Optional[str] = Field(None, max_length=100)
    assigned_to: Optional[str] = Field(None, max_length=100)
    date_reported: Optional[datetime] = None
    database_changes: Optional[bool] = False
    db_upgrade_changes: Optional[bool] = False
    release_notes: Optional[str] = None


class AmendmentCreate(AmendmentBase):
    """Schema for creating a new amendment."""

    # Reference number will be auto-generated, so not required in creation
    created_by: Optional[str] = None


class AmendmentUpdate(BaseModel):
    """Schema for updating an existing amendment (all fields optional)."""

    amendment_type: Optional[AmendmentType] = None
    description: Optional[str] = Field(None, min_length=1)
    amendment_status: Optional[AmendmentStatus] = None
    development_status: Optional[DevelopmentStatus] = None
    priority: Optional[Priority] = None
    force: Optional[str] = Field(None, max_length=50)
    application: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    reported_by: Optional[str] = Field(None, max_length=100)
    assigned_to: Optional[str] = Field(None, max_length=100)
    date_reported: Optional[datetime] = None
    database_changes: Optional[bool] = None
    db_upgrade_changes: Optional[bool] = None
    release_notes: Optional[str] = None
    modified_by: Optional[str] = None


class AmendmentQAUpdate(BaseModel):
    """Schema for updating QA-specific fields."""

    qa_status: Optional[str] = None
    qa_assigned_id: Optional[int] = None
    qa_assigned_date: Optional[datetime] = None
    qa_started_date: Optional[datetime] = None
    qa_test_plan_check: Optional[bool] = None
    qa_test_release_notes_check: Optional[bool] = None
    qa_completed: Optional[bool] = None
    qa_signature: Optional[str] = Field(None, max_length=100)
    qa_completed_date: Optional[datetime] = None
    qa_notes: Optional[str] = None
    qa_test_plan_link: Optional[str] = Field(None, max_length=500)
    qa_blocked_reason: Optional[str] = None
    modified_by: Optional[str] = None


class AmendmentSummary(BaseModel):
    """Lightweight schema for amendment list views."""

    amendment_id: int
    amendment_reference: str
    amendment_type: AmendmentType
    description: str
    amendment_status: AmendmentStatus
    development_status: DevelopmentStatus
    priority: Priority
    force: Optional[str] = None
    application: Optional[str] = None
    reported_by: Optional[str] = None
    assigned_to: Optional[str] = None
    date_reported: Optional[datetime] = None
    created_on: datetime
    modified_on: datetime

    model_config = ConfigDict(from_attributes=True)


class AmendmentResponse(AmendmentBase):
    """Full amendment response with all fields and relationships."""

    amendment_id: int
    amendment_reference: str

    # QA fields
    qa_status: Optional[str] = None
    qa_assigned_id: Optional[int] = None
    qa_assigned_date: Optional[datetime] = None
    qa_started_date: Optional[datetime] = None
    qa_test_plan_check: Optional[bool] = False
    qa_test_release_notes_check: Optional[bool] = False
    qa_completed: Optional[bool] = False
    qa_signature: Optional[str] = None
    qa_completed_date: Optional[datetime] = None
    qa_notes: Optional[str] = None
    qa_test_plan_link: Optional[str] = None
    qa_blocked_reason: Optional[str] = None

    # Audit fields
    created_by: Optional[str] = None
    created_on: datetime
    modified_by: Optional[str] = None
    modified_on: datetime

    # Relationships
    progress_entries: List[AmendmentProgressResponse] = []
    applications: List[AmendmentApplicationResponse] = []
    links: List[AmendmentLinkResponse] = []
    documents: List["AmendmentDocumentResponse"] = []

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Filter and Search Schemas
# ============================================================================


class AmendmentFilter(BaseModel):
    """Schema for filtering and searching amendments."""

    # Filter by reference or IDs
    amendment_reference: Optional[str] = None
    amendment_ids: Optional[List[int]] = None

    # Filter by status and priority
    amendment_status: Optional[List[AmendmentStatus]] = None
    development_status: Optional[List[DevelopmentStatus]] = None
    priority: Optional[List[Priority]] = None

    # Filter by type, force, application
    amendment_type: Optional[List[AmendmentType]] = None
    force: Optional[List[str]] = None
    application: Optional[List[str]] = None
    version: Optional[List[str]] = Field(
        None, description="Filter by version (e.g., Centurion 7.5, Centurion 8.0)"
    )

    # Filter by people
    assigned_to: Optional[List[str]] = None
    reported_by: Optional[List[str]] = None

    # Filter by date ranges
    date_reported_from: Optional[datetime] = None
    date_reported_to: Optional[datetime] = None
    created_on_from: Optional[datetime] = None
    created_on_to: Optional[datetime] = None
    modified_on_from: Optional[datetime] = None
    modified_on_to: Optional[datetime] = None

    # Text search
    search_text: Optional[str] = Field(
        None, description="Search in description, notes, and release_notes"
    )

    # QA filters
    qa_completed: Optional[bool] = None
    qa_assigned: Optional[bool] = Field(
        None, description="Filter by whether QA is assigned"
    )
    qa_assigned_to_employee_id: Optional[int] = Field(
        None, description="Filter by QA assigned to specific employee"
    )
    qa_overall_result: Optional[List[str]] = Field(
        None, description="Filter by QA overall result (Passed, Failed, Passed with Issues)"
    )

    # Database change filters
    database_changes: Optional[bool] = None
    db_upgrade_changes: Optional[bool] = None

    # Pagination
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of records")

    # Sorting
    sort_by: Optional[str] = Field(
        "amendment_id",
        description="Field to sort by (amendment_id, created_on, etc.)",
    )
    sort_order: Optional[str] = Field(
        "desc", pattern="^(asc|desc)$", description="Sort order: asc or desc"
    )


class AmendmentListResponse(BaseModel):
    """Response schema for paginated amendment lists."""

    items: List[AmendmentSummary]
    total: int
    skip: int
    limit: int


# ============================================================================
# Statistics and Reference Data Schemas
# ============================================================================


class AmendmentStats(BaseModel):
    """Statistics about amendments."""

    total_amendments: int
    by_status: dict[str, int]
    by_priority: dict[str, int]
    by_type: dict[str, int]
    by_development_status: dict[str, int]
    qa_pending: int
    qa_completed: int
    database_changes: int
    db_upgrade_changes: int


class ReferenceData(BaseModel):
    """Reference data for dropdowns and filters."""

    amendment_types: List[str]
    amendment_statuses: List[str]
    development_statuses: List[str]
    priorities: List[str]
    forces: List[str]
    link_types: List[str]


class NextReferenceResponse(BaseModel):
    """Response schema for next available reference number."""

    reference: str = Field(..., description="Next available reference number")


class AmendmentStatsResponse(BaseModel):
    """Response schema for amendment statistics."""

    total_amendments: int
    by_status: dict
    by_priority: dict
    by_type: dict
    by_development_status: dict
    qa_pending: int
    qa_completed: int
    database_changes: int
    db_upgrade_changes: int


# ============================================================================
# Bulk Operation Schemas
# ============================================================================


class BulkUpdateRequest(BaseModel):
    """Schema for bulk updating multiple amendments."""

    amendment_ids: List[int] = Field(..., min_length=1)
    updates: AmendmentUpdate


class BulkUpdateResponse(BaseModel):
    """Response schema for bulk updates."""

    updated_count: int
    failed_ids: List[int] = []
    errors: dict[int, str] = {}


# ============================================================================
# AmendmentDocument Schemas
# ============================================================================


class AmendmentDocumentBase(BaseModel):
    """Base schema for amendment documents."""

    document_name: str = Field(..., min_length=1, max_length=255)
    document_type: DocumentType = DocumentType.OTHER
    description: Optional[str] = None


class AmendmentDocumentCreate(AmendmentDocumentBase):
    """Schema for creating a document entry (file uploaded separately)."""

    original_filename: str
    file_path: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    uploaded_by: Optional[str] = None


class AmendmentDocumentResponse(AmendmentDocumentBase):
    """Schema for document responses."""

    document_id: int
    amendment_id: int
    original_filename: str
    file_path: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    uploaded_by: Optional[str] = None
    uploaded_on: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Employee Schemas
# ============================================================================


class EmployeeBase(BaseModel):
    """Base schema for employees."""

    employee_name: str = Field(..., min_length=1, max_length=100)
    initials: Optional[str] = Field(None, max_length=10)
    email: Optional[str] = Field(None, max_length=150)
    windows_login: Optional[str] = Field(None, max_length=100)
    is_active: bool = True


class EmployeeCreate(EmployeeBase):
    """Schema for creating a new employee."""

    pass


class EmployeeUpdate(BaseModel):
    """Schema for updating an existing employee."""

    employee_name: Optional[str] = Field(None, min_length=1, max_length=100)
    initials: Optional[str] = Field(None, max_length=10)
    email: Optional[str] = Field(None, max_length=150)
    windows_login: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class EmployeeResponse(EmployeeBase):
    """Schema for employee responses."""

    employee_id: int
    created_on: datetime
    modified_on: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Authentication Schemas
# ============================================================================


class LoginRequest(BaseModel):
    """Schema for login requests."""

    username: str = Field(..., min_length=1, max_length=100, description="Windows login or email")
    password: str = Field(..., min_length=1, description="Password")


class Token(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for decoded token data."""

    employee_id: Optional[int] = None
    role: Optional[str] = None


class UserInfo(BaseModel):
    """Schema for current user information."""

    employee_id: int
    employee_name: str
    email: Optional[str] = None
    windows_login: Optional[str] = None
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Application Schemas
# ============================================================================


class ApplicationBase(BaseModel):
    """Base schema for applications."""

    application_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: bool = True


class ApplicationCreate(ApplicationBase):
    """Schema for creating a new application."""

    pass


class ApplicationUpdate(BaseModel):
    """Schema for updating an existing application."""

    application_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ApplicationResponse(ApplicationBase):
    """Schema for application responses."""

    application_id: int
    created_on: datetime
    modified_on: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Application Version Schemas
# ============================================================================


class ApplicationVersionBase(BaseModel):
    """Base schema for application versions."""

    application_id: int
    version: str = Field(..., min_length=1, max_length=50)
    released_date: Optional[datetime] = None
    notes: Optional[str] = None
    is_active: bool = True


class ApplicationVersionCreate(ApplicationVersionBase):
    """Schema for creating a new application version."""

    pass


class ApplicationVersionUpdate(BaseModel):
    """Schema for updating an existing application version."""

    version: Optional[str] = Field(None, min_length=1, max_length=50)
    released_date: Optional[datetime] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class ApplicationVersionResponse(ApplicationVersionBase):
    """Schema for application version responses."""

    application_version_id: int
    created_on: datetime
    modified_on: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationWithVersions(ApplicationResponse):
    """Schema for application with all its versions."""

    versions: List[ApplicationVersionResponse] = []

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# QA System Schemas
# ============================================================================


# ============================================================================
# QA Test Case Schemas
# ============================================================================


class QATestCaseBase(BaseModel):
    """Base schema for QA test cases."""

    title: str = Field(..., min_length=1, max_length=255, description="Test case title")
    description: Optional[str] = Field(None, description="Detailed description")
    test_type: str = Field(..., min_length=1, max_length=50, description="Type of test (Functional, Integration, etc.)")
    priority: str = Field(default="Medium", max_length=50, description="Test priority")

    # Test details
    preconditions: Optional[str] = Field(None, description="Pre-requisites before executing test")
    test_steps: Optional[str] = Field(None, description="JSON array of test steps")
    expected_results: Optional[str] = Field(None, description="Expected test results")

    # Classification
    application_id: Optional[int] = Field(None, description="Associated application ID")
    component: Optional[str] = Field(None, max_length=100, description="Application component")
    tags: Optional[str] = Field(None, description="JSON array of tags")

    # Status
    is_active: bool = Field(default=True, description="Is test case active")
    is_automated: bool = Field(default=False, description="Is test automated")
    automation_script: Optional[str] = Field(None, description="Automation script path or code")


class QATestCaseCreate(QATestCaseBase):
    """Schema for creating a new test case."""

    created_by: Optional[str] = None


class QATestCaseUpdate(BaseModel):
    """Schema for updating an existing test case."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    test_type: Optional[str] = Field(None, min_length=1, max_length=50)
    priority: Optional[str] = Field(None, max_length=50)
    preconditions: Optional[str] = None
    test_steps: Optional[str] = None
    expected_results: Optional[str] = None
    application_id: Optional[int] = None
    component: Optional[str] = Field(None, max_length=100)
    tags: Optional[str] = None
    is_active: Optional[bool] = None
    is_automated: Optional[bool] = None
    automation_script: Optional[str] = None
    modified_by: Optional[str] = None


class QATestCaseResponse(QATestCaseBase):
    """Schema for test case responses."""

    test_case_id: int
    test_case_number: str
    created_by: Optional[str] = None
    created_on: datetime
    modified_by: Optional[str] = None
    modified_on: datetime

    model_config = ConfigDict(from_attributes=True)


class QATestCaseListResponse(BaseModel):
    """Response schema for paginated test case lists."""

    items: List[QATestCaseResponse]
    total: int
    skip: int
    limit: int


# ============================================================================
# QA Test Execution Schemas
# ============================================================================


class QATestExecutionBase(BaseModel):
    """Base schema for test executions."""

    test_case_id: int = Field(..., description="Test case to execute")
    executed_by_id: Optional[int] = Field(None, description="Employee who executed the test")

    # Execution details
    execution_status: str = Field(default="Not Run", max_length=50, description="Execution status")
    executed_on: Optional[datetime] = Field(None, description="When test was executed")
    duration_minutes: Optional[int] = Field(None, ge=0, description="Test duration in minutes")

    # Results
    actual_results: Optional[str] = Field(None, description="Actual test results")
    notes: Optional[str] = Field(None, description="Additional notes")
    attachments: Optional[str] = Field(None, description="JSON array of attachments")

    # Environment
    test_environment: Optional[str] = Field(None, max_length=100, description="Test environment")
    build_version: Optional[str] = Field(None, max_length=50, description="Build version tested")


class QATestExecutionCreate(QATestExecutionBase):
    """Schema for creating a new test execution."""

    amendment_id: int = Field(..., description="Amendment being tested")
    created_by: Optional[str] = None


class QATestExecutionUpdate(BaseModel):
    """Schema for updating an existing test execution."""

    executed_by_id: Optional[int] = None
    execution_status: Optional[str] = Field(None, max_length=50)
    executed_on: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=0)
    actual_results: Optional[str] = None
    notes: Optional[str] = None
    attachments: Optional[str] = None
    test_environment: Optional[str] = Field(None, max_length=100)
    build_version: Optional[str] = Field(None, max_length=50)
    modified_by: Optional[str] = None


class QATestExecutionExecuteRequest(BaseModel):
    """Schema for executing a test (recording results)."""

    execution_status: ExecutionStatus = Field(..., description="Test result status")
    executed_on: datetime = Field(default_factory=datetime.now, description="Execution timestamp")
    duration_minutes: Optional[int] = Field(None, ge=0, description="Test duration")
    actual_results: Optional[str] = Field(None, description="What actually happened")
    notes: Optional[str] = Field(None, description="Additional notes")
    attachments: Optional[str] = Field(None, description="JSON array of attachments")
    test_environment: Optional[str] = Field(None, description="Environment tested")
    build_version: Optional[str] = Field(None, description="Build version")
    executed_by_id: int = Field(..., description="Who executed the test")


class QATestExecutionResponse(QATestExecutionBase):
    """Schema for test execution responses."""

    execution_id: int
    amendment_id: int
    created_by: Optional[str] = None
    created_on: datetime
    modified_by: Optional[str] = None
    modified_on: datetime

    model_config = ConfigDict(from_attributes=True)


class QATestExecutionListResponse(BaseModel):
    """Response schema for paginated test execution lists."""

    items: List[QATestExecutionResponse]
    total: int


# ============================================================================
# QA Defect Schemas
# ============================================================================


class QADefectBase(BaseModel):
    """Base schema for QA defects."""

    title: str = Field(..., min_length=1, max_length=255, description="Defect title")
    description: Optional[str] = Field(None, description="Detailed defect description")
    severity: str = Field(default="Medium", max_length=50, description="Defect severity")
    status: str = Field(default="New", max_length=50, description="Defect status")

    # Reproduction
    steps_to_reproduce: Optional[str] = Field(None, description="How to reproduce the defect")
    actual_behavior: Optional[str] = Field(None, description="What actually happens")
    expected_behavior: Optional[str] = Field(None, description="What should happen")

    # Assignment
    assigned_to_id: Optional[int] = Field(None, description="Developer assigned to fix")

    # Resolution
    resolution: Optional[str] = Field(None, description="How defect was resolved")
    root_cause: Optional[str] = Field(None, description="Root cause analysis")
    fixed_in_version: Optional[str] = Field(None, max_length=50, description="Version where fixed")


class QADefectCreate(QADefectBase):
    """Schema for creating a new defect."""

    amendment_id: int = Field(..., description="Amendment being tested")
    test_execution_id: Optional[int] = Field(None, description="Related test execution")
    reported_by_id: int = Field(..., description="Who reported the defect")
    created_by: Optional[str] = None


class QADefectUpdate(BaseModel):
    """Schema for updating an existing defect."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    severity: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, max_length=50)
    steps_to_reproduce: Optional[str] = None
    actual_behavior: Optional[str] = None
    expected_behavior: Optional[str] = None
    assigned_to_id: Optional[int] = None
    resolution: Optional[str] = None
    root_cause: Optional[str] = None
    fixed_in_version: Optional[str] = Field(None, max_length=50)
    assigned_date: Optional[datetime] = None
    resolved_date: Optional[datetime] = None
    closed_date: Optional[datetime] = None
    modified_by: Optional[str] = None


class QADefectResponse(QADefectBase):
    """Schema for defect responses."""

    defect_id: int
    defect_number: str
    amendment_id: int
    test_execution_id: Optional[int] = None
    reported_by_id: Optional[int] = None
    reported_date: datetime
    assigned_date: Optional[datetime] = None
    resolved_date: Optional[datetime] = None
    closed_date: Optional[datetime] = None
    created_by: Optional[str] = None
    created_on: datetime
    modified_by: Optional[str] = None
    modified_on: datetime

    model_config = ConfigDict(from_attributes=True)


class QADefectListResponse(BaseModel):
    """Response schema for paginated defect lists."""

    items: List[QADefectResponse]
    total: int
    skip: int
    limit: int


# ============================================================================
# QA History Schemas
# ============================================================================


class QAHistoryResponse(BaseModel):
    """Schema for QA history responses (read-only)."""

    history_id: int
    amendment_id: int
    action: str
    field_name: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    comment: Optional[str] = None
    changed_by_id: Optional[int] = None
    changed_on: datetime

    model_config = ConfigDict(from_attributes=True)


class QAHistoryListResponse(BaseModel):
    """Response schema for QA history lists."""

    items: List[QAHistoryResponse]
    total: int


class QATimelineEvent(BaseModel):
    """Schema for timeline visualization."""

    event_id: int
    event_type: str  # "status_change", "assignment", "test_executed", "defect_created"
    timestamp: datetime
    title: str
    description: Optional[str] = None
    actor: Optional[str] = None  # Employee name
    metadata: Optional[dict] = None


class QATimelineResponse(BaseModel):
    """Response schema for QA timeline."""

    amendment_id: int
    events: List[QATimelineEvent]


# ============================================================================
# QA Notification Schemas
# ============================================================================


class QANotificationBase(BaseModel):
    """Base schema for QA notifications."""

    notification_type: str = Field(..., max_length=50, description="Type of notification")
    title: str = Field(..., min_length=1, max_length=255, description="Notification title")
    message: Optional[str] = Field(None, description="Notification message")
    amendment_id: Optional[int] = Field(None, description="Related amendment")
    defect_id: Optional[int] = Field(None, description="Related defect")


class QANotificationCreate(QANotificationBase):
    """Schema for creating a new notification."""

    employee_id: int = Field(..., description="Recipient employee")
    is_email_sent: bool = Field(default=False, description="Was email sent")


class QANotificationUpdate(BaseModel):
    """Schema for updating a notification."""

    is_read: Optional[bool] = Field(None, description="Mark as read/unread")
    read_on: Optional[datetime] = Field(None, description="When notification was read")


class QANotificationResponse(QANotificationBase):
    """Schema for notification responses."""

    notification_id: int
    employee_id: int
    is_read: bool
    is_email_sent: bool
    read_on: Optional[datetime] = None
    created_on: datetime

    model_config = ConfigDict(from_attributes=True)


class QANotificationListResponse(BaseModel):
    """Response schema for notification lists."""

    items: List[QANotificationResponse]
    total: int
    unread_count: int


class QANotificationUnreadCountResponse(BaseModel):
    """Response schema for unread notification count."""

    unread_count: int


# ============================================================================
# QA Comment Schemas
# ============================================================================


class QACommentBase(BaseModel):
    """Base schema for QA comments."""

    amendment_id: int
    employee_id: int
    comment_text: str
    comment_type: str = "General"


class QACommentCreate(QACommentBase):
    """Schema for creating a QA comment."""

    pass


class QACommentUpdate(BaseModel):
    """Schema for updating a QA comment."""

    comment_text: Optional[str] = None
    comment_type: Optional[str] = None


class QACommentResponse(QACommentBase):
    """Response schema for QA comments."""

    comment_id: int
    is_edited: bool
    created_on: datetime
    modified_on: datetime

    # Employee details (for display)
    employee_name: Optional[str] = None

    # GitHub Issues features
    parent_comment_id: Optional[int] = None
    replies: List[QACommentResponse] = []
    mentions: List[CommentMentionResponse] = []
    reactions: List[CommentReactionResponse] = []
    reaction_summary: Dict[str, int] = {}

    class Config:
        from_attributes = True


class QACommentListResponse(BaseModel):
    """Response schema for list of QA comments."""

    items: List[QACommentResponse]
    total: int


# ============================================================================
# QA Dashboard & Reporting Schemas
# ============================================================================


class QADashboardTaskSummary(BaseModel):
    """Summary of a QA task for dashboard."""

    amendment_id: int
    amendment_reference: str
    description: str
    qa_status: str
    priority: str
    qa_assigned_date: Optional[datetime] = None
    qa_due_date: Optional[datetime] = None
    is_overdue: bool


class QADashboardResponse(BaseModel):
    """Response schema for QA dashboard."""

    assigned_to_me: List[QADashboardTaskSummary]
    in_testing: List[QADashboardTaskSummary]
    overdue: List[QADashboardTaskSummary]
    completed_this_week: int
    total_assigned: int
    total_in_testing: int
    total_overdue: int


class QAMetricsResponse(BaseModel):
    """Response schema for QA metrics."""

    # Pass/fail rates
    total_tests_executed: int
    tests_passed: int
    tests_failed: int
    tests_blocked: int
    pass_rate_percentage: float

    # Defects
    total_defects: int
    open_defects: int
    critical_defects: int
    defects_by_severity: dict[str, int]
    defects_by_status: dict[str, int]

    # Time metrics
    average_time_to_test_hours: float
    average_test_duration_minutes: float

    # SLA compliance
    total_qa_tasks: int
    on_time_completions: int
    sla_compliance_percentage: float


class QACalendarEvent(BaseModel):
    """Schema for QA calendar events."""

    event_id: int  # Amendment ID
    title: str  # Amendment reference + description
    start: datetime  # QA due date
    status: str  # QA status
    priority: str
    is_overdue: bool
    assigned_to: Optional[str] = None


class QACalendarResponse(BaseModel):
    """Response schema for QA calendar."""

    events: List[QACalendarEvent]
    total: int


class QATesterWorkload(BaseModel):
    """Schema for tester workload."""

    employee_id: int
    employee_name: str
    total_assigned: int
    in_testing: int
    overdue: int
    completed_this_week: int
    average_completion_time_hours: float


class QAWorkloadResponse(BaseModel):
    """Response schema for team workload."""

    testers: List[QATesterWorkload]
    total_testers: int


# ============================================================================
# GitHub Issues Features - Comment Mentions
# ============================================================================


class CommentMentionBase(BaseModel):
    """Base schema for comment mentions."""

    comment_id: int
    mentioned_employee_id: int


class CommentMentionCreate(CommentMentionBase):
    """Schema for creating a comment mention."""

    mentioned_by_employee_id: int


class CommentMentionResponse(CommentMentionBase):
    """Response schema for comment mentions."""

    mention_id: int
    mentioned_by_employee_id: int
    created_on: datetime
    is_notified: bool

    class Config:
        from_attributes = True


# ============================================================================
# GitHub Issues Features - Amendment Watchers
# ============================================================================


class AmendmentWatcherBase(BaseModel):
    """Base schema for amendment watchers."""

    amendment_id: int
    employee_id: int


class AmendmentWatcherCreate(BaseModel):
    """Schema for creating an amendment watcher."""

    watch_reason: str = "Manual"
    notify_comments: bool = True
    notify_status_changes: bool = True
    notify_mentions: bool = True


class AmendmentWatcherUpdate(BaseModel):
    """Schema for updating watcher preferences."""

    is_watching: Optional[bool] = None
    notify_comments: Optional[bool] = None
    notify_status_changes: Optional[bool] = None
    notify_mentions: Optional[bool] = None


class AmendmentWatcherResponse(BaseModel):
    """Response schema for amendment watchers."""

    watcher_id: int
    amendment_id: int
    employee_id: int
    watch_reason: str
    is_watching: bool
    created_on: datetime
    notify_comments: bool
    notify_status_changes: bool
    notify_mentions: bool

    # Employee details
    employee_name: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# GitHub Issues Features - Comment Reactions
# ============================================================================


class CommentReactionCreate(BaseModel):
    """Schema for creating/toggling a comment reaction."""

    comment_id: int
    emoji: str


class CommentReactionResponse(BaseModel):
    """Response schema for comment reactions."""

    reaction_id: int
    comment_id: int
    employee_id: int
    emoji: str
    created_on: datetime

    # Employee details
    employee_name: Optional[str] = None

    class Config:
        from_attributes = True
