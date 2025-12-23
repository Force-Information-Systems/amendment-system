"""
CRUD operations for the Amendment System.

This module provides comprehensive database operations for amendments,
progress tracking, applications, and links.
"""

from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, and_, desc, asc

from .models import (
    Amendment,
    AmendmentProgress,
    AmendmentLink,
    AmendmentStatus,
    DevelopmentStatus,
    Priority,
    AmendmentType,
    Employee,
    Application,
    ApplicationVersion,
)
from .schemas import (
    AmendmentCreate,
    AmendmentUpdate,
    AmendmentQAUpdate,
    AmendmentProgressCreate,
    AmendmentLinkCreate,
    AmendmentFilter,
    EmployeeCreate,
    EmployeeUpdate,
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationVersionCreate,
    ApplicationVersionUpdate,
)


# ============================================================================
# Amendment Reference Number Generation
# ============================================================================


def generate_amendment_reference(db: Session) -> str:
    """
    Generate the next available amendment reference number.

    Reference format: AMD-YYYYMMDD-NNN
    Example: AMD-20231215-001

    Args:
        db: Database session

    Returns:
        str: Generated reference number
    """
    today = datetime.now()
    date_prefix = f"AMD-{today.strftime('%Y%m%d')}"

    # Find the highest sequence number for today
    last_amendment = (
        db.query(Amendment)
        .filter(Amendment.amendment_reference.like(f"{date_prefix}-%"))
        .order_by(desc(Amendment.amendment_reference))
        .first()
    )

    if last_amendment:
        # Extract sequence number and increment
        last_ref = last_amendment.amendment_reference
        last_seq = int(last_ref.split("-")[-1])
        next_seq = last_seq + 1
    else:
        # First amendment today
        next_seq = 1

    return f"{date_prefix}-{next_seq:03d}"


def get_next_reference(db: Session) -> str:
    """
    Get the next available reference number without creating an amendment.

    Args:
        db: Database session

    Returns:
        str: Next available reference number
    """
    return generate_amendment_reference(db)


# ============================================================================
# Amendment CRUD Operations
# ============================================================================


def create_amendment(
    db: Session, amendment: AmendmentCreate, created_by: Optional[str] = None
) -> Amendment:
    """
    Create a new amendment with auto-generated reference number.

    Args:
        db: Database session
        amendment: Amendment creation data
        created_by: Username of the creator

    Returns:
        Amendment: Created amendment with all relationships

    Raises:
        ValueError: If required fields are missing or invalid
    """
    try:
        # Generate unique reference number
        reference = generate_amendment_reference(db)

        # Create amendment model
        db_amendment = Amendment(
            amendment_reference=reference,
            amendment_type=amendment.amendment_type,
            description=amendment.description,
            amendment_status=amendment.amendment_status,
            development_status=amendment.development_status,
            priority=amendment.priority,
            force=amendment.force,
            application=amendment.application,
            notes=amendment.notes,
            reported_by=amendment.reported_by,
            assigned_to=amendment.assigned_to,
            date_reported=amendment.date_reported or datetime.now(),
            database_changes=amendment.database_changes,
            db_upgrade_changes=amendment.db_upgrade_changes,
            release_notes=amendment.release_notes,
            created_by=created_by or amendment.created_by,
        )

        db.add(db_amendment)
        db.commit()
        db.refresh(db_amendment)

        return db_amendment

    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create amendment: {str(e)}") from e


def get_amendment(db: Session, amendment_id: int) -> Optional[Amendment]:
    """
    Get an amendment by ID with all relationships loaded.

    Args:
        db: Database session
        amendment_id: Amendment ID

    Returns:
        Amendment: Amendment object or None if not found
    """
    return (
        db.query(Amendment)
        .options(
            joinedload(Amendment.progress_entries),
            joinedload(Amendment.applications),
            joinedload(Amendment.links),
        )
        .filter(Amendment.amendment_id == amendment_id)
        .first()
    )


def get_amendment_by_reference(db: Session, reference: str) -> Optional[Amendment]:
    """
    Get an amendment by reference number with all relationships loaded.

    Args:
        db: Database session
        reference: Amendment reference number

    Returns:
        Amendment: Amendment object or None if not found
    """
    return (
        db.query(Amendment)
        .options(
            joinedload(Amendment.progress_entries),
            joinedload(Amendment.applications),
            joinedload(Amendment.links),
        )
        .filter(Amendment.amendment_reference == reference)
        .first()
    )


def get_amendments(
    db: Session, filters: Optional[AmendmentFilter] = None
) -> Tuple[List[Amendment], int]:
    """
    Get amendments with advanced filtering, sorting, and pagination.

    Args:
        db: Database session
        filters: Filter criteria and pagination parameters

    Returns:
        Tuple[List[Amendment], int]: List of amendments and total count
    """
    query = db.query(Amendment)

    # Apply filters if provided
    if filters:
        # Filter by reference
        if filters.amendment_reference:
            query = query.filter(
                Amendment.amendment_reference.like(f"%{filters.amendment_reference}%")
            )

        # Filter by IDs
        if filters.amendment_ids:
            query = query.filter(Amendment.amendment_id.in_(filters.amendment_ids))

        # Filter by status
        if filters.amendment_status:
            query = query.filter(
                Amendment.amendment_status.in_(filters.amendment_status)
            )

        # Filter by development status
        if filters.development_status:
            query = query.filter(
                Amendment.development_status.in_(filters.development_status)
            )

        # Filter by priority
        if filters.priority:
            query = query.filter(Amendment.priority.in_(filters.priority))

        # Filter by type
        if filters.amendment_type:
            query = query.filter(Amendment.amendment_type.in_(filters.amendment_type))

        # Filter by force
        if filters.force:
            query = query.filter(Amendment.force.in_(filters.force))

        # Filter by application
        if filters.application:
            query = query.filter(Amendment.application.in_(filters.application))

        # Filter by assigned to
        if filters.assigned_to:
            query = query.filter(Amendment.assigned_to.in_(filters.assigned_to))

        # Filter by reported by
        if filters.reported_by:
            query = query.filter(Amendment.reported_by.in_(filters.reported_by))

        # Filter by date ranges
        if filters.date_reported_from:
            query = query.filter(Amendment.date_reported >= filters.date_reported_from)
        if filters.date_reported_to:
            query = query.filter(Amendment.date_reported <= filters.date_reported_to)
        if filters.created_on_from:
            query = query.filter(Amendment.created_on >= filters.created_on_from)
        if filters.created_on_to:
            query = query.filter(Amendment.created_on <= filters.created_on_to)
        if filters.modified_on_from:
            query = query.filter(Amendment.modified_on >= filters.modified_on_from)
        if filters.modified_on_to:
            query = query.filter(Amendment.modified_on <= filters.modified_on_to)

        # Text search across description, notes, and release notes
        if filters.search_text:
            search_pattern = f"%{filters.search_text}%"
            query = query.filter(
                or_(
                    Amendment.description.like(search_pattern),
                    Amendment.notes.like(search_pattern),
                    Amendment.release_notes.like(search_pattern),
                )
            )

        # QA filters
        if filters.qa_completed is not None:
            query = query.filter(Amendment.qa_completed == filters.qa_completed)
        if filters.qa_assigned is not None:
            if filters.qa_assigned:
                query = query.filter(Amendment.qa_assigned_id.isnot(None))
            else:
                query = query.filter(Amendment.qa_assigned_id.is_(None))

        # Database change filters
        if filters.database_changes is not None:
            query = query.filter(Amendment.database_changes == filters.database_changes)
        if filters.db_upgrade_changes is not None:
            query = query.filter(
                Amendment.db_upgrade_changes == filters.db_upgrade_changes
            )

        # Sorting
        sort_field = getattr(Amendment, filters.sort_by, Amendment.amendment_id)
        if filters.sort_order == "asc":
            query = query.order_by(asc(sort_field))
        else:
            query = query.order_by(desc(sort_field))

    # Get total count before pagination
    total = query.count()

    # Apply pagination
    if filters:
        query = query.offset(filters.skip).limit(filters.limit)

    amendments = query.all()
    return amendments, total


def update_amendment(
    db: Session,
    amendment_id: int,
    amendment_update: AmendmentUpdate,
    modified_by: Optional[str] = None,
) -> Optional[Amendment]:
    """
    Update an amendment with audit tracking.

    Args:
        db: Database session
        amendment_id: Amendment ID to update
        amendment_update: Update data (only provided fields will be updated)
        modified_by: Username of the modifier

    Returns:
        Amendment: Updated amendment or None if not found

    Raises:
        ValueError: If update fails
    """
    try:
        db_amendment = get_amendment(db, amendment_id)
        if not db_amendment:
            return None

        # Update only provided fields
        update_data = amendment_update.model_dump(exclude_unset=True)

        # Set modified_by if provided
        if modified_by:
            update_data["modified_by"] = modified_by
        elif amendment_update.modified_by:
            update_data["modified_by"] = amendment_update.modified_by

        # Apply updates
        for field, value in update_data.items():
            setattr(db_amendment, field, value)

        db.commit()
        db.refresh(db_amendment)

        return db_amendment

    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to update amendment: {str(e)}") from e


def update_amendment_qa(
    db: Session,
    amendment_id: int,
    qa_update: AmendmentQAUpdate,
    modified_by: Optional[str] = None,
) -> Optional[Amendment]:
    """
    Update QA-specific fields of an amendment.

    Args:
        db: Database session
        amendment_id: Amendment ID to update
        qa_update: QA update data
        modified_by: Username of the modifier

    Returns:
        Amendment: Updated amendment or None if not found

    Raises:
        ValueError: If update fails
    """
    try:
        db_amendment = get_amendment(db, amendment_id)
        if not db_amendment:
            return None

        # Update only provided QA fields
        update_data = qa_update.model_dump(exclude_unset=True)

        # Set modified_by if provided
        if modified_by:
            update_data["modified_by"] = modified_by
        elif qa_update.modified_by:
            update_data["modified_by"] = qa_update.modified_by

        # Apply updates
        for field, value in update_data.items():
            setattr(db_amendment, field, value)

        db.commit()
        db.refresh(db_amendment)

        return db_amendment

    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to update QA fields: {str(e)}") from e


def delete_amendment(db: Session, amendment_id: int) -> bool:
    """
    Delete an amendment and all related data (cascade).

    Args:
        db: Database session
        amendment_id: Amendment ID to delete

    Returns:
        bool: True if deleted, False if not found
    """
    try:
        db_amendment = get_amendment(db, amendment_id)
        if not db_amendment:
            return False

        db.delete(db_amendment)
        db.commit()

        return True

    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to delete amendment: {str(e)}") from e


# ============================================================================
# Amendment Progress Operations
# ============================================================================


def add_amendment_progress(
    db: Session,
    amendment_id: int,
    progress: AmendmentProgressCreate,
    created_by: Optional[str] = None,
) -> Optional[AmendmentProgress]:
    """
    Add a progress entry to an amendment.

    Args:
        db: Database session
        amendment_id: Amendment ID
        progress: Progress entry data
        created_by: Username of the creator

    Returns:
        AmendmentProgress: Created progress entry or None if amendment not found

    Raises:
        ValueError: If creation fails
    """
    try:
        # Verify amendment exists
        amendment = get_amendment(db, amendment_id)
        if not amendment:
            return None

        db_progress = AmendmentProgress(
            amendment_id=amendment_id,
            start_date=progress.start_date or datetime.now(),
            description=progress.description,
            notes=progress.notes,
            created_by=created_by or progress.created_by,
        )

        db.add(db_progress)
        db.commit()
        db.refresh(db_progress)

        return db_progress

    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to add progress entry: {str(e)}") from e


def get_amendment_progress(db: Session, amendment_id: int) -> List[AmendmentProgress]:
    """
    Get all progress entries for an amendment, ordered by date.

    Args:
        db: Database session
        amendment_id: Amendment ID

    Returns:
        List[AmendmentProgress]: List of progress entries
    """
    return (
        db.query(AmendmentProgress)
        .filter(AmendmentProgress.amendment_id == amendment_id)
        .order_by(desc(AmendmentProgress.start_date))
        .all()
    )


# ============================================================================
# Amendment Link Operations
# ============================================================================


def link_amendments(
    db: Session, amendment_id: int, link: AmendmentLinkCreate
) -> Optional[AmendmentLink]:
    """
    Create a link between two amendments.

    Args:
        db: Database session
        amendment_id: Source amendment ID
        link: Link data (target amendment ID and link type)

    Returns:
        AmendmentLink: Created link or None if either amendment not found

    Raises:
        ValueError: If link creation fails or amendment doesn't exist
    """
    try:
        # Verify both amendments exist
        source_amendment = get_amendment(db, amendment_id)
        target_amendment = get_amendment(db, link.linked_amendment_id)

        if not source_amendment or not target_amendment:
            return None

        # Check if link already exists
        existing_link = (
            db.query(AmendmentLink)
            .filter(
                AmendmentLink.amendment_id == amendment_id,
                AmendmentLink.linked_amendment_id == link.linked_amendment_id,
            )
            .first()
        )

        if existing_link:
            raise ValueError("Link already exists between these amendments")

        db_link = AmendmentLink(
            amendment_id=amendment_id,
            linked_amendment_id=link.linked_amendment_id,
            link_type=link.link_type,
        )

        db.add(db_link)
        db.commit()
        db.refresh(db_link)

        return db_link

    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create amendment link: {str(e)}") from e


def get_linked_amendments(db: Session, amendment_id: int) -> List[AmendmentLink]:
    """
    Get all amendments linked to the specified amendment.

    Args:
        db: Database session
        amendment_id: Amendment ID

    Returns:
        List[AmendmentLink]: List of amendment links
    """
    return (
        db.query(AmendmentLink).filter(AmendmentLink.amendment_id == amendment_id).all()
    )


def remove_amendment_link(db: Session, link_id: int) -> bool:
    """
    Remove a link between amendments.

    Args:
        db: Database session
        link_id: Link ID to remove

    Returns:
        bool: True if removed, False if not found
    """
    try:
        link = (
            db.query(AmendmentLink)
            .filter(AmendmentLink.amendment_link_id == link_id)
            .first()
        )
        if not link:
            return False

        db.delete(link)
        db.commit()
        return True

    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to remove amendment link: {str(e)}") from e


# ============================================================================
# Statistics and Dashboard Operations
# ============================================================================


def get_amendment_stats(db: Session) -> dict:
    """
    Get comprehensive statistics about amendments for dashboard.

    Returns:
        dict: Statistics including counts by status, priority, type, etc.
    """
    # Total amendments
    total_amendments = db.query(func.count(Amendment.amendment_id)).scalar()

    # Count by status
    by_status = {}
    for status in AmendmentStatus:
        count = (
            db.query(func.count(Amendment.amendment_id))
            .filter(Amendment.amendment_status == status)
            .scalar()
        )
        by_status[status.value] = count

    # Count by priority
    by_priority = {}
    for priority in Priority:
        count = (
            db.query(func.count(Amendment.amendment_id))
            .filter(Amendment.priority == priority)
            .scalar()
        )
        by_priority[priority.value] = count

    # Count by type
    by_type = {}
    for amd_type in AmendmentType:
        count = (
            db.query(func.count(Amendment.amendment_id))
            .filter(Amendment.amendment_type == amd_type)
            .scalar()
        )
        by_type[amd_type.value] = count

    # Count by development status
    by_development_status = {}
    for dev_status in DevelopmentStatus:
        count = (
            db.query(func.count(Amendment.amendment_id))
            .filter(Amendment.development_status == dev_status)
            .scalar()
        )
        by_development_status[dev_status.value] = count

    # QA pending (assigned but not completed)
    qa_pending = (
        db.query(func.count(Amendment.amendment_id))
        .filter(
            and_(
                Amendment.qa_assigned_id.isnot(None),
                Amendment.qa_completed.is_(False),
            )
        )
        .scalar()
    )

    # QA completed count
    qa_completed = (
        db.query(func.count(Amendment.amendment_id))
        .filter(Amendment.qa_completed.is_(True))
        .scalar()
    )

    # Database changes count
    database_changes = (
        db.query(func.count(Amendment.amendment_id))
        .filter(Amendment.database_changes.is_(True))
        .scalar()
    )

    # DB upgrade changes count
    db_upgrade_changes = (
        db.query(func.count(Amendment.amendment_id))
        .filter(Amendment.db_upgrade_changes.is_(True))
        .scalar()
    )

    return {
        "total_amendments": total_amendments,
        "by_status": by_status,
        "by_priority": by_priority,
        "by_type": by_type,
        "by_development_status": by_development_status,
        "qa_pending": qa_pending,
        "qa_completed": qa_completed,
        "database_changes": database_changes,
        "db_upgrade_changes": db_upgrade_changes,
    }


# ============================================================================
# Bulk Operations
# ============================================================================


def bulk_update_amendments(
    db: Session,
    amendment_ids: List[int],
    updates: AmendmentUpdate,
    modified_by: Optional[str] = None,
) -> Tuple[int, List[int], dict]:
    """
    Update multiple amendments at once.

    Args:
        db: Database session
        amendment_ids: List of amendment IDs to update
        updates: Update data to apply to all amendments
        modified_by: Username of the modifier

    Returns:
        Tuple[int, List[int], dict]: (updated_count, failed_ids, errors)
    """
    updated_count = 0
    failed_ids = []
    errors = {}

    for amendment_id in amendment_ids:
        try:
            result = update_amendment(db, amendment_id, updates, modified_by)
            if result:
                updated_count += 1
            else:
                failed_ids.append(amendment_id)
                errors[amendment_id] = "Amendment not found"
        except Exception as e:
            failed_ids.append(amendment_id)
            errors[amendment_id] = str(e)

    return updated_count, failed_ids, errors


# ============================================================================
# Employee CRUD Operations
# ============================================================================


def create_employee(db: Session, employee: EmployeeCreate) -> Employee:
    """
    Create a new employee record.

    Args:
        db: Database session
        employee: Employee creation data

    Returns:
        Employee: Created employee object

    Raises:
        ValueError: If employee creation fails
    """
    try:
        db_employee = Employee(
            employee_name=employee.employee_name,
            initials=employee.initials,
            email=employee.email,
            windows_login=employee.windows_login,
            is_active=employee.is_active,
        )

        db.add(db_employee)
        db.commit()
        db.refresh(db_employee)

        return db_employee

    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create employee: {str(e)}") from e


def get_employee(db: Session, employee_id: int) -> Optional[Employee]:
    """
    Get an employee by ID.

    Args:
        db: Database session
        employee_id: Employee ID

    Returns:
        Employee: Employee object or None if not found
    """
    return db.query(Employee).filter(Employee.employee_id == employee_id).first()


def get_employees(
    db: Session, skip: int = 0, limit: int = 100, active_only: bool = False
) -> Tuple[List[Employee], int]:
    """
    Get all employees with pagination.

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        active_only: If True, only return active employees

    Returns:
        Tuple[List[Employee], int]: List of employees and total count
    """
    query = db.query(Employee)

    if active_only:
        query = query.filter(Employee.is_active.is_(True))

    total = query.count()
    employees = query.order_by(Employee.employee_name).offset(skip).limit(limit).all()

    return employees, total


def update_employee(
    db: Session, employee_id: int, employee: EmployeeUpdate
) -> Optional[Employee]:
    """
    Update an employee's information.

    Args:
        db: Database session
        employee_id: Employee ID
        employee: Update data

    Returns:
        Employee: Updated employee or None if not found

    Raises:
        ValueError: If update fails
    """
    try:
        db_employee = get_employee(db, employee_id)
        if not db_employee:
            return None

        update_data = employee.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_employee, field, value)

        db.commit()
        db.refresh(db_employee)

        return db_employee

    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to update employee: {str(e)}") from e


def delete_employee(db: Session, employee_id: int) -> bool:
    """
    Delete an employee record.

    Args:
        db: Database session
        employee_id: Employee ID

    Returns:
        bool: True if deleted, False if not found

    Raises:
        ValueError: If deletion fails
    """
    try:
        db_employee = get_employee(db, employee_id)
        if not db_employee:
            return False

        db.delete(db_employee)
        db.commit()
        return True

    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to delete employee: {str(e)}") from e


# ============================================================================
# Application CRUD Operations
# ============================================================================


def create_application(db: Session, application: ApplicationCreate) -> Application:
    """
    Create a new application record.

    Args:
        db: Database session
        application: Application creation data

    Returns:
        Application: Created application object

    Raises:
        ValueError: If application creation fails
    """
    try:
        db_application = Application(
            application_name=application.application_name,
            description=application.description,
            is_active=application.is_active,
        )

        db.add(db_application)
        db.commit()
        db.refresh(db_application)

        return db_application

    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create application: {str(e)}") from e


def get_application(db: Session, application_id: int) -> Optional[Application]:
    """
    Get an application by ID with all versions loaded.

    Args:
        db: Database session
        application_id: Application ID

    Returns:
        Application: Application object or None if not found
    """
    return (
        db.query(Application)
        .options(joinedload(Application.versions))
        .filter(Application.application_id == application_id)
        .first()
    )


def get_applications(
    db: Session, skip: int = 0, limit: int = 100, active_only: bool = False
) -> Tuple[List[Application], int]:
    """
    Get all applications with pagination.

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        active_only: If True, only return active applications

    Returns:
        Tuple[List[Application], int]: List of applications and total count
    """
    query = db.query(Application)

    if active_only:
        query = query.filter(Application.is_active.is_(True))

    total = query.count()
    applications = (
        query.order_by(Application.application_name).offset(skip).limit(limit).all()
    )

    return applications, total


def update_application(
    db: Session, application_id: int, application: ApplicationUpdate
) -> Optional[Application]:
    """
    Update an application's information.

    Args:
        db: Database session
        application_id: Application ID
        application: Update data

    Returns:
        Application: Updated application or None if not found

    Raises:
        ValueError: If update fails
    """
    try:
        db_application = get_application(db, application_id)
        if not db_application:
            return None

        update_data = application.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_application, field, value)

        db.commit()
        db.refresh(db_application)

        return db_application

    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to update application: {str(e)}") from e


def delete_application(db: Session, application_id: int) -> bool:
    """
    Delete an application record.

    Args:
        db: Database session
        application_id: Application ID

    Returns:
        bool: True if deleted, False if not found

    Raises:
        ValueError: If deletion fails
    """
    try:
        db_application = get_application(db, application_id)
        if not db_application:
            return False

        db.delete(db_application)
        db.commit()
        return True

    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to delete application: {str(e)}") from e


# ============================================================================
# Application Version CRUD Operations
# ============================================================================


def create_application_version(
    db: Session, version: ApplicationVersionCreate
) -> ApplicationVersion:
    """
    Create a new application version record.

    Args:
        db: Database session
        version: Application version creation data

    Returns:
        ApplicationVersion: Created application version object

    Raises:
        ValueError: If version creation fails
    """
    try:
        db_version = ApplicationVersion(
            application_id=version.application_id,
            version=version.version,
            released_date=version.released_date,
            notes=version.notes,
            is_active=version.is_active,
        )

        db.add(db_version)
        db.commit()
        db.refresh(db_version)

        return db_version

    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create application version: {str(e)}") from e


def get_application_version(
    db: Session, version_id: int
) -> Optional[ApplicationVersion]:
    """
    Get an application version by ID.

    Args:
        db: Database session
        version_id: Application version ID

    Returns:
        ApplicationVersion: Application version object or None if not found
    """
    return (
        db.query(ApplicationVersion)
        .filter(ApplicationVersion.application_version_id == version_id)
        .first()
    )


def get_application_versions(
    db: Session, application_id: int, active_only: bool = False
) -> List[ApplicationVersion]:
    """
    Get all versions for a specific application.

    Args:
        db: Database session
        application_id: Application ID
        active_only: If True, only return active versions

    Returns:
        List[ApplicationVersion]: List of application versions
    """
    query = db.query(ApplicationVersion).filter(
        ApplicationVersion.application_id == application_id
    )

    if active_only:
        query = query.filter(ApplicationVersion.is_active.is_(True))

    return query.order_by(desc(ApplicationVersion.released_date)).all()


def update_application_version(
    db: Session, version_id: int, version: ApplicationVersionUpdate
) -> Optional[ApplicationVersion]:
    """
    Update an application version's information.

    Args:
        db: Database session
        version_id: Application version ID
        version: Update data

    Returns:
        ApplicationVersion: Updated application version or None if not found

    Raises:
        ValueError: If update fails
    """
    try:
        db_version = get_application_version(db, version_id)
        if not db_version:
            return None

        update_data = version.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_version, field, value)

        db.commit()
        db.refresh(db_version)

        return db_version

    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to update application version: {str(e)}") from e


def delete_application_version(db: Session, version_id: int) -> bool:
    """
    Delete an application version record.

    Args:
        db: Database session
        version_id: Application version ID

    Returns:
        bool: True if deleted, False if not found

    Raises:
        ValueError: If deletion fails
    """
    try:
        db_version = get_application_version(db, version_id)
        if not db_version:
            return False

        db.delete(db_version)
        db.commit()
        return True

    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to delete application version: {str(e)}") from e
