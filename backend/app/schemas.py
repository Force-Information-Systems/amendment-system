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
    Force,
    LinkType,
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
    version: Optional[str] = Field(None, max_length=50)


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
        description="Field to sort by (amendment_id, created_on, modified_on, priority, etc.)",
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
    database_changes_count: int


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

    next_reference: str
    pattern: str = Field(
        default="AMD-YYYYMMDD-NNN", description="Reference number pattern"
    )


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
