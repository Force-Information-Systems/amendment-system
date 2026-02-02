"""
Main FastAPI application for the Amendment Tracking System.
"""

import os
import shutil
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, status, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import timedelta

from .database import init_db, check_db_connection, get_db
from . import models, crud, schemas  # noqa: F401 - imported for SQLAlchemy model registration


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
# Authentication Endpoints
# ============================================================================

from .auth import get_current_user, require_admin, create_access_token
from datetime import timedelta


@app.post("/api/auth/login", response_model=schemas.Token)
def login(
    credentials: schemas.LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT access token.

    Supports two authentication methods:
    1. Windows/Active Directory (if configured) - tried first
    2. Local password authentication - fallback

    Accepts username (windows_login or email) and password.
    Returns JWT token on successful authentication.
    """
    from .auth import authenticate_windows_user

    employee = None

    # Try Windows/AD authentication first
    ad_user = authenticate_windows_user(credentials.username, credentials.password)

    if ad_user:
        # AD authentication successful
        # Check if employee exists in local database
        employee = crud.get_employee_by_windows_login(db, credentials.username)

        if not employee:
            # Auto-create employee from AD
            try:
                employee_data = schemas.EmployeeCreate(
                    employee_name=ad_user['display_name'] or credentials.username,
                    email=ad_user['email'],
                    windows_login=credentials.username,
                    is_active=True
                )

                employee = crud.create_employee(db, employee_data)

                # Set default role to User (admins must be manually promoted)
                employee.role = 'User'
                db.commit()
                db.refresh(employee)

                print(f"Auto-created employee from AD: {employee.employee_name}")

            except Exception as e:
                print(f"Error auto-creating employee: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user account"
                )
    else:
        # AD authentication failed or not configured, try local authentication
        employee = crud.authenticate_employee(db, credentials.username, credentials.password)

    # Check if authentication was successful
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not employee.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Create access token
    access_token = create_access_token(
        data={"sub": str(employee.employee_id), "role": employee.role}
    )

    # Update last login timestamp
    crud.update_last_login(db, employee.employee_id)

    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/auth/me", response_model=schemas.UserInfo)
def get_current_user_info(
    current_user: models.Employee = Depends(get_current_user)
):
    """
    Get current authenticated user information.

    Requires valid JWT token in Authorization header.
    """
    return current_user


@app.post("/api/auth/logout")
def logout():
    """
    Logout endpoint (stateless JWT - token removal handled client-side).

    Returns success message. Client should remove token from storage.
    """
    return {"message": "Logged out successfully"}


# ============================================================================
# Amendment Endpoints
# ============================================================================


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
        application=application.split(",") if application else None,
        assigned_to=assigned_to.split(",") if assigned_to else None,
        reported_by=reported_by.split(",") if reported_by else None,
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


@app.get("/api/amendments/version-stats")
def get_version_stats_endpoint(db: Session = Depends(get_db)):
    """
    Get amendment counts grouped by application and version.

    Returns a list of version statistics showing how many amendments exist for each version.
    """
    version_stats = crud.get_version_stats(db)
    return version_stats


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


@app.get("/api/employees/search", response_model=List[schemas.EmployeeResponse])
def search_employees_for_mention_endpoint(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Search employees for @mention autocomplete.

    Args:
        q: Search query string
        limit: Maximum number of results

    Returns:
        List of matching active employees
    """
    from sqlalchemy import or_

    employees = (
        db.query(models.Employee)
        .filter(
            or_(
                models.Employee.employee_name.ilike(f"%{q}%"),
                models.Employee.username.ilike(f"%{q}%")
            ),
            models.Employee.is_active == True
        )
        .limit(limit)
        .all()
    )
    return employees


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


@app.get("/api/application-versions", response_model=List[schemas.ApplicationVersionResponse])
def get_all_application_versions_endpoint(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum number of records"),
    active_only: bool = Query(False, description="Filter to only active versions"),
    db: Session = Depends(get_db),
):
    """
    Get all application versions across all applications.
    """
    versions, total = crud.get_all_application_versions(db, skip=skip, limit=limit, active_only=active_only)
    return versions


@app.post("/api/application-versions", response_model=schemas.ApplicationVersionResponse, status_code=201)
def create_application_version_direct(
    version: schemas.ApplicationVersionCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new application version (with application_id in body).
    """
    # Verify application exists
    application = crud.get_application(db, version.application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")

    try:
        db_version = crud.create_application_version(db, version)
        return db_version
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/application-versions/{version_id}", response_model=schemas.ApplicationVersionResponse)
def update_application_version_direct(
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


@app.delete("/api/application-versions/{version_id}", status_code=204)
def delete_application_version_direct(version_id: int, db: Session = Depends(get_db)):
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
def get_next_reference(
    amendment_type: str = Query(..., description="Amendment type (Bug, Fault, Enhancement, etc.)"),
    db: Session = Depends(get_db)
):
    """
    Get the next available amendment reference number for a given type.

    Useful for pre-filling forms before creating an amendment.
    """
    from .models import AmendmentType

    # Convert string to AmendmentType enum
    try:
        amd_type = AmendmentType(amendment_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid amendment type: {amendment_type}")

    next_ref = crud.get_next_reference(db, amd_type)
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


@app.get("/api/reference/document-types", response_model=List[str])
def get_document_types():
    """Get all available document types."""
    from .models import DocumentType
    return [doc_type.value for doc_type in DocumentType]


@app.get("/api/reference-data")
def get_all_reference_data(db: Session = Depends(get_db)):
    """Get all reference data from database."""
    return crud.get_all_reference_data(db)


# ============================================================================
# Reference Data Management Endpoints
# ============================================================================


@app.get("/api/forces")
def get_forces_endpoint(active_only: bool = Query(False), db: Session = Depends(get_db)):
    """Get all force references."""
    forces = crud.get_forces(db, active_only=active_only)
    return forces


@app.post("/api/forces", status_code=201)
def create_force_endpoint(force_name: str, sort_order: int = 0, db: Session = Depends(get_db)):
    """Create a new force reference."""
    try:
        force = crud.create_force(db, force_name, sort_order)
        return force
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/forces/{force_id}")
def update_force_endpoint(
    force_id: int,
    force_name: str = None,
    is_active: bool = None,
    sort_order: int = None,
    db: Session = Depends(get_db)
):
    """Update a force reference."""
    try:
        force = crud.update_force(db, force_id, force_name, is_active, sort_order)
        if not force:
            raise HTTPException(status_code=404, detail="Force not found")
        return force
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/forces/{force_id}", status_code=204)
def delete_force_endpoint(force_id: int, db: Session = Depends(get_db)):
    """Delete a force reference."""
    try:
        success = crud.delete_force(db, force_id)
        if not success:
            raise HTTPException(status_code=404, detail="Force not found")
        return None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/priorities")
def get_priorities_endpoint(active_only: bool = Query(False), db: Session = Depends(get_db)):
    """Get all priority references."""
    priorities = crud.get_priorities(db, active_only=active_only)
    return priorities


@app.post("/api/priorities", status_code=201)
def create_priority_endpoint(priority_name: str, sort_order: int = 0, db: Session = Depends(get_db)):
    """Create a new priority reference."""
    try:
        priority = crud.create_priority(db, priority_name, sort_order)
        return priority
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/priorities/{priority_id}")
def update_priority_endpoint(
    priority_id: int,
    priority_name: str = None,
    is_active: bool = None,
    sort_order: int = None,
    db: Session = Depends(get_db)
):
    """Update a priority reference."""
    try:
        priority = crud.update_priority(db, priority_id, priority_name, is_active, sort_order)
        if not priority:
            raise HTTPException(status_code=404, detail="Priority not found")
        return priority
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/priorities/{priority_id}", status_code=204)
def delete_priority_endpoint(priority_id: int, db: Session = Depends(get_db)):
    """Delete a priority reference."""
    try:
        success = crud.delete_priority(db, priority_id)
        if not success:
            raise HTTPException(status_code=404, detail="Priority not found")
        return None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/statuses")
def get_statuses_endpoint(
    status_type: str = Query(None, description="Filter by type: 'amendment' or 'development'"),
    active_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Get all status references."""
    statuses = crud.get_statuses(db, status_type=status_type, active_only=active_only)
    return statuses


@app.post("/api/statuses", status_code=201)
def create_status_endpoint(
    status_name: str,
    status_type: str,
    sort_order: int = 0,
    db: Session = Depends(get_db)
):
    """Create a new status reference."""
    if status_type not in ["amendment", "development"]:
        raise HTTPException(status_code=400, detail="status_type must be 'amendment' or 'development'")
    try:
        status = crud.create_status(db, status_name, status_type, sort_order)
        return status
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/statuses/{status_id}")
def update_status_endpoint(
    status_id: int,
    status_name: str = None,
    is_active: bool = None,
    sort_order: int = None,
    db: Session = Depends(get_db)
):
    """Update a status reference."""
    try:
        status = crud.update_status(db, status_id, status_name, is_active, sort_order)
        if not status:
            raise HTTPException(status_code=404, detail="Status not found")
        return status
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/statuses/{status_id}", status_code=204)
def delete_status_endpoint(status_id: int, db: Session = Depends(get_db)):
    """Delete a status reference."""
    try:
        success = crud.delete_status(db, status_id)
        if not success:
            raise HTTPException(status_code=404, detail="Status not found")
        return None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Document Endpoints
# ============================================================================

# Configure upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@app.post("/api/amendments/{amendment_id}/documents", response_model=schemas.AmendmentDocumentResponse, status_code=201)
async def upload_amendment_document(
    amendment_id: int,
    file: UploadFile = File(...),
    document_name: str = Query(..., description="Display name for the document"),
    document_type: str = Query("Other", description="Type of document"),
    description: str = Query(None, description="Document description"),
    uploaded_by: str = Query(None, description="Username of uploader"),
    db: Session = Depends(get_db),
):
    """
    Upload a document file for an amendment.

    The file will be saved to the uploads directory and a database record created.
    """
    # Verify amendment exists
    amendment = crud.get_amendment(db, amendment_id)
    if amendment is None:
        raise HTTPException(status_code=404, detail="Amendment not found")

    # Create amendment-specific directory
    amendment_dir = UPLOAD_DIR / f"amendment_{amendment_id}"
    amendment_dir.mkdir(exist_ok=True)

    # Generate unique filename
    file_extension = Path(file.filename).suffix
    import uuid
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = amendment_dir / unique_filename

    # Save file
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Get file size
    file_size = file_path.stat().st_size

    # Create database record
    from .models import DocumentType as DocTypeEnum

    # Convert string to enum
    try:
        doc_type_enum = DocTypeEnum(document_type)
    except ValueError:
        doc_type_enum = DocTypeEnum.OTHER

    document_data = schemas.AmendmentDocumentCreate(
        document_name=document_name,
        original_filename=file.filename,
        file_path=str(file_path.relative_to(UPLOAD_DIR)),
        file_size=file_size,
        mime_type=file.content_type,
        document_type=doc_type_enum,
        description=description,
        uploaded_by=uploaded_by,
    )

    try:
        db_document = crud.create_amendment_document(db, amendment_id, document_data)
        return db_document
    except ValueError as e:
        # If database creation fails, delete the uploaded file
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/amendments/{amendment_id}/documents", response_model=List[schemas.AmendmentDocumentResponse])
def get_amendment_documents_list(
    amendment_id: int,
    db: Session = Depends(get_db),
):
    """
    Get all documents for a specific amendment.
    """
    documents = crud.get_amendment_documents(db, amendment_id)
    return documents


@app.get("/api/documents/{document_id}/download")
async def download_amendment_document(
    document_id: int,
    db: Session = Depends(get_db),
):
    """
    Download a specific document file.
    """
    document = crud.get_amendment_document(db, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = UPLOAD_DIR / document.file_path
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=str(file_path),
        filename=document.original_filename,
        media_type=document.mime_type or "application/octet-stream",
    )


@app.delete("/api/documents/{document_id}", status_code=204)
def delete_amendment_document_endpoint(
    document_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a document and its file.
    """
    # Get document to find file path
    document = crud.get_amendment_document(db, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete file from disk
    file_path = UPLOAD_DIR / document.file_path
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception as e:
            # Log error but continue with database deletion
            print(f"Warning: Failed to delete file {file_path}: {e}")

    # Delete database record
    try:
        success = crud.delete_amendment_document(db, document_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Amendment Application Endpoints
# ============================================================================


@app.post("/api/amendments/{amendment_id}/applications", response_model=schemas.AmendmentApplicationResponse, status_code=201)
def add_amendment_application(
    amendment_id: int,
    app_data: schemas.AmendmentApplicationCreate,
    db: Session = Depends(get_db),
):
    """
    Add an application to an amendment.
    """
    try:
        result = crud.add_amendment_application(db, amendment_id, app_data)
        if result is None:
            raise HTTPException(status_code=404, detail="Amendment not found")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/amendments/{amendment_id}/applications", response_model=List[schemas.AmendmentApplicationResponse])
def get_amendment_applications(
    amendment_id: int,
    db: Session = Depends(get_db),
):
    """
    Get all applications for an amendment.
    """
    return crud.get_amendment_applications(db, amendment_id)


@app.put("/api/amendment-applications/{app_link_id}", response_model=schemas.AmendmentApplicationResponse)
def update_amendment_application(
    app_link_id: int,
    app_data: schemas.AmendmentApplicationCreate,
    db: Session = Depends(get_db),
):
    """
    Update an amendment application link.
    """
    try:
        result = crud.update_amendment_application(db, app_link_id, app_data)
        if result is None:
            raise HTTPException(status_code=404, detail="Amendment application not found")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/amendment-applications/{app_link_id}", status_code=204)
def delete_amendment_application(
    app_link_id: int,
    db: Session = Depends(get_db),
):
    """
    Remove an application from an amendment.
    """
    try:
        success = crud.delete_amendment_application(db, app_link_id)
        if not success:
            raise HTTPException(status_code=404, detail="Amendment application not found")
        return None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# QA System Endpoints
# ============================================================================

# Import QA workflow validator
from .qa_workflow import validate_qa_status_change, get_allowed_qa_statuses


# ============================================================================
# QA Test Case Endpoints
# ============================================================================


@app.post("/api/test-cases", response_model=schemas.QATestCaseResponse, status_code=201)
def create_test_case_endpoint(
    test_case: schemas.QATestCaseCreate,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Create a new test case.
    
    Generates automatic test case number (TC-001, TC-002, etc.).
    """
    try:
        return crud.create_test_case(db, test_case, created_by=current_user.employee_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/test-cases", response_model=schemas.QATestCaseListResponse)
def get_test_cases_endpoint(
    test_type: Optional[str] = Query(None, description="Filter by test type"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    application_id: Optional[int] = Query(None, description="Filter by application"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Get test cases with filtering and pagination.
    
    Supports filters for test type, priority, application, active status, and text search.
    """
    test_cases, total = crud.get_test_cases(
        db=db,
        test_type=test_type,
        priority=priority,
        application_id=application_id,
        is_active=is_active,
        search=search,
        skip=skip,
        limit=limit,
    )
    
    return {
        "items": test_cases,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@app.get("/api/test-cases/{test_case_id}", response_model=schemas.QATestCaseResponse)
def get_test_case_endpoint(
    test_case_id: int,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Get a test case by ID.
    """
    test_case = crud.get_test_case(db, test_case_id)
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    return test_case


@app.put("/api/test-cases/{test_case_id}", response_model=schemas.QATestCaseResponse)
def update_test_case_endpoint(
    test_case_id: int,
    test_case_update: schemas.QATestCaseUpdate,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Update an existing test case.
    """
    try:
        updated = crud.update_test_case(
            db, test_case_id, test_case_update, modified_by=current_user.employee_name
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Test case not found")
        return updated
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/test-cases/{test_case_id}", status_code=204)
def delete_test_case_endpoint(
    test_case_id: int,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(require_admin),  # Admin only
):
    """
    Delete a test case.
    
    **Admin only** - Requires admin role.
    """
    success = crud.delete_test_case(db, test_case_id)
    if not success:
        raise HTTPException(status_code=404, detail="Test case not found")
    return None


@app.get("/api/test-cases/stats", response_model=dict)
def get_test_case_stats_endpoint(
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Get test case statistics.
    """
    total_test_cases = db.query(models.QATestCase).count()
    active_test_cases = db.query(models.QATestCase).filter(models.QATestCase.is_active == True).count()
    automated_test_cases = db.query(models.QATestCase).filter(models.QATestCase.is_automated == True).count()
    
    return {
        "total_test_cases": total_test_cases,
        "active_test_cases": active_test_cases,
        "automated_test_cases": automated_test_cases,
        "manual_test_cases": total_test_cases - automated_test_cases,
    }


# ============================================================================
# QA Test Execution Endpoints
# ============================================================================


@app.post("/api/amendments/{amendment_id}/test-executions", response_model=schemas.QATestExecutionResponse, status_code=201)
def link_test_to_amendment_endpoint(
    amendment_id: int,
    test_execution: schemas.QATestExecutionCreate,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Link a test case to an amendment for execution.
    
    Creates a test execution record that can later be executed with results.
    """
    # Verify amendment exists
    amendment = crud.get_amendment(db, amendment_id)
    if not amendment:
        raise HTTPException(status_code=404, detail="Amendment not found")
    
    # Override amendment_id from URL
    test_execution.amendment_id = amendment_id
    
    try:
        return crud.create_test_execution(db, test_execution, created_by=current_user.employee_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/amendments/{amendment_id}/test-executions", response_model=schemas.QATestExecutionListResponse)
def get_amendment_test_executions_endpoint(
    amendment_id: int,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Get all test executions for an amendment.
    
    Includes test case details and execution results.
    """
    # Verify amendment exists
    amendment = crud.get_amendment(db, amendment_id)
    if not amendment:
        raise HTTPException(status_code=404, detail="Amendment not found")
    
    executions = crud.get_test_executions(db, amendment_id)
    
    return {
        "items": executions,
        "total": len(executions),
    }


@app.patch("/api/test-executions/{execution_id}", response_model=schemas.QATestExecutionResponse)
def update_test_execution_endpoint(
    execution_id: int,
    execution_update: schemas.QATestExecutionUpdate,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Update a test execution.
    """
    try:
        updated = crud.update_test_execution(
            db, execution_id, execution_update, modified_by=current_user.employee_name
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Test execution not found")
        return updated
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/test-executions/{execution_id}/execute", response_model=schemas.QATestExecutionResponse)
def execute_test_endpoint(
    execution_id: int,
    execute_request: schemas.QATestExecutionExecuteRequest,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Execute a test and record results.
    
    Records test execution status (Passed/Failed/Blocked), actual results, and metadata.
    Creates QA history entry automatically.
    """
    try:
        executed = crud.execute_test(
            db, execution_id, execute_request, modified_by=current_user.employee_name
        )
        if not executed:
            raise HTTPException(status_code=404, detail="Test execution not found")
        return executed
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/test-executions/bulk-execute", response_model=List[schemas.QATestExecutionResponse])
def bulk_execute_tests_endpoint(
    execution_ids: List[int],
    execute_request: schemas.QATestExecutionExecuteRequest,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Execute multiple tests with the same results.
    
    Useful for marking multiple tests as passed/failed/blocked in bulk.
    """
    results = []
    errors = []
    
    for execution_id in execution_ids:
        try:
            executed = crud.execute_test(
                db, execution_id, execute_request, modified_by=current_user.employee_name
            )
            if executed:
                results.append(executed)
            else:
                errors.append(f"Execution {execution_id} not found")
        except Exception as e:
            errors.append(f"Execution {execution_id}: {str(e)}")
    
    if errors:
        raise HTTPException(
            status_code=400,
            detail=f"Some executions failed: {'; '.join(errors)}"
        )
    
    return results


# ============================================================================
# QA Defect Endpoints
# ============================================================================


@app.post("/api/defects", response_model=schemas.QADefectResponse, status_code=201)
def create_defect_endpoint(
    defect: schemas.QADefectCreate,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Create a new defect.
    
    Generates automatic defect number (DEF-001, DEF-002, etc.).
    Creates QA history entry automatically.
    """
    try:
        return crud.create_defect(db, defect, created_by=current_user.employee_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/defects", response_model=schemas.QADefectListResponse)
def get_defects_endpoint(
    amendment_id: Optional[int] = Query(None, description="Filter by amendment"),
    status: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    assigned_to_id: Optional[int] = Query(None, description="Filter by assigned developer"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Get defects with filtering and pagination.
    
    Supports filters for amendment, status, severity, and assigned developer.
    """
    defects, total = crud.get_defects(
        db=db,
        amendment_id=amendment_id,
        status=status,
        severity=severity,
        assigned_to_id=assigned_to_id,
        skip=skip,
        limit=limit,
    )
    
    return {
        "items": defects,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@app.get("/api/defects/{defect_id}", response_model=schemas.QADefectResponse)
def get_defect_endpoint(
    defect_id: int,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Get a defect by ID.
    
    Includes reporter and assignee information.
    """
    defect = crud.get_defect(db, defect_id)
    if not defect:
        raise HTTPException(status_code=404, detail="Defect not found")
    return defect


@app.patch("/api/defects/{defect_id}", response_model=schemas.QADefectResponse)
def update_defect_endpoint(
    defect_id: int,
    defect_update: schemas.QADefectUpdate,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Update an existing defect.
    
    Tracks status transitions (e.g., sets resolved_date when status = Resolved).
    Creates QA history entry for status changes.
    """
    try:
        updated = crud.update_defect(
            db, defect_id, defect_update, modified_by=current_user.employee_name
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Defect not found")
        return updated
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/defects/{defect_id}", status_code=204)
def delete_defect_endpoint(
    defect_id: int,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(require_admin),  # Admin only
):
    """
    Delete a defect.
    
    **Admin only** - Requires admin role.
    """
    success = crud.delete_defect(db, defect_id)
    if not success:
        raise HTTPException(status_code=404, detail="Defect not found")
    return None


@app.get("/api/defects/stats", response_model=dict)
def get_defect_stats_endpoint(
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Get defect statistics.
    """
    total_defects = db.query(models.QADefect).count()
    
    by_status = {}
    for status_val in ["New", "Assigned", "In Progress", "Resolved", "Verified", "Closed", "Reopened"]:
        count = db.query(models.QADefect).filter(models.QADefect.status == status_val).count()
        by_status[status_val] = count
    
    by_severity = {}
    for severity_val in ["Critical", "High", "Medium", "Low"]:
        count = db.query(models.QADefect).filter(models.QADefect.severity == severity_val).count()
        by_severity[severity_val] = count
    
    return {
        "total_defects": total_defects,
        "by_status": by_status,
        "by_severity": by_severity,
    }


# ============================================================================
# QA History Endpoints
# ============================================================================


@app.get("/api/amendments/{amendment_id}/qa-history", response_model=schemas.QAHistoryListResponse)
def get_qa_history_endpoint(
    amendment_id: int,
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records"),
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Get QA history (audit trail) for an amendment.
    
    Returns chronological list of all QA-related changes and events.
    """
    # Verify amendment exists
    amendment = crud.get_amendment(db, amendment_id)
    if not amendment:
        raise HTTPException(status_code=404, detail="Amendment not found")
    
    history = crud.get_qa_history(db, amendment_id, limit=limit)
    
    return {
        "items": history,
        "total": len(history),
    }


@app.get("/api/amendments/{amendment_id}/qa-timeline", response_model=schemas.QATimelineResponse)
def get_qa_timeline_endpoint(
    amendment_id: int,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Get QA timeline for visual representation.
    
    Returns formatted timeline events suitable for UI visualization.
    """
    # Verify amendment exists
    amendment = crud.get_amendment(db, amendment_id)
    if not amendment:
        raise HTTPException(status_code=404, detail="Amendment not found")
    
    history = crud.get_qa_history(db, amendment_id, limit=100)
    
    # Convert history to timeline events
    events = []
    for entry in history:
        event = schemas.QATimelineEvent(
            event_id=entry.history_id,
            event_type=entry.action.lower().replace(" ", "_"),
            timestamp=entry.changed_on,
            title=entry.action,
            description=entry.comment,
            actor=entry.changed_by.employee_name if entry.changed_by else None,
            metadata={
                "field_name": entry.field_name,
                "old_value": entry.old_value,
                "new_value": entry.new_value,
            } if entry.field_name else None,
        )
        events.append(event)
    
    return {
        "amendment_id": amendment_id,
        "events": events,
    }


# ============================================================================
# QA Notification Endpoints
# ============================================================================


@app.get("/api/notifications", response_model=schemas.QANotificationListResponse)
def get_notifications_endpoint(
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of records"),
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Get notifications for the current user.
    
    Returns notifications sorted by newest first, with unread count.
    """
    notifications, total, unread_count = crud.get_notifications(
        db=db,
        employee_id=current_user.employee_id,
        is_read=is_read,
        skip=skip,
        limit=limit,
    )
    
    return {
        "items": notifications,
        "total": total,
        "unread_count": unread_count,
    }


@app.get("/api/notifications/unread-count", response_model=schemas.QANotificationUnreadCountResponse)
def get_unread_count_endpoint(
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Get count of unread notifications for the current user.
    
    Useful for notification badge display.
    """
    unread_count = crud.get_unread_count(db, current_user.employee_id)
    
    return {
        "unread_count": unread_count,
    }


@app.patch("/api/notifications/{notification_id}/read", response_model=schemas.QANotificationResponse)
def mark_notification_read_endpoint(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Mark a notification as read.
    
    Sets is_read=True and records read_on timestamp.
    """
    notification = crud.mark_notification_read(db, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    # Verify notification belongs to current user
    if notification.employee_id != current_user.employee_id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this notification")
    
    return notification


@app.post("/api/notifications/mark-all-read", response_model=dict)
def mark_all_notifications_read_endpoint(
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Mark all notifications as read for the current user.
    """
    count = crud.mark_all_notifications_read(db, current_user.employee_id)
    
    return {
        "marked_read": count,
        "message": f"Marked {count} notifications as read",
    }


@app.delete("/api/notifications/{notification_id}", status_code=204)
def delete_notification_endpoint(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Delete a notification.
    """
    # Get notification to verify ownership
    notification = db.query(models.QANotification).filter(
        models.QANotification.notification_id == notification_id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    # Verify notification belongs to current user
    if notification.employee_id != current_user.employee_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this notification")
    
    success = crud.delete_notification(db, notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")

    return None


# ============================================================================
# QA Comment Endpoints
# ============================================================================


@app.post("/api/amendments/{amendment_id}/qa-comments", response_model=schemas.QACommentResponse)
def create_qa_comment_endpoint(
    amendment_id: int,
    comment: schemas.QACommentCreate,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
    parent_comment_id: Optional[int] = Query(None, description="Parent comment ID for threading"),  # NEW: For threading
):
    """
    Create a QA comment for an amendment with threading and mention support.

    Args:
        amendment_id: Amendment ID
        comment: Comment data
        parent_comment_id: Parent comment ID for threading (optional)

    Returns:
        Created comment with mentions and watcher notifications
    """
    # Verify amendment exists
    amendment = crud.get_amendment(db, amendment_id)
    if not amendment:
        raise HTTPException(status_code=404, detail="Amendment not found")

    # Verify parent comment exists if provided
    if parent_comment_id:
        parent_comment = crud.get_qa_comment(db, parent_comment_id)
        if not parent_comment or parent_comment.amendment_id != amendment_id:
            raise HTTPException(status_code=404, detail="Parent comment not found")

    # Use enhanced comment creation with mentions and notifications
    db_comment = crud.create_qa_comment_enhanced(
        db,
        amendment_id=amendment_id,
        employee_id=current_user.employee_id,
        comment_text=comment.comment_text,
        comment_type=comment.comment_type,
        parent_comment_id=parent_comment_id
    )

    # Attach employee name for response
    db_comment.employee_name = current_user.employee_name

    return db_comment


@app.get("/api/amendments/{amendment_id}/qa-comments", response_model=schemas.QACommentListResponse)
def get_qa_comments_endpoint(
    amendment_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Get all QA comments for an amendment.

    Args:
        amendment_id: Amendment ID
        skip: Number of records to skip (default: 0)
        limit: Maximum number of records to return (default: 100)

    Returns:
        List of comments
    """
    # Verify amendment exists
    amendment = crud.get_amendment(db, amendment_id)
    if not amendment:
        raise HTTPException(status_code=404, detail="Amendment not found")

    comments = crud.get_qa_comments_for_amendment(db, amendment_id, skip, limit)
    total = crud.count_qa_comments_for_amendment(db, amendment_id)

    # Attach employee names
    for comment in comments:
        employee = db.query(models.Employee).filter(
            models.Employee.employee_id == comment.employee_id
        ).first()
        if employee:
            comment.employee_name = employee.employee_name

    return schemas.QACommentListResponse(items=comments, total=total)


@app.patch("/api/qa-comments/{comment_id}", response_model=schemas.QACommentResponse)
def update_qa_comment_endpoint(
    comment_id: int,
    comment_update: schemas.QACommentUpdate,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Update a QA comment.

    Args:
        comment_id: Comment ID
        comment_update: Comment update data

    Returns:
        Updated comment
    """
    # Get comment
    db_comment = crud.get_qa_comment(db, comment_id)
    if not db_comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Verify comment belongs to current user
    if db_comment.employee_id != current_user.employee_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this comment")

    updated_comment = crud.update_qa_comment(db, comment_id, comment_update)

    # Attach employee name
    updated_comment.employee_name = current_user.employee_name

    return updated_comment


@app.delete("/api/qa-comments/{comment_id}", status_code=204)
def delete_qa_comment_endpoint(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Delete a QA comment.

    Args:
        comment_id: Comment ID
    """
    # Get comment
    db_comment = crud.get_qa_comment(db, comment_id)
    if not db_comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Verify comment belongs to current user (or user is admin - you can add role check here)
    if db_comment.employee_id != current_user.employee_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")

    success = crud.delete_qa_comment(db, comment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Comment not found")

    return None


# ============================================================================
# GitHub Issues Features - Comment Mentions
# ============================================================================


@app.get("/api/comments/{comment_id}/mentions", response_model=List[schemas.CommentMentionResponse])
def get_comment_mentions_endpoint(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """Get all mentions for a comment."""
    mentions = crud.get_mentions_for_comment(db, comment_id)
    return mentions


# ============================================================================
# GitHub Issues Features - Amendment Watchers
# ============================================================================


@app.post("/api/amendments/{amendment_id}/watchers", response_model=schemas.AmendmentWatcherResponse)
def watch_amendment_endpoint(
    amendment_id: int,
    watcher_data: schemas.AmendmentWatcherCreate,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Watch an amendment (subscribe for notifications).

    Args:
        amendment_id: Amendment ID to watch
        watcher_data: Watcher preferences

    Returns:
        Watcher record
    """
    # Verify amendment exists
    amendment = crud.get_amendment(db, amendment_id)
    if not amendment:
        raise HTTPException(status_code=404, detail="Amendment not found")

    watcher = crud.add_watcher(
        db,
        amendment_id,
        current_user.employee_id,
        watcher_data.watch_reason
    )

    # Attach employee name
    watcher.employee_name = current_user.employee_name

    return watcher


@app.delete("/api/amendments/{amendment_id}/watchers", status_code=204)
def unwatch_amendment_endpoint(
    amendment_id: int,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Unwatch an amendment (unsubscribe from notifications).

    Args:
        amendment_id: Amendment ID to unwatch
    """
    crud.remove_watcher(db, amendment_id, current_user.employee_id)
    return None


@app.get("/api/amendments/{amendment_id}/watchers", response_model=List[schemas.AmendmentWatcherResponse])
def get_amendment_watchers_endpoint(
    amendment_id: int,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Get all watchers for an amendment.

    Args:
        amendment_id: Amendment ID

    Returns:
        List of watchers
    """
    watchers = crud.get_watchers(db, amendment_id)

    # Attach employee names
    for watcher in watchers:
        employee = db.query(models.Employee).filter(models.Employee.employee_id == watcher.employee_id).first()
        if employee:
            watcher.employee_name = employee.employee_name

    return watchers


@app.get("/api/amendments/{amendment_id}/is-watching")
def check_if_watching_endpoint(
    amendment_id: int,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Check if current user is watching an amendment.

    Args:
        amendment_id: Amendment ID

    Returns:
        {"is_watching": bool}
    """
    is_watching = crud.is_watching(db, amendment_id, current_user.employee_id)
    return {"is_watching": is_watching}


@app.patch("/api/amendments/{amendment_id}/watchers", response_model=schemas.AmendmentWatcherResponse)
def update_watcher_preferences_endpoint(
    amendment_id: int,
    update_data: schemas.AmendmentWatcherUpdate,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Update watcher notification preferences.

    Args:
        amendment_id: Amendment ID
        update_data: Preference updates

    Returns:
        Updated watcher record
    """
    watcher = (
        db.query(models.AmendmentWatcher)
        .filter(
            models.AmendmentWatcher.amendment_id == amendment_id,
            models.AmendmentWatcher.employee_id == current_user.employee_id
        )
        .first()
    )

    if not watcher:
        raise HTTPException(status_code=404, detail="Not watching this amendment")

    if update_data.is_watching is not None:
        watcher.is_watching = update_data.is_watching
    if update_data.notify_comments is not None:
        watcher.notify_comments = update_data.notify_comments
    if update_data.notify_status_changes is not None:
        watcher.notify_status_changes = update_data.notify_status_changes
    if update_data.notify_mentions is not None:
        watcher.notify_mentions = update_data.notify_mentions

    db.commit()
    db.refresh(watcher)

    # Attach employee name
    watcher.employee_name = current_user.employee_name

    return watcher


@app.get("/api/employees/{employee_id}/watching", response_model=List[int])
def get_user_watched_amendments_endpoint(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Get all amendments a user is watching.

    Args:
        employee_id: Employee ID (must be current user or admin)

    Returns:
        List of amendment IDs
    """
    # Users can only get their own watched amendments (unless admin)
    if employee_id != current_user.employee_id:
        # TODO: Add admin check here if needed
        raise HTTPException(status_code=403, detail="Not authorized")

    watchers = (
        db.query(models.AmendmentWatcher)
        .filter(
            models.AmendmentWatcher.employee_id == employee_id,
            models.AmendmentWatcher.is_watching == True
        )
        .all()
    )

    return [w.amendment_id for w in watchers]


# ============================================================================
# GitHub Issues Features - Comment Reactions
# ============================================================================


@app.post("/api/comments/{comment_id}/reactions")
def toggle_comment_reaction_endpoint(
    comment_id: int,
    emoji: str = Query(..., min_length=1, max_length=10, description="Emoji to react with"),
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Toggle reaction on a comment.

    Args:
        comment_id: Comment ID
        emoji: Emoji to toggle

    Returns:
        {"added": bool, "reaction": Optional[reaction]}
    """
    # Verify comment exists
    comment = crud.get_qa_comment(db, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    reaction = crud.toggle_reaction(
        db,
        comment_id,
        current_user.employee_id,
        emoji
    )

    is_added = reaction is not None

    if reaction:
        reaction.employee_name = current_user.employee_name

    return {
        "added": is_added,
        "reaction": reaction
    }


@app.get("/api/comments/{comment_id}/reactions", response_model=List[schemas.CommentReactionResponse])
def get_comment_reactions_endpoint(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Get all reactions for a comment.

    Args:
        comment_id: Comment ID

    Returns:
        List of reactions
    """
    reactions = crud.get_reactions_for_comment(db, comment_id)

    # Attach employee names
    for reaction in reactions:
        employee = db.query(models.Employee).filter(models.Employee.employee_id == reaction.employee_id).first()
        if employee:
            reaction.employee_name = employee.employee_name

    return reactions


@app.get("/api/comments/{comment_id}/reactions/summary")
def get_comment_reaction_summary_endpoint(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Get reaction summary for a comment.

    Args:
        comment_id: Comment ID

    Returns:
        {"reactions": {"👍": 5, "❤️": 2}}
    """
    summary = crud.get_reaction_summary(db, comment_id)
    return {"reactions": summary}


# ============================================================================
# QA Dashboard & Reporting Endpoints
# ============================================================================


@app.get("/api/qa/dashboard", response_model=schemas.QADashboardResponse)
def get_qa_dashboard_endpoint(
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Get QA dashboard data for the current user.
    
    Returns:
    - Amendments assigned to me
    - Amendments in testing
    - Overdue amendments
    - Completed this week count
    - Summary statistics
    """
    dashboard_data = crud.get_qa_dashboard(db, current_user.employee_id)
    
    return dashboard_data


@app.get("/api/qa/metrics", response_model=schemas.QAMetricsResponse)
def get_qa_metrics_endpoint(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Get QA metrics and analytics.
    
    Returns:
    - Test pass/fail rates
    - Defect statistics by severity and status
    - Time metrics (time to test, test duration)
    - SLA compliance percentage
    """
    metrics = crud.get_qa_metrics(db, days=days)
    
    return metrics


@app.get("/api/qa/calendar", response_model=schemas.QACalendarResponse)
def get_qa_calendar_endpoint(
    employee_id: Optional[int] = Query(None, description="Filter by QA tester (leave blank for all)"),
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Get QA calendar events (amendments with due dates).
    
    Returns events suitable for calendar display.
    Can be filtered to show only events for a specific QA tester.
    """
    # If no employee_id specified, show events for current user
    if employee_id is None:
        employee_id = current_user.employee_id
    
    events = crud.get_qa_calendar_events(db, employee_id=employee_id)
    
    return {
        "events": events,
        "total": len(events),
    }


@app.get("/api/qa/workload", response_model=schemas.QAWorkloadResponse)
def get_qa_workload_endpoint(
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Get QA team workload distribution.
    
    Returns workload metrics for all QA testers:
    - Total assigned
    - In testing count
    - Overdue count
    - Completed this week
    - Average completion time
    """
    workload = crud.get_tester_workload(db)
    
    return {
        "testers": workload,
        "total_testers": len(workload),
    }


# ============================================================================
# QA Workflow Helper Endpoints
# ============================================================================


@app.get("/api/qa/workflow/allowed-statuses/{current_status}", response_model=List[str])
def get_allowed_qa_statuses_endpoint(
    current_status: str,
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Get allowed next QA statuses from the current status.
    
    Helps UI show only valid status transitions.
    """
    allowed = get_allowed_qa_statuses(current_status)
    return allowed


@app.get("/api/qa/workflow/help", response_model=dict)
def get_qa_workflow_help_endpoint(
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Get QA workflow documentation.
    
    Returns workflow rules, status descriptions, and requirements.
    """
    from .qa_workflow import QAWorkflowValidator
    return QAWorkflowValidator.get_workflow_help()


@app.post("/api/qa/workflow/validate-transition", response_model=dict)
def validate_qa_transition_endpoint(
    amendment_id: int,
    new_status: str,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Validate if a QA status transition is allowed for an amendment.
    
    Returns validation result with detailed error messages if invalid.
    Useful for frontend validation before attempting status change.
    """
    # Get amendment
    amendment = crud.get_amendment(db, amendment_id)
    if not amendment:
        raise HTTPException(status_code=404, detail="Amendment not found")
    
    # Validate transition
    is_valid, error_message = validate_qa_status_change(amendment, new_status)
    
    return {
        "is_valid": is_valid,
        "error_message": error_message,
        "current_status": amendment.qa_status,
        "new_status": new_status,
    }


# ============================================================================
# Version Management & Progress Endpoints
# ============================================================================


@app.get("/api/versions", response_model=List[str])
def get_all_versions_endpoint(
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Get all unique versions from amendments.

    Returns:
        List of unique version strings
    """
    versions = (
        db.query(models.Amendment.version)
        .filter(models.Amendment.version.isnot(None))
        .distinct()
        .order_by(models.Amendment.version)
        .all()
    )

    return [v[0] for v in versions if v[0]]


@app.get("/api/versions/{version}/amendments", response_model=schemas.AmendmentListResponse)
def get_amendments_by_version_endpoint(
    version: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Get all amendments for a specific version.

    Args:
        version: Version string (e.g., "Centurion 7.5")
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of amendments for the version
    """
    # Create filter with version
    filters = schemas.AmendmentFilter(
        version=[version],
        skip=skip,
        limit=limit,
        sort_by="amendment_id",
        sort_order="desc",
    )

    amendments, total = crud.get_amendments(db, filters)

    return schemas.AmendmentListResponse(items=amendments, total=total)


@app.get("/api/amendments/{amendment_id}/qa-progress", response_model=dict)
def get_amendment_qa_progress_endpoint(
    amendment_id: int,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Get QA progress for an amendment.

    Returns:
        Progress information including:
        - Test execution stats (total, passed, failed, blocked, not run)
        - Progress percentage
        - Checklist completion
        - Overall status
    """
    # Verify amendment exists
    amendment = crud.get_amendment(db, amendment_id)
    if not amendment:
        raise HTTPException(status_code=404, detail="Amendment not found")

    progress = crud.calculate_qa_progress(db, amendment_id)

    return progress
