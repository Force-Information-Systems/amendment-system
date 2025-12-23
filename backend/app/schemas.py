"""
Pydantic schemas for request/response validation.

These schemas handle data validation, serialization, and documentation
for the Amendment System API.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from .models import (
    AmendmentType,
    AmendmentStatus,
    DevelopmentStatus,
    Priority,
    LinkType,
    DocumentType,
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
    database_changes: bool = False
    db_upgrade_changes: bool = False
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

    qa_assigned_id: Optional[int] = None
    qa_assigned_date: Optional[datetime] = None
    qa_test_plan_check: Optional[bool] = None
    qa_test_release_notes_check: Optional[bool] = None
    qa_completed: Optional[bool] = None
    qa_signature: Optional[str] = Field(None, max_length=100)
    qa_completed_date: Optional[datetime] = None
    qa_notes: Optional[str] = None
    qa_test_plan_link: Optional[str] = Field(None, max_length=500)
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
    qa_assigned_id: Optional[int] = None
    qa_assigned_date: Optional[datetime] = None
    qa_test_plan_check: bool = False
    qa_test_release_notes_check: bool = False
    qa_completed: bool = False
    qa_signature: Optional[str] = None
    qa_completed_date: Optional[datetime] = None
    qa_notes: Optional[str] = None
    qa_test_plan_link: Optional[str] = None

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
