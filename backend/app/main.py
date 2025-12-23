"""
Main FastAPI application for the Amendment Tracking System.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db, check_db_connection
from . import models  # noqa: F401 - imported for SQLAlchemy model registration


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events:
    - Startup: Initialize database and check connection
    - Shutdown: Cleanup resources
    """
    # Startup
    print("Starting Amendment Tracking System...")
    if not check_db_connection():
        raise RuntimeError("Database connection failed at startup!")
    init_db()
    print("Application startup complete")

    yield

    # Shutdown
    print("Shutting down Amendment Tracking System...")


app = FastAPI(
    title="Amendment Tracking System",
    description=(
        "Internal amendment tracking system for managing application updates, "
        "bug fixes, enhancements, and feature requests."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# CORS configuration from environment
cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000")
cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    """Root endpoint with API information."""
    return {
        "message": "Amendment Tracking System API",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    db_status = check_db_connection()
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
    }


# ============================================================================
# Amendment Endpoints
# ============================================================================

from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from .database import get_db
from . import crud, schemas


@app.post("/api/amendments", response_model=schemas.AmendmentResponse, status_code=201)
def create_amendment(
    amendment: schemas.AmendmentCreate,
    created_by: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Create a new amendment.

    Auto-generates a unique reference number in the format AMD-YYYYMMDD-NNN.
    """
    try:
        db_amendment = crud.create_amendment(db, amendment, created_by)
        return db_amendment
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/amendments", response_model=schemas.AmendmentListResponse)
def list_amendments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    amendment_reference: Optional[str] = None,
    amendment_ids: Optional[str] = None,
    amendment_status: Optional[str] = None,
    development_status: Optional[str] = None,
    priority: Optional[str] = None,
    amendment_type: Optional[str] = None,
    force: Optional[str] = None,
    application: Optional[str] = None,
    assigned_to: Optional[str] = None,
    reported_by: Optional[str] = None,
    date_reported_from: Optional[str] = None,
    date_reported_to: Optional[str] = None,
    created_on_from: Optional[str] = None,
    created_on_to: Optional[str] = None,
    search_text: Optional[str] = None,
    qa_completed: Optional[bool] = None,
    qa_assigned: Optional[bool] = None,
    database_changes: Optional[bool] = None,
    db_upgrade_changes: Optional[bool] = None,
    sort_by: str = "created_on",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
):
    """
    List amendments with advanced filtering and pagination.

    Supports filtering by status, priority, dates, assigned users, and text search.
    """
    # Build filter object
    filters = schemas.AmendmentFilter(
        amendment_reference=amendment_reference,
        amendment_ids=[int(x) for x in amendment_ids.split(",")] if amendment_ids else None,
        amendment_status=amendment_status.split(",") if amendment_status else None,
        development_status=development_status.split(",") if development_status else None,
        priority=priority.split(",") if priority else None,
        amendment_type=amendment_type.split(",") if amendment_type else None,
        force=force.split(",") if force else None,
        application=application,
        assigned_to=assigned_to,
        reported_by=reported_by,
        date_reported_from=date_reported_from,
        date_reported_to=date_reported_to,
        created_on_from=created_on_from,
        created_on_to=created_on_to,
        search_text=search_text,
        qa_completed=qa_completed,
        qa_assigned=qa_assigned,
        database_changes=database_changes,
        db_upgrade_changes=db_upgrade_changes,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    amendments, total = crud.get_amendments(db, filters=filters)

    return schemas.AmendmentListResponse(
        items=amendments,
        total=total,
        skip=skip,
        limit=limit,
    )


@app.get("/api/amendments/stats", response_model=schemas.AmendmentStatsResponse)
def get_amendment_stats_endpoint(db: Session = Depends(get_db)):
    """
    Get amendment statistics for dashboard.

    Returns counts by status, priority, type, and development status.
    """
    stats = crud.get_amendment_stats(db)
    return stats


@app.get("/api/amendments/reference/{reference}", response_model=schemas.AmendmentResponse)
def get_amendment_by_reference(reference: str, db: Session = Depends(get_db)):
    """
    Get a specific amendment by reference number.

    Example: GET /api/amendments/reference/AMD-20231215-001
    """
    amendment = crud.get_amendment_by_reference(db, reference)
    if not amendment:
        raise HTTPException(status_code=404, detail="Amendment not found")
    return amendment


@app.get("/api/amendments/{amendment_id}", response_model=schemas.AmendmentResponse)
def get_amendment(amendment_id: int, db: Session = Depends(get_db)):
    """
    Get a specific amendment by ID.

    Includes all relationships (progress history, applications, links).
    """
    amendment = crud.get_amendment(db, amendment_id)
    if not amendment:
        raise HTTPException(status_code=404, detail="Amendment not found")
    return amendment


@app.put("/api/amendments/{amendment_id}", response_model=schemas.AmendmentResponse)
def update_amendment(
    amendment_id: int,
    amendment: schemas.AmendmentUpdate,
    modified_by: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Update an amendment.

    Allows partial updates. Only provided fields will be updated.
    """
    updated_amendment = crud.update_amendment(db, amendment_id, amendment, modified_by)
    if not updated_amendment:
        raise HTTPException(status_code=404, detail="Amendment not found")
    return updated_amendment


@app.patch("/api/amendments/{amendment_id}/qa", response_model=schemas.AmendmentResponse)
def update_amendment_qa(
    amendment_id: int,
    qa_update: schemas.AmendmentQAUpdate,
    modified_by: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Update QA-specific fields for an amendment.

    Dedicated endpoint for QA team to update testing-related fields.
    """
    updated_amendment = crud.update_amendment_qa(db, amendment_id, qa_update, modified_by)
    if not updated_amendment:
        raise HTTPException(status_code=404, detail="Amendment not found")
    return updated_amendment


@app.delete("/api/amendments/{amendment_id}", status_code=204)
def delete_amendment(amendment_id: int, db: Session = Depends(get_db)):
    """
    Delete an amendment.

    Cascades to all related progress entries, applications, and links.
    """
    success = crud.delete_amendment(db, amendment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Amendment not found")
    return None


# ============================================================================
# Amendment Progress Endpoints
# ============================================================================


@app.post(
    "/api/amendments/{amendment_id}/progress",
    response_model=schemas.AmendmentProgressResponse,
    status_code=201,
)
def add_amendment_progress(
    amendment_id: int,
    progress: schemas.AmendmentProgressCreate,
    created_by: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Add a progress update to an amendment.

    Tracks development progress with timestamp and notes.
    """
    try:
        db_progress = crud.add_amendment_progress(db, amendment_id, progress, created_by)
        return db_progress
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get(
    "/api/amendments/{amendment_id}/progress",
    response_model=List[schemas.AmendmentProgressResponse],
)
def get_amendment_progress(amendment_id: int, db: Session = Depends(get_db)):
    """
    Get all progress updates for an amendment.

    Returns progress entries ordered by date (newest first).
    """
    progress_list = crud.get_amendment_progress(db, amendment_id)
    return progress_list


# ============================================================================
# Amendment Link Endpoints
# ============================================================================


@app.post(
    "/api/amendments/{amendment_id}/links",
    response_model=schemas.AmendmentLinkResponse,
    status_code=201,
)
def link_amendments(
    amendment_id: int,
    link: schemas.AmendmentLinkCreate,
    created_by: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Link two amendments together.

    Link types: Related, Duplicate, Blocks, Blocked By
    """
    try:
        db_link = crud.link_amendments(db, amendment_id, link, created_by)
        return db_link
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get(
    "/api/amendments/{amendment_id}/links",
    response_model=List[schemas.AmendmentLinkResponse],
)
def get_linked_amendments(amendment_id: int, db: Session = Depends(get_db)):
    """
    Get all amendments linked to this amendment.

    Returns all links where this amendment is either the source or target.
    """
    links = crud.get_linked_amendments(db, amendment_id)
    return links


@app.delete("/api/amendments/links/{link_id}", status_code=204)
def remove_amendment_link(link_id: int, db: Session = Depends(get_db)):
    """
    Remove a link between two amendments.
    """
    success = crud.remove_amendment_link(db, link_id)
    if not success:
        raise HTTPException(status_code=404, detail="Link not found")
    return None


# ============================================================================
# Employee Endpoints
# ============================================================================


@app.post("/api/employees", response_model=schemas.EmployeeResponse, status_code=201)
def create_employee(
    employee: schemas.EmployeeCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new employee record.
    """
    try:
        db_employee = crud.create_employee(db, employee)
        return db_employee
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/employees/{employee_id}", response_model=schemas.EmployeeResponse)
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    """
    Get a specific employee by ID.
    """
    employee = crud.get_employee(db, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@app.get("/api/employees", response_model=List[schemas.EmployeeResponse])
def get_employees(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    active_only: bool = Query(False, description="Filter to only active employees"),
    db: Session = Depends(get_db),
):
    """
    Get all employees with pagination.
    """
    employees, total = crud.get_employees(db, skip=skip, limit=limit, active_only=active_only)
    return employees


@app.put("/api/employees/{employee_id}", response_model=schemas.EmployeeResponse)
def update_employee(
    employee_id: int,
    employee: schemas.EmployeeUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an employee's information.
    """
    try:
        updated_employee = crud.update_employee(db, employee_id, employee)
        if updated_employee is None:
            raise HTTPException(status_code=404, detail="Employee not found")
        return updated_employee
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/employees/{employee_id}", status_code=204)
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    """
    Delete an employee record.
    """
    try:
        success = crud.delete_employee(db, employee_id)
        if not success:
            raise HTTPException(status_code=404, detail="Employee not found")
        return None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Application Endpoints
# ============================================================================


@app.post("/api/applications", response_model=schemas.ApplicationResponse, status_code=201)
def create_application(
    application: schemas.ApplicationCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new application record.
    """
    try:
        db_application = crud.create_application(db, application)
        return db_application
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/applications/{application_id}", response_model=schemas.ApplicationWithVersions)
def get_application(application_id: int, db: Session = Depends(get_db)):
    """
    Get a specific application by ID with all its versions.
    """
    application = crud.get_application(db, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


@app.get("/api/applications", response_model=List[schemas.ApplicationResponse])
def get_applications(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    active_only: bool = Query(False, description="Filter to only active applications"),
    db: Session = Depends(get_db),
):
    """
    Get all applications with pagination.
    """
    applications, total = crud.get_applications(db, skip=skip, limit=limit, active_only=active_only)
    return applications


@app.put("/api/applications/{application_id}", response_model=schemas.ApplicationResponse)
def update_application(
    application_id: int,
    application: schemas.ApplicationUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an application's information.
    """
    try:
        updated_application = crud.update_application(db, application_id, application)
        if updated_application is None:
            raise HTTPException(status_code=404, detail="Application not found")
        return updated_application
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/applications/{application_id}", status_code=204)
def delete_application(application_id: int, db: Session = Depends(get_db)):
    """
    Delete an application record.
    """
    try:
        success = crud.delete_application(db, application_id)
        if not success:
            raise HTTPException(status_code=404, detail="Application not found")
        return None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Application Version Endpoints
# ============================================================================


@app.post("/api/applications/{application_id}/versions", response_model=schemas.ApplicationVersionResponse, status_code=201)
def create_application_version(
    application_id: int,
    version: schemas.ApplicationVersionCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new version for an application.
    """
    # Verify application exists
    application = crud.get_application(db, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")

    # Ensure the version data has the correct application_id
    version.application_id = application_id

    try:
        db_version = crud.create_application_version(db, version)
        return db_version
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/applications/{application_id}/versions", response_model=List[schemas.ApplicationVersionResponse])
def get_application_versions(
    application_id: int,
    active_only: bool = Query(False, description="Filter to only active versions"),
    db: Session = Depends(get_db),
):
    """
    Get all versions for a specific application.
    """
    versions = crud.get_application_versions(db, application_id, active_only=active_only)
    return versions


@app.get("/api/versions/{version_id}", response_model=schemas.ApplicationVersionResponse)
def get_application_version(version_id: int, db: Session = Depends(get_db)):
    """
    Get a specific application version by ID.
    """
    version = crud.get_application_version(db, version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Application version not found")
    return version


@app.put("/api/versions/{version_id}", response_model=schemas.ApplicationVersionResponse)
def update_application_version(
    version_id: int,
    version: schemas.ApplicationVersionUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an application version's information.
    """
    try:
        updated_version = crud.update_application_version(db, version_id, version)
        if updated_version is None:
            raise HTTPException(status_code=404, detail="Application version not found")
        return updated_version
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/versions/{version_id}", status_code=204)
def delete_application_version(version_id: int, db: Session = Depends(get_db)):
    """
    Delete an application version record.
    """
    try:
        success = crud.delete_application_version(db, version_id)
        if not success:
            raise HTTPException(status_code=404, detail="Application version not found")
        return None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Statistics and Reference Data Endpoints
# ============================================================================


@app.get("/api/reference/next", response_model=schemas.NextReferenceResponse)
def get_next_reference(db: Session = Depends(get_db)):
    """
    Get the next available amendment reference number.

    Useful for pre-filling forms before creating an amendment.
    """
    next_ref = crud.get_next_reference(db)
    return schemas.NextReferenceResponse(reference=next_ref)


@app.get("/api/reference/statuses", response_model=List[str])
def get_statuses():
    """Get all available amendment statuses."""
    from .models import AmendmentStatus
    return [status.value for status in AmendmentStatus]


@app.get("/api/reference/development-statuses", response_model=List[str])
def get_dev_statuses():
    """Get all available development statuses."""
    from .models import DevelopmentStatus
    return [status.value for status in DevelopmentStatus]


@app.get("/api/reference/priorities", response_model=List[str])
def get_priorities():
    """Get all available priority levels."""
    from .models import Priority
    return [priority.value for priority in Priority]


@app.get("/api/reference/types", response_model=List[str])
def get_types():
    """Get all available amendment types."""
    from .models import AmendmentType
    return [type_.value for type_ in AmendmentType]


@app.get("/api/reference/forces", response_model=List[str])
def get_forces():
    """Get all available military forces."""
    from .models import Force
    return [force.value for force in Force]


@app.get("/api/reference/link-types", response_model=List[str])
def get_link_types():
    """Get all available amendment link types."""
    from .models import LinkType
    return [link_type.value for link_type in LinkType]
