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
    AmendmentDocument,
    AmendmentApplication,
    AmendmentReferences,
    AmendmentStatus,
    DevelopmentStatus,
    Priority,
    AmendmentType,
    Employee,
    Application,
    ApplicationVersion,
    # QA System models
    QATestCase,
    QATestExecution,
    QADefect,
    QAHistory,
    QANotification,
    QAComment,
    # GitHub Issues features
    CommentMention,
    AmendmentWatcher,
    CommentReaction,
    ExecutionStatus,
    DefectStatus,
    DefectSeverity,
    NotificationType,
    QAStatus,
)
from .schemas import (
    AmendmentCreate,
    AmendmentUpdate,
    AmendmentQAUpdate,
    AmendmentProgressCreate,
    AmendmentLinkCreate,
    AmendmentDocumentCreate,
    AmendmentApplicationCreate,
    AmendmentFilter,
    EmployeeCreate,
    EmployeeUpdate,
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationVersionCreate,
    ApplicationVersionUpdate,
    # QA System schemas
    QATestCaseCreate,
    QATestCaseUpdate,
    QATestExecutionCreate,
    QATestExecutionUpdate,
    QATestExecutionExecuteRequest,
    QADefectCreate,
    QADefectUpdate,
    QANotificationCreate,
    QANotificationUpdate,
    QACommentCreate,
    QACommentUpdate,
)


# ============================================================================
# Amendment Reference Number Generation
# ============================================================================

# Type suffix mapping
TYPE_SUFFIX_MAP = {
    AmendmentType.FAULT: "F",
    AmendmentType.ENHANCEMENT: "E",
    AmendmentType.SUGGESTION: "S",
}


def get_or_create_references(db: Session) -> AmendmentReferences:
    """
    Get the amendment references record or create if it doesn't exist.

    Args:
        db: Database session

    Returns:
        AmendmentReferences: The references tracking object
    """
    refs = db.query(AmendmentReferences).first()
    if not refs:
        refs = AmendmentReferences(
            bug_reference=0,
            fault_reference=0,
            enhancement_reference=0,
            feature_reference=0,
            suggestion_reference=0,
            maintenance_reference=0,
            documentation_reference=0,
        )
        db.add(refs)
        db.commit()
        db.refresh(refs)
    return refs


def generate_amendment_reference(db: Session, amendment_type: AmendmentType) -> str:
    """
    Generate the next available amendment reference number based on type.

    Reference format: {Number}{TypeSuffix}
    Examples: 1B, 5F, 12E, 3FT

    Args:
        db: Database session
        amendment_type: Type of amendment

    Returns:
        str: Generated reference number
    """
    refs = get_or_create_references(db)

    # Get the suffix for this type
    suffix = TYPE_SUFFIX_MAP.get(amendment_type, "U")  # "U" for Unknown if not mapped

    # Increment the appropriate counter
    if amendment_type == AmendmentType.FAULT:
        refs.fault_reference += 1
        counter = refs.fault_reference
    elif amendment_type == AmendmentType.ENHANCEMENT:
        refs.enhancement_reference += 1
        counter = refs.enhancement_reference
    elif amendment_type == AmendmentType.SUGGESTION:
        refs.suggestion_reference += 1
        counter = refs.suggestion_reference
    else:
        # Fallback - use fault reference
        refs.fault_reference += 1
        counter = refs.fault_reference

    db.commit()
    db.refresh(refs)

    return f"{counter}{suffix}"


def get_next_reference(db: Session, amendment_type: AmendmentType) -> str:
    """
    Preview the next available reference number without incrementing counters.

    Args:
        db: Database session
        amendment_type: Type of amendment

    Returns:
        str: Next available reference number
    """
    refs = get_or_create_references(db)
    suffix = TYPE_SUFFIX_MAP.get(amendment_type, "U")

    # Get the current counter value (next will be +1)
    if amendment_type == AmendmentType.FAULT:
        counter = refs.fault_reference + 1
    elif amendment_type == AmendmentType.ENHANCEMENT:
        counter = refs.enhancement_reference + 1
    elif amendment_type == AmendmentType.SUGGESTION:
        counter = refs.suggestion_reference + 1
    else:
        counter = refs.fault_reference + 1

    return f"{counter}{suffix}"


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
        # Generate unique reference number based on type
        reference = generate_amendment_reference(db, amendment.amendment_type)

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
            joinedload(Amendment.documents),
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
            joinedload(Amendment.documents),
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

        # Filter by application (check both direct application field and amendment_applications table)
        if filters.application:
            query = query.join(Amendment.applications).filter(
                AmendmentApplication.application_name.in_(filters.application)
            )

        # Filter by version
        if filters.version:
            query = query.filter(Amendment.version.in_(filters.version))

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

        # Text search across reference, description, notes, and release notes
        if filters.search_text:
            search_pattern = f"%{filters.search_text}%"
            query = query.filter(
                or_(
                    Amendment.amendment_reference.like(search_pattern),
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
        if filters.qa_assigned_to_employee_id is not None:
            query = query.filter(Amendment.qa_assigned_id == filters.qa_assigned_to_employee_id)
        if filters.qa_overall_result:
            query = query.filter(Amendment.qa_overall_result.in_(filters.qa_overall_result))

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
    Optimized to use single query instead of 20-30+ separate queries.

    Returns:
        dict: Statistics including counts by status, priority, type, etc.
    """
    # Fetch all amendments once
    amendments = db.query(Amendment).all()

    # Initialize counters
    total_amendments = len(amendments)
    by_status = {status.value: 0 for status in AmendmentStatus}
    by_priority = {priority.value: 0 for priority in Priority}
    by_type = {amd_type.value: 0 for amd_type in AmendmentType}
    by_development_status = {dev_status.value: 0 for dev_status in DevelopmentStatus}
    qa_pending = 0
    qa_completed = 0
    database_changes = 0
    db_upgrade_changes = 0

    # Process all amendments in memory (fast)
    for amd in amendments:
        # Count by status - handle both enum objects and strings
        if amd.amendment_status:
            status_val = amd.amendment_status.value if hasattr(amd.amendment_status, 'value') else amd.amendment_status
            if status_val in by_status:
                by_status[status_val] += 1

        # Count by priority
        if amd.priority:
            priority_val = amd.priority.value if hasattr(amd.priority, 'value') else amd.priority
            if priority_val in by_priority:
                by_priority[priority_val] += 1

        # Count by type
        if amd.amendment_type:
            type_val = amd.amendment_type.value if hasattr(amd.amendment_type, 'value') else amd.amendment_type
            if type_val in by_type:
                by_type[type_val] += 1

        # Count by development status
        if amd.development_status:
            dev_val = amd.development_status.value if hasattr(amd.development_status, 'value') else amd.development_status
            if dev_val in by_development_status:
                by_development_status[dev_val] += 1

        # QA pending (assigned but not completed)
        if amd.qa_assigned_id is not None and not amd.qa_completed:
            qa_pending += 1

        # QA completed
        if amd.qa_completed:
            qa_completed += 1

        # Database changes
        if amd.database_changes:
            database_changes += 1

        # DB upgrade changes
        if amd.db_upgrade_changes:
            db_upgrade_changes += 1

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


def get_version_stats(db: Session) -> List[dict]:
    """
    Get amendment counts grouped by application and version.

    Filters to only show:
    - Centurion English (versions >= 7.4.2)
    - Centurion Scottish (all versions)
    - Centurion Web (all versions)

    Returns:
        List[dict]: List of version stats with format:
            {
                "application_name": str,
                "version": str,
                "amendment_count": int
            }
    """
    from .models import AmendmentApplication

    # Query to get counts grouped by application and version
    results = (
        db.query(
            AmendmentApplication.application_name,
            AmendmentApplication.reported_version,
            func.count(AmendmentApplication.amendment_id).label("count"),
        )
        .filter(AmendmentApplication.reported_version.isnot(None))
        .group_by(
            AmendmentApplication.application_name,
            AmendmentApplication.reported_version,
        )
        .order_by(
            AmendmentApplication.application_name,
            AmendmentApplication.reported_version,
        )
        .all()
    )

    def parse_version(version_str):
        """Parse version string into tuple of integers for comparison."""
        try:
            parts = version_str.split('.')
            return tuple(int(p) for p in parts if p.isdigit())
        except:
            return (0, 0, 0)

    def should_include_version(app_name, version):
        """Check if this app/version should be included in stats."""
        # Only include Centurion applications
        if not app_name.startswith("Centurion"):
            return False

        # For Centurion English, only include versions >= 7.4.2
        if app_name == "Centurion English":
            parsed = parse_version(version)
            min_version = (7, 4, 2)
            return parsed >= min_version

        # Include all versions of Centurion Scottish and Centurion Web
        if app_name in ["Centurion Scottish", "Centurion Web"]:
            return True

        return False

    # Convert to list of dictionaries and filter
    version_stats = []
    for app_name, version, count in results:
        if should_include_version(app_name, version):
            version_stats.append({
                "application_name": app_name,
                "version": version,
                "amendment_count": count,
            })

    return version_stats


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


def get_all_application_versions(
    db: Session,
    skip: int = 0,
    limit: int = 1000,
    active_only: bool = False,
) -> tuple[List[ApplicationVersion], int]:
    """
    Get all application versions across all applications with pagination.

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        active_only: If True, return only active versions

    Returns:
        Tuple of (versions list, total count)
    """
    query = db.query(ApplicationVersion)

    if active_only:
        query = query.filter(ApplicationVersion.is_active.is_(True))

    total = query.count()
    versions = (
        query.order_by(
            ApplicationVersion.application_id,
            desc(ApplicationVersion.released_date)
        )
        .offset(skip)
        .limit(limit)
        .all()
    )

    return versions, total


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


# ============================================================================
# Amendment Document CRUD Operations
# ============================================================================


def create_amendment_document(
    db: Session, amendment_id: int, document: AmendmentDocumentCreate
) -> AmendmentDocument:
    """
    Create a new document record for an amendment.

    Args:
        db: Database session
        amendment_id: Amendment ID
        document: Document creation data

    Returns:
        AmendmentDocument: Created document object

    Raises:
        ValueError: If document creation fails
    """
    try:
        db_document = AmendmentDocument(
            amendment_id=amendment_id,
            document_name=document.document_name,
            original_filename=document.original_filename,
            file_path=document.file_path,
            file_size=document.file_size,
            mime_type=document.mime_type,
            document_type=document.document_type,
            description=document.description,
            uploaded_by=document.uploaded_by,
        )

        db.add(db_document)
        db.commit()
        db.refresh(db_document)

        return db_document

    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create document: {str(e)}") from e


def get_amendment_document(
    db: Session, document_id: int
) -> Optional[AmendmentDocument]:
    """
    Get a document by ID.

    Args:
        db: Database session
        document_id: Document ID

    Returns:
        AmendmentDocument: Document object or None if not found
    """
    return (
        db.query(AmendmentDocument)
        .filter(AmendmentDocument.document_id == document_id)
        .first()
    )


def get_amendment_documents(
    db: Session, amendment_id: int
) -> List[AmendmentDocument]:
    """
    Get all documents for a specific amendment.

    Args:
        db: Database session
        amendment_id: Amendment ID

    Returns:
        List[AmendmentDocument]: List of documents
    """
    return (
        db.query(AmendmentDocument)
        .filter(AmendmentDocument.amendment_id == amendment_id)
        .order_by(desc(AmendmentDocument.uploaded_on))
        .all()
    )


def delete_amendment_document(db: Session, document_id: int) -> bool:
    """
    Delete a document record.

    Args:
        db: Database session
        document_id: Document ID

    Returns:
        bool: True if deleted, False if not found

    Raises:
        ValueError: If deletion fails
    """
    try:
        db_document = get_amendment_document(db, document_id)
        if not db_document:
            return False

        db.delete(db_document)
        db.commit()
        return True

    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to delete document: {str(e)}") from e


# ============================================================================
# Amendment Application CRUD Operations
# ============================================================================


def add_amendment_application(
    db: Session, amendment_id: int, app_data: AmendmentApplicationCreate
) -> Optional[AmendmentApplication]:
    """
    Add an application to an amendment.

    Args:
        db: Database session
        amendment_id: Amendment ID
        app_data: Application data

    Returns:
        AmendmentApplication: Created application link or None if amendment not found

    Raises:
        ValueError: If creation fails
    """
    try:
        # Verify amendment exists
        amendment = get_amendment(db, amendment_id)
        if not amendment:
            return None

        db_app = AmendmentApplication(
            amendment_id=amendment_id,
            application_id=app_data.application_id,
            application_name=app_data.application_name,
            reported_version=app_data.reported_version,
            applied_version=app_data.applied_version,
            development_status=app_data.development_status,
        )

        db.add(db_app)
        db.commit()
        db.refresh(db_app)

        return db_app

    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to add application to amendment: {str(e)}") from e


def get_amendment_applications(
    db: Session, amendment_id: int
) -> List[AmendmentApplication]:
    """
    Get all applications for a specific amendment.

    Args:
        db: Database session
        amendment_id: Amendment ID

    Returns:
        List[AmendmentApplication]: List of application links
    """
    return (
        db.query(AmendmentApplication)
        .filter(AmendmentApplication.amendment_id == amendment_id)
        .all()
    )


def update_amendment_application(
    db: Session, app_link_id: int, app_data: AmendmentApplicationCreate
) -> Optional[AmendmentApplication]:
    """
    Update an amendment application link.

    Args:
        db: Database session
        app_link_id: AmendmentApplication ID
        app_data: Updated application data

    Returns:
        AmendmentApplication: Updated application link or None if not found

    Raises:
        ValueError: If update fails
    """
    try:
        db_app = db.query(AmendmentApplication).filter(
            AmendmentApplication.id == app_link_id
        ).first()

        if not db_app:
            return None

        # Update fields
        db_app.application_id = app_data.application_id
        db_app.application_name = app_data.application_name
        db_app.reported_version = app_data.reported_version
        db_app.applied_version = app_data.applied_version
        db_app.development_status = app_data.development_status

        db.commit()
        db.refresh(db_app)

        return db_app

    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to update amendment application: {str(e)}") from e


def delete_amendment_application(db: Session, app_link_id: int) -> bool:
    """
    Remove an application from an amendment.

    Args:
        db: Database session
        app_link_id: AmendmentApplication ID

    Returns:
        bool: True if deleted, False if not found

    Raises:
        ValueError: If deletion fails
    """
    try:
        db_app = db.query(AmendmentApplication).filter(
            AmendmentApplication.id == app_link_id
        ).first()

        if not db_app:
            return False

        db.delete(db_app)
        db.commit()
        return True

    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to delete amendment application: {str(e)}") from e


# ============================================================================
# Reference Data CRUD Operations
# ============================================================================


def get_forces(db: Session, active_only: bool = False) -> List:
    """Get all force references."""
    from .models import ForceReference
    query = db.query(ForceReference).order_by(ForceReference.sort_order)
    if active_only:
        query = query.filter(ForceReference.is_active.is_(True))
    return query.all()


def create_force(db: Session, force_name: str, sort_order: int = 0) -> object:
    """Create a new force reference."""
    from .models import ForceReference
    try:
        db_force = ForceReference(
            force_name=force_name,
            is_active=True,
            sort_order=sort_order,
        )
        db.add(db_force)
        db.commit()
        db.refresh(db_force)
        return db_force
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create force: {str(e)}") from e


def update_force(db: Session, force_id: int, force_name: str = None, is_active: bool = None, sort_order: int = None) -> object:
    """Update a force reference."""
    from .models import ForceReference
    try:
        db_force = db.query(ForceReference).filter(ForceReference.force_id == force_id).first()
        if not db_force:
            return None
        
        if force_name is not None:
            db_force.force_name = force_name
        if is_active is not None:
            db_force.is_active = is_active
        if sort_order is not None:
            db_force.sort_order = sort_order
        
        db.commit()
        db.refresh(db_force)
        return db_force
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to update force: {str(e)}") from e


def delete_force(db: Session, force_id: int) -> bool:
    """Delete a force reference."""
    from .models import ForceReference
    try:
        db_force = db.query(ForceReference).filter(ForceReference.force_id == force_id).first()
        if not db_force:
            return False
        db.delete(db_force)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to delete force: {str(e)}") from e


def get_priorities(db: Session, active_only: bool = False) -> List:
    """Get all priority references."""
    from .models import PriorityReference
    query = db.query(PriorityReference).order_by(PriorityReference.sort_order)
    if active_only:
        query = query.filter(PriorityReference.is_active.is_(True))
    return query.all()


def create_priority(db: Session, priority_name: str, sort_order: int = 0) -> object:
    """Create a new priority reference."""
    from .models import PriorityReference
    try:
        db_priority = PriorityReference(
            priority_name=priority_name,
            is_active=True,
            sort_order=sort_order,
        )
        db.add(db_priority)
        db.commit()
        db.refresh(db_priority)
        return db_priority
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create priority: {str(e)}") from e


def update_priority(db: Session, priority_id: int, priority_name: str = None, is_active: bool = None, sort_order: int = None) -> object:
    """Update a priority reference."""
    from .models import PriorityReference
    try:
        db_priority = db.query(PriorityReference).filter(PriorityReference.priority_id == priority_id).first()
        if not db_priority:
            return None
        
        if priority_name is not None:
            db_priority.priority_name = priority_name
        if is_active is not None:
            db_priority.is_active = is_active
        if sort_order is not None:
            db_priority.sort_order = sort_order
        
        db.commit()
        db.refresh(db_priority)
        return db_priority
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to update priority: {str(e)}") from e


def delete_priority(db: Session, priority_id: int) -> bool:
    """Delete a priority reference."""
    from .models import PriorityReference
    try:
        db_priority = db.query(PriorityReference).filter(PriorityReference.priority_id == priority_id).first()
        if not db_priority:
            return False
        db.delete(db_priority)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to delete priority: {str(e)}") from e


def get_statuses(db: Session, status_type: str = None, active_only: bool = False) -> List:
    """Get all status references, optionally filtered by type."""
    from .models import StatusReference
    query = db.query(StatusReference).order_by(StatusReference.sort_order)
    if status_type:
        query = query.filter(StatusReference.status_type == status_type)
    if active_only:
        query = query.filter(StatusReference.is_active.is_(True))
    return query.all()


def create_status(db: Session, status_name: str, status_type: str, sort_order: int = 0) -> object:
    """Create a new status reference."""
    from .models import StatusReference
    try:
        db_status = StatusReference(
            status_name=status_name,
            status_type=status_type,
            is_active=True,
            sort_order=sort_order,
        )
        db.add(db_status)
        db.commit()
        db.refresh(db_status)
        return db_status
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create status: {str(e)}") from e


def update_status(db: Session, status_id: int, status_name: str = None, is_active: bool = None, sort_order: int = None) -> object:
    """Update a status reference."""
    from .models import StatusReference
    try:
        db_status = db.query(StatusReference).filter(StatusReference.status_id == status_id).first()
        if not db_status:
            return None
        
        if status_name is not None:
            db_status.status_name = status_name
        if is_active is not None:
            db_status.is_active = is_active
        if sort_order is not None:
            db_status.sort_order = sort_order
        
        db.commit()
        db.refresh(db_status)
        return db_status
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to update status: {str(e)}") from e


def delete_status(db: Session, status_id: int) -> bool:
    """Delete a status reference."""
    from .models import StatusReference
    try:
        db_status = db.query(StatusReference).filter(StatusReference.status_id == status_id).first()
        if not db_status:
            return False
        db.delete(db_status)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to delete status: {str(e)}") from e


def get_all_reference_data(db: Session) -> dict:
    """Get all reference data from database."""
    forces = get_forces(db, active_only=True)
    priorities = get_priorities(db, active_only=True)
    amendment_statuses = get_statuses(db, status_type="amendment", active_only=True)
    development_statuses = get_statuses(db, status_type="development", active_only=True)

    from .models import AmendmentType, LinkType, DocumentType

    return {
        "forces": [f.force_name for f in forces],
        "priorities": [p.priority_name for p in priorities],
        "amendment_statuses": [s.status_name for s in amendment_statuses],
        "development_statuses": [s.status_name for s in development_statuses],
        "amendment_types": [type_.value for type_ in AmendmentType],
        "link_types": [link_type.value for link_type in LinkType],
        "document_types": [doc_type.value for doc_type in DocumentType],
    }


# ============================================================================
# Authentication Helper Functions
# ============================================================================


def get_employee_by_windows_login(db: Session, windows_login: str) -> Optional[Employee]:
    """
    Get employee by Windows login username.

    Args:
        db: Database session
        windows_login: Windows login username

    Returns:
        Employee object if found, None otherwise
    """
    return db.query(Employee).filter(Employee.windows_login == windows_login).first()


def get_employee_by_email(db: Session, email: str) -> Optional[Employee]:
    """
    Get employee by email address.

    Args:
        db: Database session
        email: Email address

    Returns:
        Employee object if found, None otherwise
    """
    return db.query(Employee).filter(Employee.email == email).first()


def authenticate_employee(db: Session, username: str, password: str) -> Optional[Employee]:
    """
    Authenticate an employee using username (windows_login or email) and password.

    Tries to find employee by windows_login first, then by email.
    Verifies password hash if employee is found.

    Args:
        db: Database session
        username: Windows login or email
        password: Plain text password

    Returns:
        Employee object if authentication successful, None otherwise
    """
    from .auth import verify_password

    # Try windows_login first
    employee = get_employee_by_windows_login(db, username)

    # If not found, try email
    if not employee:
        employee = get_employee_by_email(db, username)

    # Check if employee exists and is active
    if not employee or not employee.is_active:
        return None

    # Verify password
    if not employee.password_hash:
        return None  # No password set (AD-only user?)

    if not verify_password(password, employee.password_hash):
        return None

    return employee


def update_last_login(db: Session, employee_id: int) -> None:
    """
    Update the last_login timestamp for an employee.

    Args:
        db: Database session
        employee_id: Employee ID
    """
    employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()

    if employee:
        employee.last_login = datetime.now()
        db.commit()


# ============================================================================
# QA Test Case CRUD Operations
# ============================================================================


def generate_test_case_number(db: Session) -> str:
    """
    Generate the next test case number (TC-001, TC-002, etc.).

    Args:
        db: Database session

    Returns:
        str: Generated test case number
    """
    # Get the highest existing test case number
    last_test_case = (
        db.query(QATestCase)
        .order_by(desc(QATestCase.test_case_id))
        .first()
    )

    if not last_test_case:
        return "TC-001"

    # Extract number from last test case
    try:
        last_number = int(last_test_case.test_case_number.split("-")[1])
        new_number = last_number + 1
    except (IndexError, ValueError):
        new_number = 1

    return f"TC-{new_number:03d}"


def create_test_case(
    db: Session, test_case: QATestCaseCreate, created_by: Optional[str] = None
) -> QATestCase:
    """
    Create a new test case.

    Args:
        db: Database session
        test_case: Test case creation data
        created_by: Username of the creator

    Returns:
        QATestCase: Created test case

    Raises:
        ValueError: If validation fails
    """
    # Generate test case number
    test_case_number = generate_test_case_number(db)

    # Create test case model
    db_test_case = QATestCase(
        test_case_number=test_case_number,
        title=test_case.title,
        description=test_case.description,
        test_type=test_case.test_type,
        priority=test_case.priority,
        preconditions=test_case.preconditions,
        test_steps=test_case.test_steps,
        expected_results=test_case.expected_results,
        application_id=test_case.application_id,
        component=test_case.component,
        tags=test_case.tags,
        is_active=test_case.is_active,
        is_automated=test_case.is_automated,
        automation_script=test_case.automation_script,
        created_by=created_by or test_case.created_by,
    )

    db.add(db_test_case)
    db.commit()
    db.refresh(db_test_case)

    return db_test_case


def get_test_case(db: Session, test_case_id: int) -> Optional[QATestCase]:
    """
    Get a test case by ID.

    Args:
        db: Database session
        test_case_id: Test case ID

    Returns:
        QATestCase or None
    """
    return (
        db.query(QATestCase)
        .filter(QATestCase.test_case_id == test_case_id)
        .first()
    )


def get_test_cases(
    db: Session,
    test_type: Optional[str] = None,
    priority: Optional[str] = None,
    application_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> Tuple[List[QATestCase], int]:
    """
    Get test cases with filtering and pagination.

    Args:
        db: Database session
        test_type: Filter by test type
        priority: Filter by priority
        application_id: Filter by application
        is_active: Filter by active status
        search: Search in title and description
        skip: Number of records to skip
        limit: Maximum number of records

    Returns:
        Tuple of (test cases list, total count)
    """
    query = db.query(QATestCase)

    # Apply filters
    if test_type:
        query = query.filter(QATestCase.test_type == test_type)
    if priority:
        query = query.filter(QATestCase.priority == priority)
    if application_id:
        query = query.filter(QATestCase.application_id == application_id)
    if is_active is not None:
        query = query.filter(QATestCase.is_active == is_active)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                QATestCase.title.ilike(search_pattern),
                QATestCase.description.ilike(search_pattern),
                QATestCase.test_case_number.ilike(search_pattern),
            )
        )

    # Get total count
    total = query.count()

    # Apply pagination and ordering
    test_cases = (
        query.order_by(desc(QATestCase.created_on))
        .offset(skip)
        .limit(limit)
        .all()
    )

    return test_cases, total


def update_test_case(
    db: Session,
    test_case_id: int,
    test_case_update: QATestCaseUpdate,
    modified_by: Optional[str] = None,
) -> Optional[QATestCase]:
    """
    Update an existing test case.

    Args:
        db: Database session
        test_case_id: Test case ID
        test_case_update: Update data
        modified_by: Username of the modifier

    Returns:
        Updated QATestCase or None
    """
    db_test_case = get_test_case(db, test_case_id)
    if not db_test_case:
        return None

    # Update fields that are provided
    update_data = test_case_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field != "modified_by":
            setattr(db_test_case, field, value)

    db_test_case.modified_by = modified_by or test_case_update.modified_by

    db.commit()
    db.refresh(db_test_case)

    return db_test_case


def delete_test_case(db: Session, test_case_id: int) -> bool:
    """
    Delete a test case.

    Args:
        db: Database session
        test_case_id: Test case ID

    Returns:
        True if deleted, False if not found
    """
    db_test_case = get_test_case(db, test_case_id)
    if not db_test_case:
        return False

    db.delete(db_test_case)
    db.commit()

    return True


# ============================================================================
# QA Test Execution CRUD Operations
# ============================================================================


def create_test_execution(
    db: Session,
    test_execution: QATestExecutionCreate,
    created_by: Optional[str] = None,
) -> QATestExecution:
    """
    Create a new test execution (link test to amendment).

    Args:
        db: Database session
        test_execution: Test execution creation data
        created_by: Username of the creator

    Returns:
        QATestExecution: Created test execution
    """
    db_execution = QATestExecution(
        amendment_id=test_execution.amendment_id,
        test_case_id=test_execution.test_case_id,
        executed_by_id=test_execution.executed_by_id,
        execution_status=test_execution.execution_status,
        executed_on=test_execution.executed_on,
        duration_minutes=test_execution.duration_minutes,
        actual_results=test_execution.actual_results,
        notes=test_execution.notes,
        attachments=test_execution.attachments,
        test_environment=test_execution.test_environment,
        build_version=test_execution.build_version,
        created_by=created_by or test_execution.created_by,
    )

    db.add(db_execution)
    db.commit()
    db.refresh(db_execution)

    return db_execution


def get_test_executions(
    db: Session, amendment_id: int
) -> List[QATestExecution]:
    """
    Get all test executions for an amendment.

    Args:
        db: Database session
        amendment_id: Amendment ID

    Returns:
        List of QATestExecution
    """
    return (
        db.query(QATestExecution)
        .filter(QATestExecution.amendment_id == amendment_id)
        .options(joinedload(QATestExecution.test_case))
        .options(joinedload(QATestExecution.executed_by))
        .order_by(desc(QATestExecution.created_on))
        .all()
    )


def update_test_execution(
    db: Session,
    execution_id: int,
    execution_update: QATestExecutionUpdate,
    modified_by: Optional[str] = None,
) -> Optional[QATestExecution]:
    """
    Update an existing test execution.

    Args:
        db: Database session
        execution_id: Test execution ID
        execution_update: Update data
        modified_by: Username of the modifier

    Returns:
        Updated QATestExecution or None
    """
    db_execution = (
        db.query(QATestExecution)
        .filter(QATestExecution.execution_id == execution_id)
        .first()
    )

    if not db_execution:
        return None

    # Update fields that are provided
    update_data = execution_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field != "modified_by":
            setattr(db_execution, field, value)

    db_execution.modified_by = modified_by or execution_update.modified_by

    db.commit()
    db.refresh(db_execution)

    return db_execution


def execute_test(
    db: Session,
    execution_id: int,
    execute_request: QATestExecutionExecuteRequest,
    modified_by: Optional[str] = None,
) -> Optional[QATestExecution]:
    """
    Execute a test and record results.

    Args:
        db: Database session
        execution_id: Test execution ID
        execute_request: Execution result data
        modified_by: Username

    Returns:
        Updated QATestExecution or None
    """
    db_execution = (
        db.query(QATestExecution)
        .filter(QATestExecution.execution_id == execution_id)
        .first()
    )

    if not db_execution:
        return None

    # Update execution with results
    db_execution.execution_status = execute_request.execution_status.value
    db_execution.executed_on = execute_request.executed_on
    db_execution.duration_minutes = execute_request.duration_minutes
    db_execution.actual_results = execute_request.actual_results
    db_execution.notes = execute_request.notes
    db_execution.attachments = execute_request.attachments
    db_execution.test_environment = execute_request.test_environment
    db_execution.build_version = execute_request.build_version
    db_execution.executed_by_id = execute_request.executed_by_id
    db_execution.modified_by = modified_by

    db.commit()
    db.refresh(db_execution)

    # Create QA history entry
    create_qa_history(
        db=db,
        amendment_id=db_execution.amendment_id,
        action="Test Executed",
        comment=f"Test case {db_execution.test_case.test_case_number} - Status: {execute_request.execution_status.value}",
        changed_by_id=execute_request.executed_by_id,
    )

    return db_execution


# ============================================================================
# QA Defect CRUD Operations
# ============================================================================


def generate_defect_number(db: Session) -> str:
    """
    Generate the next defect number (DEF-001, DEF-002, etc.).

    Args:
        db: Database session

    Returns:
        str: Generated defect number
    """
    # Get the highest existing defect number
    last_defect = (
        db.query(QADefect)
        .order_by(desc(QADefect.defect_id))
        .first()
    )

    if not last_defect:
        return "DEF-001"

    # Extract number from last defect
    try:
        last_number = int(last_defect.defect_number.split("-")[1])
        new_number = last_number + 1
    except (IndexError, ValueError):
        new_number = 1

    return f"DEF-{new_number:03d}"


def create_defect(
    db: Session, defect: QADefectCreate, created_by: Optional[str] = None
) -> QADefect:
    """
    Create a new defect.

    Args:
        db: Database session
        defect: Defect creation data
        created_by: Username of the creator

    Returns:
        QADefect: Created defect
    """
    # Generate defect number
    defect_number = generate_defect_number(db)

    # Create defect model
    db_defect = QADefect(
        defect_number=defect_number,
        amendment_id=defect.amendment_id,
        test_execution_id=defect.test_execution_id,
        title=defect.title,
        description=defect.description,
        severity=defect.severity,
        status=defect.status,
        steps_to_reproduce=defect.steps_to_reproduce,
        actual_behavior=defect.actual_behavior,
        expected_behavior=defect.expected_behavior,
        reported_by_id=defect.reported_by_id,
        assigned_to_id=defect.assigned_to_id,
        resolution=defect.resolution,
        root_cause=defect.root_cause,
        fixed_in_version=defect.fixed_in_version,
        created_by=created_by or defect.created_by,
    )

    if defect.assigned_to_id:
        db_defect.assigned_date = datetime.now()

    db.add(db_defect)
    db.commit()
    db.refresh(db_defect)

    # Create QA history entry
    create_qa_history(
        db=db,
        amendment_id=defect.amendment_id,
        action="Defect Created",
        comment=f"Defect {defect_number}: {defect.title} (Severity: {defect.severity})",
        changed_by_id=defect.reported_by_id,
    )

    return db_defect


def get_defect(db: Session, defect_id: int) -> Optional[QADefect]:
    """
    Get a defect by ID.

    Args:
        db: Database session
        defect_id: Defect ID

    Returns:
        QADefect or None
    """
    return (
        db.query(QADefect)
        .options(joinedload(QADefect.reported_by))
        .options(joinedload(QADefect.assigned_to))
        .filter(QADefect.defect_id == defect_id)
        .first()
    )


def get_defects(
    db: Session,
    amendment_id: Optional[int] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    assigned_to_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
) -> Tuple[List[QADefect], int]:
    """
    Get defects with filtering and pagination.

    Args:
        db: Database session
        amendment_id: Filter by amendment
        status: Filter by status
        severity: Filter by severity
        assigned_to_id: Filter by assigned developer
        skip: Number of records to skip
        limit: Maximum number of records

    Returns:
        Tuple of (defects list, total count)
    """
    query = db.query(QADefect)

    # Apply filters
    if amendment_id:
        query = query.filter(QADefect.amendment_id == amendment_id)
    if status:
        query = query.filter(QADefect.status == status)
    if severity:
        query = query.filter(QADefect.severity == severity)
    if assigned_to_id:
        query = query.filter(QADefect.assigned_to_id == assigned_to_id)

    # Get total count
    total = query.count()

    # Apply pagination and ordering
    defects = (
        query.options(joinedload(QADefect.reported_by))
        .options(joinedload(QADefect.assigned_to))
        .order_by(desc(QADefect.reported_date))
        .offset(skip)
        .limit(limit)
        .all()
    )

    return defects, total


def update_defect(
    db: Session,
    defect_id: int,
    defect_update: QADefectUpdate,
    modified_by: Optional[str] = None,
) -> Optional[QADefect]:
    """
    Update an existing defect.

    Args:
        db: Database session
        defect_id: Defect ID
        defect_update: Update data
        modified_by: Username of the modifier

    Returns:
        Updated QADefect or None
    """
    db_defect = get_defect(db, defect_id)
    if not db_defect:
        return None

    old_status = db_defect.status

    # Update fields that are provided
    update_data = defect_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field != "modified_by":
            # Track status transitions
            if field == "status" and value != old_status:
                if value == "Resolved":
                    db_defect.resolved_date = datetime.now()
                elif value == "Closed":
                    db_defect.closed_date = datetime.now()
            setattr(db_defect, field, value)

    db_defect.modified_by = modified_by or defect_update.modified_by

    db.commit()
    db.refresh(db_defect)

    # Create QA history entry for status change
    if defect_update.status and defect_update.status != old_status:
        create_qa_history(
            db=db,
            amendment_id=db_defect.amendment_id,
            action="Defect Status Changed",
            field_name="status",
            old_value=old_status,
            new_value=defect_update.status,
            comment=f"Defect {db_defect.defect_number}: {old_status} → {defect_update.status}",
        )

    return db_defect


def delete_defect(db: Session, defect_id: int) -> bool:
    """
    Delete a defect.

    Args:
        db: Database session
        defect_id: Defect ID

    Returns:
        True if deleted, False if not found
    """
    db_defect = get_defect(db, defect_id)
    if not db_defect:
        return False

    db.delete(db_defect)
    db.commit()

    return True


# ============================================================================
# QA History CRUD Operations
# ============================================================================


def create_qa_history(
    db: Session,
    amendment_id: int,
    action: str,
    field_name: Optional[str] = None,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    comment: Optional[str] = None,
    changed_by_id: Optional[int] = None,
) -> QAHistory:
    """
    Create a QA history entry (audit trail).

    Args:
        db: Database session
        amendment_id: Amendment ID
        action: Action performed
        field_name: Field that changed
        old_value: Old value
        new_value: New value
        comment: Additional comment
        changed_by_id: Employee who made the change

    Returns:
        QAHistory: Created history entry
    """
    db_history = QAHistory(
        amendment_id=amendment_id,
        action=action,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        comment=comment,
        changed_by_id=changed_by_id,
    )

    db.add(db_history)
    db.commit()
    db.refresh(db_history)

    return db_history


def get_qa_history(
    db: Session, amendment_id: int, limit: int = 100
) -> List[QAHistory]:
    """
    Get QA history for an amendment.

    Args:
        db: Database session
        amendment_id: Amendment ID
        limit: Maximum number of records

    Returns:
        List of QAHistory entries
    """
    return (
        db.query(QAHistory)
        .filter(QAHistory.amendment_id == amendment_id)
        .options(joinedload(QAHistory.changed_by))
        .order_by(desc(QAHistory.changed_on))
        .limit(limit)
        .all()
    )


def track_qa_change(
    db: Session,
    amendment_id: int,
    field_name: str,
    old_value: str,
    new_value: str,
    changed_by_id: Optional[int] = None,
) -> QAHistory:
    """
    Automatically track a QA field change.

    Args:
        db: Database session
        amendment_id: Amendment ID
        field_name: Field that changed
        old_value: Old value
        new_value: New value
        changed_by_id: Employee who made the change

    Returns:
        QAHistory: Created history entry
    """
    return create_qa_history(
        db=db,
        amendment_id=amendment_id,
        action="Field Updated",
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        changed_by_id=changed_by_id,
    )


# ============================================================================
# QA Notification CRUD Operations
# ============================================================================


def create_notification(
    db: Session, notification: QANotificationCreate
) -> QANotification:
    """
    Create a new notification.

    Args:
        db: Database session
        notification: Notification creation data

    Returns:
        QANotification: Created notification
    """
    db_notification = QANotification(
        employee_id=notification.employee_id,
        notification_type=notification.notification_type,
        title=notification.title,
        message=notification.message,
        amendment_id=notification.amendment_id,
        defect_id=notification.defect_id,
        is_email_sent=notification.is_email_sent,
    )

    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)

    return db_notification


def get_notifications(
    db: Session,
    employee_id: int,
    is_read: Optional[bool] = None,
    skip: int = 0,
    limit: int = 50,
) -> Tuple[List[QANotification], int, int]:
    """
    Get notifications for an employee.

    Args:
        db: Database session
        employee_id: Employee ID
        is_read: Filter by read status
        skip: Number of records to skip
        limit: Maximum number of records

    Returns:
        Tuple of (notifications list, total count, unread count)
    """
    query = db.query(QANotification).filter(
        QANotification.employee_id == employee_id
    )

    # Apply is_read filter
    if is_read is not None:
        query = query.filter(QANotification.is_read == is_read)

    # Get total count
    total = query.count()

    # Get unread count
    unread_count = (
        db.query(QANotification)
        .filter(
            and_(
                QANotification.employee_id == employee_id,
                QANotification.is_read == False,
            )
        )
        .count()
    )

    # Apply pagination and ordering
    notifications = (
        query.order_by(desc(QANotification.created_on))
        .offset(skip)
        .limit(limit)
        .all()
    )

    return notifications, total, unread_count


def get_unread_count(db: Session, employee_id: int) -> int:
    """
    Get count of unread notifications for an employee.

    Args:
        db: Database session
        employee_id: Employee ID

    Returns:
        int: Count of unread notifications
    """
    return (
        db.query(QANotification)
        .filter(
            and_(
                QANotification.employee_id == employee_id,
                QANotification.is_read == False,
            )
        )
        .count()
    )


def mark_notification_read(
    db: Session, notification_id: int
) -> Optional[QANotification]:
    """
    Mark a notification as read.

    Args:
        db: Database session
        notification_id: Notification ID

    Returns:
        Updated QANotification or None
    """
    db_notification = (
        db.query(QANotification)
        .filter(QANotification.notification_id == notification_id)
        .first()
    )

    if not db_notification:
        return None

    db_notification.is_read = True
    db_notification.read_on = datetime.now()

    db.commit()
    db.refresh(db_notification)

    return db_notification


def mark_all_notifications_read(db: Session, employee_id: int) -> int:
    """
    Mark all notifications as read for an employee.

    Args:
        db: Database session
        employee_id: Employee ID

    Returns:
        int: Number of notifications marked as read
    """
    updated_count = (
        db.query(QANotification)
        .filter(
            and_(
                QANotification.employee_id == employee_id,
                QANotification.is_read == False,
            )
        )
        .update({"is_read": True, "read_on": datetime.now()})
    )

    db.commit()

    return updated_count


def delete_notification(db: Session, notification_id: int) -> bool:
    """
    Delete a notification.

    Args:
        db: Database session
        notification_id: Notification ID

    Returns:
        True if deleted, False if not found
    """
    db_notification = (
        db.query(QANotification)
        .filter(QANotification.notification_id == notification_id)
        .first()
    )

    if not db_notification:
        return False

    db.delete(db_notification)
    db.commit()

    return True


# ============================================================================
# QA Comment Functions
# ============================================================================


def create_qa_comment(
    db: Session, comment: QACommentCreate
) -> QAComment:
    """
    Create a QA comment.

    Args:
        db: Database session
        comment: Comment data

    Returns:
        Created QAComment object
    """
    db_comment = QAComment(
        amendment_id=comment.amendment_id,
        employee_id=comment.employee_id,
        comment_text=comment.comment_text,
        comment_type=comment.comment_type,
    )

    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)

    return db_comment


def get_qa_comments_for_amendment(
    db: Session, amendment_id: int, skip: int = 0, limit: int = 100
) -> List[QAComment]:
    """
    Get all QA comments for an amendment.

    Args:
        db: Database session
        amendment_id: Amendment ID
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of QAComment objects
    """
    return (
        db.query(QAComment)
        .filter(QAComment.amendment_id == amendment_id)
        .order_by(QAComment.created_on.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_qa_comment(db: Session, comment_id: int) -> Optional[QAComment]:
    """
    Get a single QA comment by ID.

    Args:
        db: Database session
        comment_id: Comment ID

    Returns:
        QAComment object or None
    """
    return (
        db.query(QAComment)
        .filter(QAComment.comment_id == comment_id)
        .first()
    )


def update_qa_comment(
    db: Session, comment_id: int, comment_update: QACommentUpdate
) -> Optional[QAComment]:
    """
    Update a QA comment.

    Args:
        db: Database session
        comment_id: Comment ID
        comment_update: Comment update data

    Returns:
        Updated QAComment object or None if not found
    """
    db_comment = get_qa_comment(db, comment_id)

    if not db_comment:
        return None

    # Update fields
    update_data = comment_update.dict(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_comment, field, value)

    # Mark as edited
    db_comment.is_edited = True
    db_comment.modified_on = datetime.now()

    db.commit()
    db.refresh(db_comment)

    return db_comment


def delete_qa_comment(db: Session, comment_id: int) -> bool:
    """
    Delete a QA comment.

    Args:
        db: Database session
        comment_id: Comment ID

    Returns:
        True if deleted, False if not found
    """
    db_comment = get_qa_comment(db, comment_id)

    if not db_comment:
        return False

    db.delete(db_comment)
    db.commit()

    return True


def count_qa_comments_for_amendment(db: Session, amendment_id: int) -> int:
    """
    Count QA comments for an amendment.

    Args:
        db: Database session
        amendment_id: Amendment ID

    Returns:
        Number of comments
    """
    return (
        db.query(QAComment)
        .filter(QAComment.amendment_id == amendment_id)
        .count()
    )


# ============================================================================
# QA Dashboard & Reporting Functions
# ============================================================================


def calculate_qa_progress(db: Session, amendment_id: int) -> dict:
    """
    Calculate QA progress for an amendment.

    Args:
        db: Database session
        amendment_id: Amendment ID

    Returns:
        dict: Progress information including test execution stats and checklist completion
    """
    # Get amendment
    amendment = get_amendment(db, amendment_id)
    if not amendment:
        return {
            "total_tests": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "tests_blocked": 0,
            "tests_not_run": 0,
            "progress_percentage": 0,
            "checklist_items_completed": 0,
            "checklist_items_total": 2,
            "overall_status": "Not Started",
        }

    # Count test executions by status
    test_stats = (
        db.query(
            QATestExecution.execution_status,
            func.count(QATestExecution.execution_id).label("count"),
        )
        .filter(QATestExecution.amendment_id == amendment_id)
        .group_by(QATestExecution.execution_status)
        .all()
    )

    # Initialize counters
    total_tests = 0
    tests_passed = 0
    tests_failed = 0
    tests_blocked = 0
    tests_not_run = 0

    for status, count in test_stats:
        total_tests += count
        if status == "Passed":
            tests_passed += count
        elif status == "Failed":
            tests_failed += count
        elif status == "Blocked":
            tests_blocked += count
        elif status == "Not Run":
            tests_not_run += count

    # Calculate progress percentage (based on passed tests)
    progress_percentage = 0
    if total_tests > 0:
        progress_percentage = int((tests_passed / total_tests) * 100)

    # Count checklist items completed
    checklist_items_completed = 0
    checklist_items_total = 2

    if amendment.qa_test_plan_check:
        checklist_items_completed += 1
    if amendment.qa_test_release_notes_check:
        checklist_items_completed += 1

    # Determine overall status
    overall_status = "In Progress"
    if amendment.qa_status == "Passed":
        overall_status = "Completed"
    elif amendment.qa_status == "Failed":
        overall_status = "Failed"
    elif amendment.qa_status == "Blocked":
        overall_status = "Blocked"
    elif amendment.qa_status == "Not Started":
        overall_status = "Not Started"

    return {
        "total_tests": total_tests,
        "tests_passed": tests_passed,
        "tests_failed": tests_failed,
        "tests_blocked": tests_blocked,
        "tests_not_run": tests_not_run,
        "progress_percentage": progress_percentage,
        "checklist_items_completed": checklist_items_completed,
        "checklist_items_total": checklist_items_total,
        "overall_status": overall_status,
    }


def get_qa_dashboard(db: Session, employee_id: int) -> dict:
    """
    Get QA dashboard data for an employee.

    Args:
        db: Database session
        employee_id: Employee ID

    Returns:
        dict: Dashboard data with task summaries
    """
    from datetime import timedelta

    # Get all amendments assigned to this QA tester
    assigned_amendments = (
        db.query(Amendment)
        .filter(Amendment.qa_assigned_id == employee_id)
        .all()
    )

    # Separate by status
    assigned_to_me = []
    in_testing = []
    overdue = []

    for amendment in assigned_amendments:
        task_summary = {
            "amendment_id": amendment.amendment_id,
            "amendment_reference": amendment.amendment_reference,
            "description": amendment.description,
            "qa_status": amendment.qa_status,
            "priority": amendment.priority,
            "qa_assigned_date": amendment.qa_assigned_date,
            "qa_due_date": amendment.qa_due_date,
            "is_overdue": False,
        }

        # Check if overdue
        if amendment.qa_due_date and datetime.now() > amendment.qa_due_date:
            task_summary["is_overdue"] = True
            overdue.append(task_summary)

        if amendment.qa_status == "In Testing":
            in_testing.append(task_summary)
        elif amendment.qa_status in ["Assigned", "Not Started"]:
            assigned_to_me.append(task_summary)

    # Get completed this week
    week_ago = datetime.now() - timedelta(days=7)
    completed_this_week = (
        db.query(Amendment)
        .filter(
            and_(
                Amendment.qa_assigned_id == employee_id,
                Amendment.qa_status == "Passed",
                Amendment.qa_completed_date >= week_ago,
            )
        )
        .count()
    )

    return {
        "assigned_to_me": assigned_to_me,
        "in_testing": in_testing,
        "overdue": overdue,
        "completed_this_week": completed_this_week,
        "total_assigned": len(assigned_to_me),
        "total_in_testing": len(in_testing),
        "total_overdue": len(overdue),
    }


def get_qa_metrics(db: Session, days: int = 30) -> dict:
    """
    Get QA metrics and analytics.

    Args:
        db: Database session
        days: Number of days to analyze

    Returns:
        dict: QA metrics data
    """
    from datetime import timedelta

    cutoff_date = datetime.now() - timedelta(days=days)

    # Get test execution stats
    test_executions = (
        db.query(QATestExecution)
        .filter(QATestExecution.executed_on >= cutoff_date)
        .all()
    )

    total_tests = len(test_executions)
    tests_passed = sum(1 for t in test_executions if t.execution_status == "Passed")
    tests_failed = sum(1 for t in test_executions if t.execution_status == "Failed")
    tests_blocked = sum(1 for t in test_executions if t.execution_status == "Blocked")

    pass_rate = (tests_passed / total_tests * 100) if total_tests > 0 else 0

    # Get defect stats
    defects = db.query(QADefect).filter(QADefect.reported_date >= cutoff_date).all()

    defects_by_severity = {
        "Critical": sum(1 for d in defects if d.severity == "Critical"),
        "High": sum(1 for d in defects if d.severity == "High"),
        "Medium": sum(1 for d in defects if d.severity == "Medium"),
        "Low": sum(1 for d in defects if d.severity == "Low"),
    }

    defects_by_status = {
        "New": sum(1 for d in defects if d.status == "New"),
        "Assigned": sum(1 for d in defects if d.status == "Assigned"),
        "In Progress": sum(1 for d in defects if d.status == "In Progress"),
        "Resolved": sum(1 for d in defects if d.status == "Resolved"),
        "Closed": sum(1 for d in defects if d.status == "Closed"),
    }

    open_defects = sum(1 for d in defects if d.status in ["New", "Assigned", "In Progress"])
    critical_defects = defects_by_severity["Critical"]

    # Calculate average time to test
    completed_qa = (
        db.query(Amendment)
        .filter(
            and_(
                Amendment.qa_completed_date >= cutoff_date,
                Amendment.qa_assigned_date.isnot(None),
            )
        )
        .all()
    )

    avg_time_to_test = 0
    if completed_qa:
        total_hours = sum(
            (a.qa_completed_date - a.qa_assigned_date).total_seconds() / 3600
            for a in completed_qa
        )
        avg_time_to_test = total_hours / len(completed_qa)

    # Calculate average test duration
    avg_test_duration = 0
    if test_executions:
        durations = [t.duration_minutes for t in test_executions if t.duration_minutes]
        if durations:
            avg_test_duration = sum(durations) / len(durations)

    # Calculate SLA compliance
    total_qa_tasks = (
        db.query(Amendment)
        .filter(Amendment.qa_completed_date >= cutoff_date)
        .count()
    )

    on_time_completions = (
        db.query(Amendment)
        .filter(
            and_(
                Amendment.qa_completed_date >= cutoff_date,
                Amendment.qa_due_date.isnot(None),
                Amendment.qa_completed_date <= Amendment.qa_due_date,
            )
        )
        .count()
    )

    sla_compliance = (
        (on_time_completions / total_qa_tasks * 100) if total_qa_tasks > 0 else 100
    )

    return {
        "total_tests_executed": total_tests,
        "tests_passed": tests_passed,
        "tests_failed": tests_failed,
        "tests_blocked": tests_blocked,
        "pass_rate_percentage": round(pass_rate, 2),
        "total_defects": len(defects),
        "open_defects": open_defects,
        "critical_defects": critical_defects,
        "defects_by_severity": defects_by_severity,
        "defects_by_status": defects_by_status,
        "average_time_to_test_hours": round(avg_time_to_test, 2),
        "average_test_duration_minutes": round(avg_test_duration, 2),
        "total_qa_tasks": total_qa_tasks,
        "on_time_completions": on_time_completions,
        "sla_compliance_percentage": round(sla_compliance, 2),
    }


def get_qa_calendar_events(db: Session, employee_id: Optional[int] = None) -> List[dict]:
    """
    Get QA calendar events (amendments with due dates).

    Args:
        db: Database session
        employee_id: Optional filter by assigned QA tester

    Returns:
        List of calendar event dicts
    """
    query = db.query(Amendment).filter(Amendment.qa_due_date.isnot(None))

    if employee_id:
        query = query.filter(Amendment.qa_assigned_id == employee_id)

    amendments = query.all()

    events = []
    for amendment in amendments:
        is_overdue = datetime.now() > amendment.qa_due_date if amendment.qa_due_date else False

        events.append({
            "event_id": amendment.amendment_id,
            "title": f"{amendment.amendment_reference} - {amendment.description[:50]}",
            "start": amendment.qa_due_date,
            "status": amendment.qa_status,
            "priority": amendment.priority,
            "is_overdue": is_overdue,
            "assigned_to": None,  # TODO: Get employee name
        })

    return events


def get_tester_workload(db: Session) -> List[dict]:
    """
    Get workload distribution across QA testers.

    Args:
        db: Database session

    Returns:
        List of tester workload dicts
    """
    from datetime import timedelta

    # Get all QA testers (employees with QA assignments)
    qa_testers = (
        db.query(Employee.employee_id, Employee.employee_name)
        .join(Amendment, Amendment.qa_assigned_id == Employee.employee_id)
        .distinct()
        .all()
    )

    workload = []
    week_ago = datetime.now() - timedelta(days=7)

    for tester_id, tester_name in qa_testers:
        # Get assigned amendments
        assigned = (
            db.query(Amendment)
            .filter(
                and_(
                    Amendment.qa_assigned_id == tester_id,
                    Amendment.qa_status.in_(["Assigned", "Not Started"]),
                )
            )
            .count()
        )

        # Get in testing
        in_testing = (
            db.query(Amendment)
            .filter(
                and_(
                    Amendment.qa_assigned_id == tester_id,
                    Amendment.qa_status == "In Testing",
                )
            )
            .count()
        )

        # Get overdue
        overdue = (
            db.query(Amendment)
            .filter(
                and_(
                    Amendment.qa_assigned_id == tester_id,
                    Amendment.qa_due_date < datetime.now(),
                    Amendment.qa_status != "Passed",
                )
            )
            .count()
        )

        # Get completed this week
        completed_this_week = (
            db.query(Amendment)
            .filter(
                and_(
                    Amendment.qa_assigned_id == tester_id,
                    Amendment.qa_status == "Passed",
                    Amendment.qa_completed_date >= week_ago,
                )
            )
            .count()
        )

        # Calculate average completion time
        completed = (
            db.query(Amendment)
            .filter(
                and_(
                    Amendment.qa_assigned_id == tester_id,
                    Amendment.qa_completed_date >= week_ago,
                    Amendment.qa_assigned_date.isnot(None),
                )
            )
            .all()
        )

        avg_completion_time = 0
        if completed:
            total_hours = sum(
                (a.qa_completed_date - a.qa_assigned_date).total_seconds() / 3600
                for a in completed
            )
            avg_completion_time = total_hours / len(completed)

        workload.append({
            "employee_id": tester_id,
            "employee_name": tester_name,
            "total_assigned": assigned,
            "in_testing": in_testing,
            "overdue": overdue,
            "completed_this_week": completed_this_week,
            "average_completion_time_hours": round(avg_completion_time, 2),
        })

    return workload


def check_overdue_qa(db: Session) -> List[Amendment]:
    """
    Find all overdue QA tasks.

    Args:
        db: Database session

    Returns:
        List of overdue amendments
    """
    return (
        db.query(Amendment)
        .filter(
            and_(
                Amendment.qa_due_date < datetime.now(),
                Amendment.qa_status.in_(
                    ["Assigned", "In Testing", "Blocked", "Not Started"]
                ),
            )
        )
        .all()
    )


# ============================================================================
# GitHub Issues Features - Comment Mentions
# ============================================================================


def parse_mentions(comment_text: str, db: Session) -> List[int]:
    """
    Extract @mentions from comment text.
    Returns list of employee_ids mentioned.
    Pattern: @username or @"First Last"

    Args:
        comment_text: The comment text to parse
        db: Database session

    Returns:
        List of employee IDs mentioned in the comment
    """
    import re
    # Pattern: @word or @"quoted name"
    mentions = re.findall(r'@(\w+|"[^"]+")', comment_text)

    employee_ids = []
    for mention in mentions:
        mention = mention.strip('"')
        # Search employees by username or name
        employee = db.query(Employee).filter(
            or_(
                Employee.username == mention,
                Employee.employee_name.ilike(f"%{mention}%")
            ),
            Employee.is_active == True
        ).first()
        if employee:
            employee_ids.append(employee.employee_id)

    return employee_ids


def create_comment_mentions(
    db: Session,
    comment_id: int,
    mentioned_employee_ids: List[int],
    mentioned_by_employee_id: int
) -> List[CommentMention]:
    """Create mention records and trigger notifications."""
    mentions = []
    for employee_id in mentioned_employee_ids:
        mention = CommentMention(
            comment_id=comment_id,
            mentioned_employee_id=employee_id,
            mentioned_by_employee_id=mentioned_by_employee_id
        )
        db.add(mention)
        mentions.append(mention)

    db.commit()

    # Auto-add mentioned users as watchers
    comment = db.query(QAComment).filter(QAComment.comment_id == comment_id).first()
    if comment:
        for employee_id in mentioned_employee_ids:
            add_watcher(db, comment.amendment_id, employee_id, reason="Mentioned")

    return mentions


def get_mentions_for_comment(db: Session, comment_id: int) -> List[CommentMention]:
    """Get all mentions for a comment."""
    return db.query(CommentMention).filter(
        CommentMention.comment_id == comment_id
    ).all()


# ============================================================================
# GitHub Issues Features - Amendment Watchers
# ============================================================================


def add_watcher(
    db: Session,
    amendment_id: int,
    employee_id: int,
    reason: str = "Manual"
) -> AmendmentWatcher:
    """Add user as watcher to amendment (idempotent)."""
    # Check if already watching
    existing = db.query(AmendmentWatcher).filter(
        AmendmentWatcher.amendment_id == amendment_id,
        AmendmentWatcher.employee_id == employee_id
    ).first()

    if existing:
        if not existing.is_watching:
            existing.is_watching = True
            db.commit()
        return existing

    watcher = AmendmentWatcher(
        amendment_id=amendment_id,
        employee_id=employee_id,
        watch_reason=reason
    )
    db.add(watcher)
    db.commit()
    db.refresh(watcher)
    return watcher


def remove_watcher(db: Session, amendment_id: int, employee_id: int):
    """Remove user as watcher (set is_watching=False)."""
    watcher = db.query(AmendmentWatcher).filter(
        AmendmentWatcher.amendment_id == amendment_id,
        AmendmentWatcher.employee_id == employee_id
    ).first()

    if watcher:
        watcher.is_watching = False
        db.commit()


def get_watchers(db: Session, amendment_id: int) -> List[AmendmentWatcher]:
    """Get all watchers for an amendment."""
    return db.query(AmendmentWatcher).filter(
        AmendmentWatcher.amendment_id == amendment_id,
        AmendmentWatcher.is_watching == True
    ).all()


def is_watching(db: Session, amendment_id: int, employee_id: int) -> bool:
    """Check if user is watching amendment."""
    watcher = db.query(AmendmentWatcher).filter(
        AmendmentWatcher.amendment_id == amendment_id,
        AmendmentWatcher.employee_id == employee_id,
        AmendmentWatcher.is_watching == True
    ).first()
    return watcher is not None


def notify_watchers(db: Session, amendment_id: int, event_type: str, message: str, exclude_employee_id: Optional[int] = None):
    """Notify all watchers of amendment about an event."""
    watchers = get_watchers(db, amendment_id)

    for watcher in watchers:
        # Skip the user who triggered the event
        if exclude_employee_id and watcher.employee_id == exclude_employee_id:
            continue

        # Check notification preferences
        if event_type == "comment" and not watcher.notify_comments:
            continue
        if event_type == "status_change" and not watcher.notify_status_changes:
            continue
        if event_type == "mention" and not watcher.notify_mentions:
            continue

        # Create notification (using existing notification system)
        create_notification(
            db,
            employee_id=watcher.employee_id,
            notification_type="Amendment Update",
            title=f"Amendment Update - {event_type}",
            message=message,
            amendment_id=amendment_id
        )


# ============================================================================
# GitHub Issues Features - Comment Reactions
# ============================================================================


def toggle_reaction(
    db: Session,
    comment_id: int,
    employee_id: int,
    emoji: str
) -> Optional[CommentReaction]:
    """
    Toggle reaction on comment.
    If exists, remove it. If not, add it.
    Returns reaction if added, None if removed.
    """
    existing = db.query(CommentReaction).filter(
        CommentReaction.comment_id == comment_id,
        CommentReaction.employee_id == employee_id,
        CommentReaction.emoji == emoji
    ).first()

    if existing:
        # Remove reaction
        db.delete(existing)
        db.commit()
        return None
    else:
        # Add reaction
        reaction = CommentReaction(
            comment_id=comment_id,
            employee_id=employee_id,
            emoji=emoji
        )
        db.add(reaction)
        db.commit()
        db.refresh(reaction)
        return reaction


def get_reactions_for_comment(db: Session, comment_id: int) -> List[CommentReaction]:
    """Get all reactions for a comment."""
    return db.query(CommentReaction).filter(
        CommentReaction.comment_id == comment_id
    ).all()


def get_reaction_summary(db: Session, comment_id: int) -> dict:
    """
    Get reaction summary for a comment.
    Returns: {"👍": 5, "❤️": 2, "🎉": 1}
    """
    reactions = get_reactions_for_comment(db, comment_id)
    summary = {}
    for reaction in reactions:
        emoji = reaction.emoji
        summary[emoji] = summary.get(emoji, 0) + 1
    return summary


# ============================================================================
# Enhanced Comment Creation (with threading and mentions)
# ============================================================================


def create_qa_comment_enhanced(
    db: Session,
    amendment_id: int,
    employee_id: int,
    comment_text: str,
    comment_type: str = "General",
    parent_comment_id: Optional[int] = None
) -> QAComment:
    """
    Create QA comment with automatic mention detection and watcher notification.

    Args:
        db: Database session
        amendment_id: Amendment ID
        employee_id: Employee creating the comment
        comment_text: Comment content
        comment_type: Type of comment (General/Issue/Resolution/Question)
        parent_comment_id: Parent comment ID for threading (optional)

    Returns:
        Created QA comment
    """
    # Create comment
    comment = QAComment(
        amendment_id=amendment_id,
        employee_id=employee_id,
        comment_text=comment_text,
        comment_type=comment_type,
        parent_comment_id=parent_comment_id
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    # Parse and create mentions
    mentioned_ids = parse_mentions(comment_text, db)
    if mentioned_ids:
        create_comment_mentions(db, comment.comment_id, mentioned_ids, employee_id)

    # Auto-add commenter as watcher
    add_watcher(db, amendment_id, employee_id, reason="Participated")

    # Notify watchers (except the commenter)
    employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if employee:
        notify_watchers(
            db,
            amendment_id,
            "comment",
            f"{employee.employee_name} commented: {comment_text[:100]}",
            exclude_employee_id=employee_id
        )

    return comment
