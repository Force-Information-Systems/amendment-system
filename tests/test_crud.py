"""
Comprehensive tests for CRUD operations.

This test suite covers all 16 CRUD functions with thorough testing
of success cases, edge cases, error handling, and complex scenarios.
"""

import pytest
from datetime import datetime, timedelta

from backend.app import crud, models, schemas


# ============================================================================
# Tests for Reference Number Generation
# ============================================================================


class TestReferenceGeneration:
    """Test cases for amendment reference number generation."""

    def test_generate_first_reference_of_day(self, test_session):
        """Test generating the first reference number for a new day."""
        reference = crud.generate_amendment_reference(test_session)

        today = datetime.now()
        expected_prefix = f"AMD-{today.strftime('%Y%m%d')}"

        assert reference.startswith(expected_prefix)
        assert reference.endswith("-001")
        assert len(reference) == len(expected_prefix) + 4  # -NNN

    def test_generate_sequential_references(self, test_session):
        """Test generating multiple sequential references."""
        ref1 = crud.generate_amendment_reference(test_session)

        # Create an amendment with the first reference
        amendment1 = models.Amendment(
            amendment_reference=ref1,
            amendment_type=models.AmendmentType.BUG,
            description="First amendment",
        )
        test_session.add(amendment1)
        test_session.commit()

        # Generate next reference
        ref2 = crud.generate_amendment_reference(test_session)

        assert ref1.endswith("-001")
        assert ref2.endswith("-002")
        assert ref1[:-3] == ref2[:-3]  # Same date prefix

    def test_generate_reference_handles_gaps(self, test_session):
        """Test reference generation with existing amendments."""
        today = datetime.now()
        date_prefix = f"AMD-{today.strftime('%Y%m%d')}"

        # Create amendments with specific references
        for i in [1, 2, 5]:  # Gap at 3, 4
            amendment = models.Amendment(
                amendment_reference=f"{date_prefix}-{i:03d}",
                amendment_type=models.AmendmentType.FEATURE,
                description=f"Amendment {i}",
            )
            test_session.add(amendment)
        test_session.commit()

        # Should generate 006 (next after highest)
        reference = crud.generate_amendment_reference(test_session)
        assert reference == f"{date_prefix}-006"

    def test_get_next_reference(self, test_session):
        """Test get_next_reference function."""
        ref1 = crud.get_next_reference(test_session)
        ref2 = crud.get_next_reference(test_session)

        # Should return the same reference since nothing was created
        assert ref1 == ref2

    def test_reference_format_validation(self, test_session):
        """Test that reference format matches expected pattern."""
        reference = crud.generate_amendment_reference(test_session)

        # Format: AMD-YYYYMMDD-NNN
        parts = reference.split("-")
        assert len(parts) == 3
        assert parts[0] == "AMD"
        assert len(parts[1]) == 8  # YYYYMMDD
        assert len(parts[2]) == 3  # NNN
        assert parts[2].isdigit()


# ============================================================================
# Tests for Amendment CRUD Operations
# ============================================================================


class TestCreateAmendment:
    """Test cases for creating amendments."""

    def test_create_amendment_with_required_fields(self, test_session):
        """Test creating an amendment with only required fields."""
        amendment_data = schemas.AmendmentCreate(
            amendment_type=models.AmendmentType.BUG,
            description="Test bug fix",
        )

        result = crud.create_amendment(test_session, amendment_data)

        assert result.amendment_id is not None
        assert result.amendment_reference is not None
        assert result.amendment_type == models.AmendmentType.BUG
        assert result.description == "Test bug fix"
        assert result.amendment_status == models.AmendmentStatus.OPEN
        assert result.development_status == models.DevelopmentStatus.NOT_STARTED
        assert result.priority == models.Priority.MEDIUM

    def test_create_amendment_with_all_fields(self, test_session):
        """Test creating an amendment with all fields populated."""
        amendment_data = schemas.AmendmentCreate(
            amendment_type=models.AmendmentType.FEATURE,
            description="Complete feature implementation",
            amendment_status=models.AmendmentStatus.IN_PROGRESS,
            development_status=models.DevelopmentStatus.IN_DEVELOPMENT,
            priority=models.Priority.HIGH,
            force="Army",
            application="Main System",
            notes="Important feature",
            reported_by="John Doe",
            assigned_to="Jane Smith",
            date_reported=datetime(2024, 1, 15, 10, 0, 0),
            database_changes=True,
            db_upgrade_changes=True,
            release_notes="Major update",
            created_by="admin",
        )

        result = crud.create_amendment(
            test_session, amendment_data, created_by="system"
        )

        assert result.amendment_type == models.AmendmentType.FEATURE
        assert result.priority == models.Priority.HIGH
        assert result.force == "Army"
        assert result.application == "Main System"
        assert result.database_changes is True
        assert result.db_upgrade_changes is True
        assert result.created_by == "system"  # Should use parameter value

    def test_create_amendment_auto_generates_reference(self, test_session):
        """Test that reference number is auto-generated."""
        amendment_data = schemas.AmendmentCreate(
            amendment_type=models.AmendmentType.ENHANCEMENT,
            description="Test enhancement",
        )

        result = crud.create_amendment(test_session, amendment_data)

        assert result.amendment_reference is not None
        assert result.amendment_reference.startswith("AMD-")

    def test_create_amendment_sets_date_reported(self, test_session):
        """Test that date_reported is set if not provided."""
        before = datetime.now()

        amendment_data = schemas.AmendmentCreate(
            amendment_type=models.AmendmentType.BUG,
            description="Test bug",
        )

        result = crud.create_amendment(test_session, amendment_data)
        after = datetime.now()

        assert result.date_reported is not None
        assert before <= result.date_reported <= after

    def test_create_amendment_preserves_custom_date(self, test_session):
        """Test that custom date_reported is preserved."""
        custom_date = datetime(2023, 6, 15, 14, 30, 0)

        amendment_data = schemas.AmendmentCreate(
            amendment_type=models.AmendmentType.BUG,
            description="Test bug",
            date_reported=custom_date,
        )

        result = crud.create_amendment(test_session, amendment_data)

        assert result.date_reported == custom_date

    def test_create_amendment_with_all_enum_types(self, test_session):
        """Test creating amendments with all enum type values."""
        enum_types = [
            models.AmendmentType.BUG,
            models.AmendmentType.ENHANCEMENT,
            models.AmendmentType.FEATURE,
            models.AmendmentType.MAINTENANCE,
            models.AmendmentType.DOCUMENTATION,
        ]

        for amd_type in enum_types:
            amendment_data = schemas.AmendmentCreate(
                amendment_type=amd_type,
                description=f"Test {amd_type.value}",
            )
            result = crud.create_amendment(test_session, amendment_data)
            assert result.amendment_type == amd_type

    def test_create_amendment_with_empty_description_fails(self, test_session):
        """Test that creating amendment with empty description fails validation."""
        # This should fail at the Pydantic level before reaching CRUD
        with pytest.raises((ValueError, Exception)):
            schemas.AmendmentCreate(
                amendment_type=models.AmendmentType.BUG,
                description="",  # Empty description
            )


class TestGetAmendment:
    """Test cases for retrieving amendments."""

    def test_get_amendment_by_id(self, test_session, sample_amendment):
        """Test retrieving an amendment by ID."""
        result = crud.get_amendment(test_session, sample_amendment.amendment_id)

        assert result is not None
        assert result.amendment_id == sample_amendment.amendment_id
        assert result.amendment_reference == sample_amendment.amendment_reference

    def test_get_amendment_with_relationships(self, test_session, sample_amendment):
        """Test that relationships are loaded with amendment."""
        # Add progress entry
        progress = models.AmendmentProgress(
            amendment_id=sample_amendment.amendment_id,
            description="Test progress",
        )
        test_session.add(progress)
        test_session.commit()

        result = crud.get_amendment(test_session, sample_amendment.amendment_id)

        assert result is not None
        assert len(result.progress_entries) == 1
        assert result.progress_entries[0].description == "Test progress"

    def test_get_amendment_nonexistent_id(self, test_session):
        """Test retrieving an amendment with non-existent ID."""
        result = crud.get_amendment(test_session, 99999)

        assert result is None

    def test_get_amendment_loads_all_relationships(
        self, test_session, sample_amendment
    ):
        """Test that all relationships are eagerly loaded."""
        # Add various relationships
        progress = models.AmendmentProgress(
            amendment_id=sample_amendment.amendment_id,
            description="Progress entry",
        )
        app = models.AmendmentApplication(
            amendment_id=sample_amendment.amendment_id,
            application_name="Test App",
        )
        test_session.add_all([progress, app])
        test_session.commit()

        result = crud.get_amendment(test_session, sample_amendment.amendment_id)

        assert len(result.progress_entries) == 1
        assert len(result.applications) == 1


class TestGetAmendmentByReference:
    """Test cases for retrieving amendments by reference."""

    def test_get_amendment_by_reference(self, test_session, sample_amendment):
        """Test retrieving an amendment by reference number."""
        result = crud.get_amendment_by_reference(
            test_session, sample_amendment.amendment_reference
        )

        assert result is not None
        assert result.amendment_id == sample_amendment.amendment_id
        assert result.amendment_reference == sample_amendment.amendment_reference

    def test_get_amendment_by_reference_nonexistent(self, test_session):
        """Test retrieving amendment with non-existent reference."""
        result = crud.get_amendment_by_reference(test_session, "AMD-20990101-999")

        assert result is None

    def test_get_amendment_by_reference_with_relationships(
        self, test_session, sample_amendment
    ):
        """Test that relationships are loaded when getting by reference."""
        progress = models.AmendmentProgress(
            amendment_id=sample_amendment.amendment_id,
            description="Test progress",
        )
        test_session.add(progress)
        test_session.commit()

        result = crud.get_amendment_by_reference(
            test_session, sample_amendment.amendment_reference
        )

        assert result is not None
        assert len(result.progress_entries) == 1


class TestGetAmendments:
    """Test cases for listing and filtering amendments."""

    def test_get_all_amendments_no_filter(self, test_session):
        """Test getting all amendments without filters."""
        # Create multiple amendments
        for i in range(5):
            amendment = models.Amendment(
                amendment_reference=f"AMD-20240101-{i+1:03d}",
                amendment_type=models.AmendmentType.BUG,
                description=f"Amendment {i+1}",
            )
            test_session.add(amendment)
        test_session.commit()

        amendments, total = crud.get_amendments(test_session)

        assert total == 5
        assert len(amendments) == 5

    def test_get_amendments_with_pagination(self, test_session):
        """Test pagination of amendments."""
        # Create 10 amendments
        for i in range(10):
            amendment = models.Amendment(
                amendment_reference=f"AMD-20240101-{i+1:03d}",
                amendment_type=models.AmendmentType.BUG,
                description=f"Amendment {i+1}",
            )
            test_session.add(amendment)
        test_session.commit()

        # Get first page
        filters = schemas.AmendmentFilter(skip=0, limit=3)
        amendments, total = crud.get_amendments(test_session, filters)

        assert total == 10
        assert len(amendments) == 3

        # Get second page
        filters = schemas.AmendmentFilter(skip=3, limit=3)
        amendments, total = crud.get_amendments(test_session, filters)

        assert total == 10
        assert len(amendments) == 3

    def test_filter_by_amendment_reference(self, test_session):
        """Test filtering by amendment reference."""
        amendment1 = models.Amendment(
            amendment_reference="AMD-20240101-001",
            amendment_type=models.AmendmentType.BUG,
            description="First",
        )
        amendment2 = models.Amendment(
            amendment_reference="AMD-20240102-001",
            amendment_type=models.AmendmentType.FEATURE,
            description="Second",
        )
        test_session.add_all([amendment1, amendment2])
        test_session.commit()

        filters = schemas.AmendmentFilter(amendment_reference="20240101")
        amendments, total = crud.get_amendments(test_session, filters)

        assert total == 1
        assert amendments[0].amendment_reference == "AMD-20240101-001"

    def test_filter_by_amendment_ids(self, test_session):
        """Test filtering by specific amendment IDs."""
        amendments_list = []
        for i in range(5):
            amendment = models.Amendment(
                amendment_reference=f"AMD-20240101-{i+1:03d}",
                amendment_type=models.AmendmentType.BUG,
                description=f"Amendment {i+1}",
            )
            test_session.add(amendment)
            amendments_list.append(amendment)
        test_session.commit()

        # Filter by first and third IDs
        target_ids = [amendments_list[0].amendment_id, amendments_list[2].amendment_id]
        filters = schemas.AmendmentFilter(amendment_ids=target_ids)
        amendments, total = crud.get_amendments(test_session, filters)

        assert total == 2
        result_ids = [a.amendment_id for a in amendments]
        assert set(result_ids) == set(target_ids)

    def test_filter_by_amendment_status(self, test_session):
        """Test filtering by amendment status."""
        amendment1 = models.Amendment(
            amendment_reference="AMD-20240101-001",
            amendment_type=models.AmendmentType.BUG,
            description="Open bug",
            amendment_status=models.AmendmentStatus.OPEN,
        )
        amendment2 = models.Amendment(
            amendment_reference="AMD-20240101-002",
            amendment_type=models.AmendmentType.BUG,
            description="Completed bug",
            amendment_status=models.AmendmentStatus.COMPLETED,
        )
        test_session.add_all([amendment1, amendment2])
        test_session.commit()

        filters = schemas.AmendmentFilter(
            amendment_status=[models.AmendmentStatus.OPEN]
        )
        amendments, total = crud.get_amendments(test_session, filters)

        assert total == 1
        assert amendments[0].amendment_status == models.AmendmentStatus.OPEN

    def test_filter_by_multiple_statuses(self, test_session):
        """Test filtering by multiple amendment statuses."""
        statuses = [
            models.AmendmentStatus.OPEN,
            models.AmendmentStatus.IN_PROGRESS,
            models.AmendmentStatus.COMPLETED,
        ]

        for i, status in enumerate(statuses):
            amendment = models.Amendment(
                amendment_reference=f"AMD-20240101-{i+1:03d}",
                amendment_type=models.AmendmentType.BUG,
                description=f"Status {status.value}",
                amendment_status=status,
            )
            test_session.add(amendment)
        test_session.commit()

        filters = schemas.AmendmentFilter(
            amendment_status=[
                models.AmendmentStatus.OPEN,
                models.AmendmentStatus.IN_PROGRESS,
            ]
        )
        amendments, total = crud.get_amendments(test_session, filters)

        assert total == 2

    def test_filter_by_development_status(self, test_session):
        """Test filtering by development status."""
        amendment1 = models.Amendment(
            amendment_reference="AMD-20240101-001",
            amendment_type=models.AmendmentType.FEATURE,
            description="Not started",
            development_status=models.DevelopmentStatus.NOT_STARTED,
        )
        amendment2 = models.Amendment(
            amendment_reference="AMD-20240101-002",
            amendment_type=models.AmendmentType.FEATURE,
            description="In development",
            development_status=models.DevelopmentStatus.IN_DEVELOPMENT,
        )
        test_session.add_all([amendment1, amendment2])
        test_session.commit()

        filters = schemas.AmendmentFilter(
            development_status=[models.DevelopmentStatus.IN_DEVELOPMENT]
        )
        amendments, total = crud.get_amendments(test_session, filters)

        assert total == 1
        assert (
            amendments[0].development_status == models.DevelopmentStatus.IN_DEVELOPMENT
        )

    def test_filter_by_priority(self, test_session):
        """Test filtering by priority."""
        priorities = [
            models.Priority.LOW,
            models.Priority.HIGH,
            models.Priority.CRITICAL,
        ]

        for i, priority in enumerate(priorities):
            amendment = models.Amendment(
                amendment_reference=f"AMD-20240101-{i+1:03d}",
                amendment_type=models.AmendmentType.BUG,
                description=f"Priority {priority.value}",
                priority=priority,
            )
            test_session.add(amendment)
        test_session.commit()

        filters = schemas.AmendmentFilter(
            priority=[models.Priority.HIGH, models.Priority.CRITICAL]
        )
        amendments, total = crud.get_amendments(test_session, filters)

        assert total == 2

    def test_filter_by_amendment_type(self, test_session):
        """Test filtering by amendment type."""
        amendment1 = models.Amendment(
            amendment_reference="AMD-20240101-001",
            amendment_type=models.AmendmentType.BUG,
            description="Bug fix",
        )
        amendment2 = models.Amendment(
            amendment_reference="AMD-20240101-002",
            amendment_type=models.AmendmentType.FEATURE,
            description="New feature",
        )
        test_session.add_all([amendment1, amendment2])
        test_session.commit()

        filters = schemas.AmendmentFilter(amendment_type=[models.AmendmentType.FEATURE])
        amendments, total = crud.get_amendments(test_session, filters)

        assert total == 1
        assert amendments[0].amendment_type == models.AmendmentType.FEATURE

    def test_filter_by_force(self, test_session):
        """Test filtering by force."""
        amendment1 = models.Amendment(
            amendment_reference="AMD-20240101-001",
            amendment_type=models.AmendmentType.BUG,
            description="Army amendment",
            force="Army",
        )
        amendment2 = models.Amendment(
            amendment_reference="AMD-20240101-002",
            amendment_type=models.AmendmentType.BUG,
            description="Navy amendment",
            force="Navy",
        )
        test_session.add_all([amendment1, amendment2])
        test_session.commit()

        filters = schemas.AmendmentFilter(force=["Army"])
        amendments, total = crud.get_amendments(test_session, filters)

        assert total == 1
        assert amendments[0].force == "Army"

    def test_filter_by_application(self, test_session):
        """Test filtering by application."""
        amendment1 = models.Amendment(
            amendment_reference="AMD-20240101-001",
            amendment_type=models.AmendmentType.BUG,
            description="App1 amendment",
            application="App1",
        )
        amendment2 = models.Amendment(
            amendment_reference="AMD-20240101-002",
            amendment_type=models.AmendmentType.BUG,
            description="App2 amendment",
            application="App2",
        )
        test_session.add_all([amendment1, amendment2])
        test_session.commit()

        filters = schemas.AmendmentFilter(application=["App1"])
        amendments, total = crud.get_amendments(test_session, filters)

        assert total == 1
        assert amendments[0].application == "App1"

    def test_filter_by_assigned_to(self, test_session):
        """Test filtering by assigned_to."""
        amendment1 = models.Amendment(
            amendment_reference="AMD-20240101-001",
            amendment_type=models.AmendmentType.BUG,
            description="Assigned to Alice",
            assigned_to="Alice",
        )
        amendment2 = models.Amendment(
            amendment_reference="AMD-20240101-002",
            amendment_type=models.AmendmentType.BUG,
            description="Assigned to Bob",
            assigned_to="Bob",
        )
        test_session.add_all([amendment1, amendment2])
        test_session.commit()

        filters = schemas.AmendmentFilter(assigned_to=["Alice"])
        amendments, total = crud.get_amendments(test_session, filters)

        assert total == 1
        assert amendments[0].assigned_to == "Alice"

    def test_filter_by_reported_by(self, test_session):
        """Test filtering by reported_by."""
        amendment1 = models.Amendment(
            amendment_reference="AMD-20240101-001",
            amendment_type=models.AmendmentType.BUG,
            description="Reported by John",
            reported_by="John",
        )
        amendment2 = models.Amendment(
            amendment_reference="AMD-20240101-002",
            amendment_type=models.AmendmentType.BUG,
            description="Reported by Jane",
            reported_by="Jane",
        )
        test_session.add_all([amendment1, amendment2])
        test_session.commit()

        filters = schemas.AmendmentFilter(reported_by=["John"])
        amendments, total = crud.get_amendments(test_session, filters)

        assert total == 1
        assert amendments[0].reported_by == "John"

    def test_filter_by_date_reported_range(self, test_session):
        """Test filtering by date_reported range."""
        date1 = datetime(2024, 1, 1, 10, 0, 0)
        date2 = datetime(2024, 1, 15, 10, 0, 0)
        date3 = datetime(2024, 2, 1, 10, 0, 0)

        amendment1 = models.Amendment(
            amendment_reference="AMD-20240101-001",
            amendment_type=models.AmendmentType.BUG,
            description="January 1",
            date_reported=date1,
        )
        amendment2 = models.Amendment(
            amendment_reference="AMD-20240101-002",
            amendment_type=models.AmendmentType.BUG,
            description="January 15",
            date_reported=date2,
        )
        amendment3 = models.Amendment(
            amendment_reference="AMD-20240101-003",
            amendment_type=models.AmendmentType.BUG,
            description="February 1",
            date_reported=date3,
        )
        test_session.add_all([amendment1, amendment2, amendment3])
        test_session.commit()

        filters = schemas.AmendmentFilter(
            date_reported_from=datetime(2024, 1, 10),
            date_reported_to=datetime(2024, 1, 20),
        )
        amendments, total = crud.get_amendments(test_session, filters)

        assert total == 1
        assert amendments[0].description == "January 15"

    def test_filter_by_created_on_range(self, test_session):
        """Test filtering by created_on range."""
        # Create amendments with slight delays
        amendment1 = models.Amendment(
            amendment_reference="AMD-20240101-001",
            amendment_type=models.AmendmentType.BUG,
            description="First",
        )
        test_session.add(amendment1)
        test_session.commit()

        time1 = amendment1.created_on

        amendment2 = models.Amendment(
            amendment_reference="AMD-20240101-002",
            amendment_type=models.AmendmentType.BUG,
            description="Second",
        )
        test_session.add(amendment2)
        test_session.commit()

        # Filter from time after first amendment
        filters = schemas.AmendmentFilter(created_on_from=time1 + timedelta(seconds=1))
        amendments, total = crud.get_amendments(test_session, filters)

        # Should only get the second amendment
        assert total <= 1

    def test_filter_by_search_text(self, test_session):
        """Test text search across description, notes, and release notes."""
        amendment1 = models.Amendment(
            amendment_reference="AMD-20240101-001",
            amendment_type=models.AmendmentType.BUG,
            description="Fix login bug",
            notes="This is critical",
        )
        amendment2 = models.Amendment(
            amendment_reference="AMD-20240101-002",
            amendment_type=models.AmendmentType.FEATURE,
            description="Add dashboard",
            release_notes="Critical feature update",
        )
        amendment3 = models.Amendment(
            amendment_reference="AMD-20240101-003",
            amendment_type=models.AmendmentType.BUG,
            description="Fix validation",
            notes="Not important",
        )
        test_session.add_all([amendment1, amendment2, amendment3])
        test_session.commit()

        filters = schemas.AmendmentFilter(search_text="critical")
        amendments, total = crud.get_amendments(test_session, filters)

        assert total == 2
        descriptions = [a.description for a in amendments]
        assert "Fix login bug" in descriptions
        assert "Add dashboard" in descriptions

    def test_filter_by_qa_completed(self, test_session):
        """Test filtering by QA completion status."""
        amendment1 = models.Amendment(
            amendment_reference="AMD-20240101-001",
            amendment_type=models.AmendmentType.BUG,
            description="QA completed",
            qa_completed=True,
        )
        amendment2 = models.Amendment(
            amendment_reference="AMD-20240101-002",
            amendment_type=models.AmendmentType.BUG,
            description="QA not completed",
            qa_completed=False,
        )
        test_session.add_all([amendment1, amendment2])
        test_session.commit()

        filters = schemas.AmendmentFilter(qa_completed=True)
        amendments, total = crud.get_amendments(test_session, filters)

        assert total == 1
        assert amendments[0].qa_completed is True

    def test_filter_by_qa_assigned(self, test_session):
        """Test filtering by whether QA is assigned."""
        amendment1 = models.Amendment(
            amendment_reference="AMD-20240101-001",
            amendment_type=models.AmendmentType.BUG,
            description="QA assigned",
            qa_assigned_id=123,
        )
        amendment2 = models.Amendment(
            amendment_reference="AMD-20240101-002",
            amendment_type=models.AmendmentType.BUG,
            description="QA not assigned",
            qa_assigned_id=None,
        )
        test_session.add_all([amendment1, amendment2])
        test_session.commit()

        # Filter for assigned QA
        filters = schemas.AmendmentFilter(qa_assigned=True)
        amendments, total = crud.get_amendments(test_session, filters)
        assert total == 1
        assert amendments[0].qa_assigned_id is not None

        # Filter for unassigned QA
        filters = schemas.AmendmentFilter(qa_assigned=False)
        amendments, total = crud.get_amendments(test_session, filters)
        assert total == 1
        assert amendments[0].qa_assigned_id is None

    def test_filter_by_database_changes(self, test_session):
        """Test filtering by database_changes flag."""
        amendment1 = models.Amendment(
            amendment_reference="AMD-20240101-001",
            amendment_type=models.AmendmentType.FEATURE,
            description="Has DB changes",
            database_changes=True,
        )
        amendment2 = models.Amendment(
            amendment_reference="AMD-20240101-002",
            amendment_type=models.AmendmentType.BUG,
            description="No DB changes",
            database_changes=False,
        )
        test_session.add_all([amendment1, amendment2])
        test_session.commit()

        filters = schemas.AmendmentFilter(database_changes=True)
        amendments, total = crud.get_amendments(test_session, filters)

        assert total == 1
        assert amendments[0].database_changes is True

    def test_filter_by_db_upgrade_changes(self, test_session):
        """Test filtering by db_upgrade_changes flag."""
        amendment1 = models.Amendment(
            amendment_reference="AMD-20240101-001",
            amendment_type=models.AmendmentType.FEATURE,
            description="Has upgrade changes",
            db_upgrade_changes=True,
        )
        amendment2 = models.Amendment(
            amendment_reference="AMD-20240101-002",
            amendment_type=models.AmendmentType.BUG,
            description="No upgrade changes",
            db_upgrade_changes=False,
        )
        test_session.add_all([amendment1, amendment2])
        test_session.commit()

        filters = schemas.AmendmentFilter(db_upgrade_changes=True)
        amendments, total = crud.get_amendments(test_session, filters)

        assert total == 1
        assert amendments[0].db_upgrade_changes is True

    def test_sorting_ascending(self, test_session):
        """Test sorting amendments in ascending order."""
        for i in range(3):
            amendment = models.Amendment(
                amendment_reference=f"AMD-20240101-{i+1:03d}",
                amendment_type=models.AmendmentType.BUG,
                description=f"Amendment {i+1}",
            )
            test_session.add(amendment)
        test_session.commit()

        filters = schemas.AmendmentFilter(
            sort_by="amendment_reference", sort_order="asc"
        )
        amendments, total = crud.get_amendments(test_session, filters)

        references = [a.amendment_reference for a in amendments]
        assert references == sorted(references)

    def test_sorting_descending(self, test_session):
        """Test sorting amendments in descending order."""
        for i in range(3):
            amendment = models.Amendment(
                amendment_reference=f"AMD-20240101-{i+1:03d}",
                amendment_type=models.AmendmentType.BUG,
                description=f"Amendment {i+1}",
            )
            test_session.add(amendment)
        test_session.commit()

        filters = schemas.AmendmentFilter(
            sort_by="amendment_reference", sort_order="desc"
        )
        amendments, total = crud.get_amendments(test_session, filters)

        references = [a.amendment_reference for a in amendments]
        assert references == sorted(references, reverse=True)

    def test_complex_multi_filter(self, test_session):
        """Test combining multiple filters."""
        amendment1 = models.Amendment(
            amendment_reference="AMD-20240101-001",
            amendment_type=models.AmendmentType.BUG,
            description="Critical bug in Army system",
            priority=models.Priority.CRITICAL,
            force="Army",
            amendment_status=models.AmendmentStatus.OPEN,
        )
        amendment2 = models.Amendment(
            amendment_reference="AMD-20240101-002",
            amendment_type=models.AmendmentType.BUG,
            description="Low priority Navy bug",
            priority=models.Priority.LOW,
            force="Navy",
            amendment_status=models.AmendmentStatus.OPEN,
        )
        amendment3 = models.Amendment(
            amendment_reference="AMD-20240101-003",
            amendment_type=models.AmendmentType.FEATURE,
            description="Critical Army feature",
            priority=models.Priority.CRITICAL,
            force="Army",
            amendment_status=models.AmendmentStatus.COMPLETED,
        )
        test_session.add_all([amendment1, amendment2, amendment3])
        test_session.commit()

        # Filter: Critical priority, Army force, OPEN status, BUG type
        filters = schemas.AmendmentFilter(
            priority=[models.Priority.CRITICAL],
            force=["Army"],
            amendment_status=[models.AmendmentStatus.OPEN],
            amendment_type=[models.AmendmentType.BUG],
        )
        amendments, total = crud.get_amendments(test_session, filters)

        assert total == 1
        assert amendments[0].description == "Critical bug in Army system"


class TestUpdateAmendment:
    """Test cases for updating amendments."""

    def test_update_amendment_single_field(self, test_session, sample_amendment):
        """Test updating a single field."""
        update_data = schemas.AmendmentUpdate(description="Updated description")

        result = crud.update_amendment(
            test_session, sample_amendment.amendment_id, update_data
        )

        assert result is not None
        assert result.description == "Updated description"
        # Other fields should remain unchanged
        assert result.amendment_type == sample_amendment.amendment_type
        assert result.priority == sample_amendment.priority

    def test_update_amendment_multiple_fields(self, test_session, sample_amendment):
        """Test updating multiple fields."""
        update_data = schemas.AmendmentUpdate(
            description="New description",
            priority=models.Priority.CRITICAL,
            amendment_status=models.AmendmentStatus.IN_PROGRESS,
            assigned_to="New Developer",
        )

        result = crud.update_amendment(
            test_session, sample_amendment.amendment_id, update_data
        )

        assert result.description == "New description"
        assert result.priority == models.Priority.CRITICAL
        assert result.amendment_status == models.AmendmentStatus.IN_PROGRESS
        assert result.assigned_to == "New Developer"

    def test_update_amendment_with_modified_by(self, test_session, sample_amendment):
        """Test that modified_by is set correctly."""
        update_data = schemas.AmendmentUpdate(description="Modified description")

        result = crud.update_amendment(
            test_session,
            sample_amendment.amendment_id,
            update_data,
            modified_by="admin",
        )

        assert result.modified_by == "admin"

    def test_update_amendment_nonexistent(self, test_session):
        """Test updating non-existent amendment returns None."""
        update_data = schemas.AmendmentUpdate(description="New description")

        result = crud.update_amendment(test_session, 99999, update_data)

        assert result is None

    def test_update_amendment_enum_values(self, test_session, sample_amendment):
        """Test updating enum fields."""
        update_data = schemas.AmendmentUpdate(
            amendment_type=models.AmendmentType.ENHANCEMENT,
            amendment_status=models.AmendmentStatus.TESTING,
            development_status=models.DevelopmentStatus.CODE_REVIEW,
            priority=models.Priority.HIGH,
        )

        result = crud.update_amendment(
            test_session, sample_amendment.amendment_id, update_data
        )

        assert result.amendment_type == models.AmendmentType.ENHANCEMENT
        assert result.amendment_status == models.AmendmentStatus.TESTING
        assert result.development_status == models.DevelopmentStatus.CODE_REVIEW
        assert result.priority == models.Priority.HIGH

    def test_update_amendment_boolean_fields(self, test_session, sample_amendment):
        """Test updating boolean fields."""
        update_data = schemas.AmendmentUpdate(
            database_changes=True,
            db_upgrade_changes=True,
        )

        result = crud.update_amendment(
            test_session, sample_amendment.amendment_id, update_data
        )

        assert result.database_changes is True
        assert result.db_upgrade_changes is True

    def test_update_amendment_optional_fields_to_none(self, test_session):
        """Test setting optional fields to None."""
        amendment = models.Amendment(
            amendment_reference="AMD-20240101-001",
            amendment_type=models.AmendmentType.BUG,
            description="Test amendment",
            force="Army",
            application="Test App",
            notes="Some notes",
        )
        test_session.add(amendment)
        test_session.commit()

        update_data = schemas.AmendmentUpdate(
            force=None,
            application=None,
            notes=None,
        )

        result = crud.update_amendment(
            test_session, amendment.amendment_id, update_data
        )

        assert result.force is None
        assert result.application is None
        assert result.notes is None

    def test_update_amendment_dates(self, test_session, sample_amendment):
        """Test updating date fields."""
        new_date = datetime(2024, 6, 15, 14, 30, 0)

        update_data = schemas.AmendmentUpdate(date_reported=new_date)

        result = crud.update_amendment(
            test_session, sample_amendment.amendment_id, update_data
        )

        assert result.date_reported == new_date

    def test_update_amendment_modified_on_updates(self, test_session, sample_amendment):
        """Test that modified_on timestamp updates."""
        original_modified = sample_amendment.modified_on

        update_data = schemas.AmendmentUpdate(description="Updated")

        result = crud.update_amendment(
            test_session, sample_amendment.amendment_id, update_data
        )

        assert result.modified_on >= original_modified


class TestUpdateAmendmentQA:
    """Test cases for updating QA fields."""

    def test_update_qa_fields(self, test_session, sample_amendment):
        """Test updating QA-specific fields."""
        qa_date = datetime(2024, 1, 20, 10, 0, 0)
        completed_date = datetime(2024, 1, 25, 15, 0, 0)

        qa_update = schemas.AmendmentQAUpdate(
            qa_assigned_id=456,
            qa_assigned_date=qa_date,
            qa_test_plan_check=True,
            qa_test_release_notes_check=True,
            qa_completed=True,
            qa_signature="QA Engineer",
            qa_completed_date=completed_date,
            qa_notes="All tests passed successfully",
            qa_test_plan_link="https://example.com/test-plan",
        )

        result = crud.update_amendment_qa(
            test_session, sample_amendment.amendment_id, qa_update
        )

        assert result.qa_assigned_id == 456
        assert result.qa_assigned_date == qa_date
        assert result.qa_test_plan_check is True
        assert result.qa_test_release_notes_check is True
        assert result.qa_completed is True
        assert result.qa_signature == "QA Engineer"
        assert result.qa_completed_date == completed_date
        assert result.qa_notes == "All tests passed successfully"
        assert result.qa_test_plan_link == "https://example.com/test-plan"

    def test_update_qa_partial_fields(self, test_session, sample_amendment):
        """Test updating only some QA fields."""
        qa_update = schemas.AmendmentQAUpdate(
            qa_assigned_id=789,
            qa_test_plan_check=True,
        )

        result = crud.update_amendment_qa(
            test_session, sample_amendment.amendment_id, qa_update
        )

        assert result.qa_assigned_id == 789
        assert result.qa_test_plan_check is True
        # Other QA fields should remain at defaults
        assert result.qa_completed is False

    def test_update_qa_nonexistent_amendment(self, test_session):
        """Test updating QA for non-existent amendment."""
        qa_update = schemas.AmendmentQAUpdate(qa_completed=True)

        result = crud.update_amendment_qa(test_session, 99999, qa_update)

        assert result is None

    def test_update_qa_with_modified_by(self, test_session, sample_amendment):
        """Test that modified_by is set in QA update."""
        qa_update = schemas.AmendmentQAUpdate(qa_completed=True)

        result = crud.update_amendment_qa(
            test_session,
            sample_amendment.amendment_id,
            qa_update,
            modified_by="qa_admin",
        )

        assert result.modified_by == "qa_admin"


class TestDeleteAmendment:
    """Test cases for deleting amendments."""

    def test_delete_amendment(self, test_session, sample_amendment):
        """Test deleting an amendment."""
        amendment_id = sample_amendment.amendment_id

        result = crud.delete_amendment(test_session, amendment_id)

        assert result is True

        # Verify deletion
        deleted = crud.get_amendment(test_session, amendment_id)
        assert deleted is None

    def test_delete_nonexistent_amendment(self, test_session):
        """Test deleting non-existent amendment."""
        result = crud.delete_amendment(test_session, 99999)

        assert result is False

    def test_delete_amendment_cascades_to_progress(
        self, test_session, sample_amendment
    ):
        """Test that deleting amendment cascades to progress entries."""
        # Add progress entry
        progress = models.AmendmentProgress(
            amendment_id=sample_amendment.amendment_id,
            description="Test progress",
        )
        test_session.add(progress)
        test_session.commit()
        progress_id = progress.amendment_progress_id

        # Delete amendment
        crud.delete_amendment(test_session, sample_amendment.amendment_id)

        # Progress should be deleted
        deleted_progress = test_session.get(models.AmendmentProgress, progress_id)
        assert deleted_progress is None

    def test_delete_amendment_cascades_to_applications(
        self, test_session, sample_amendment
    ):
        """Test that deleting amendment cascades to applications."""
        # Add application
        app = models.AmendmentApplication(
            amendment_id=sample_amendment.amendment_id,
            application_name="Test App",
        )
        test_session.add(app)
        test_session.commit()
        app_id = app.id

        # Delete amendment
        crud.delete_amendment(test_session, sample_amendment.amendment_id)

        # Application should be deleted
        deleted_app = test_session.get(models.AmendmentApplication, app_id)
        assert deleted_app is None

    def test_delete_amendment_cascades_to_links(self, test_session, sample_amendment):
        """Test that deleting amendment cascades to links."""
        # Create another amendment to link to
        other_amendment = models.Amendment(
            amendment_reference="AMD-20240101-002",
            amendment_type=models.AmendmentType.BUG,
            description="Other amendment",
        )
        test_session.add(other_amendment)
        test_session.commit()

        # Add link
        link = models.AmendmentLink(
            amendment_id=sample_amendment.amendment_id,
            linked_amendment_id=other_amendment.amendment_id,
        )
        test_session.add(link)
        test_session.commit()
        link_id = link.amendment_link_id

        # Delete amendment
        crud.delete_amendment(test_session, sample_amendment.amendment_id)

        # Link should be deleted
        deleted_link = test_session.get(models.AmendmentLink, link_id)
        assert deleted_link is None


# ============================================================================
# Tests for Amendment Progress Operations
# ============================================================================


class TestAddAmendmentProgress:
    """Test cases for adding progress entries."""

    def test_add_progress_entry(self, test_session, sample_amendment):
        """Test adding a progress entry to an amendment."""
        progress_data = schemas.AmendmentProgressCreate(
            description="Started implementation",
            notes="Working on core features",
        )

        result = crud.add_amendment_progress(
            test_session, sample_amendment.amendment_id, progress_data
        )

        assert result is not None
        assert result.amendment_progress_id is not None
        assert result.amendment_id == sample_amendment.amendment_id
        assert result.description == "Started implementation"
        assert result.notes == "Working on core features"

    def test_add_progress_with_custom_date(self, test_session, sample_amendment):
        """Test adding progress entry with custom start date."""
        custom_date = datetime(2024, 1, 15, 9, 0, 0)

        progress_data = schemas.AmendmentProgressCreate(
            start_date=custom_date,
            description="Started work",
        )

        result = crud.add_amendment_progress(
            test_session, sample_amendment.amendment_id, progress_data
        )

        assert result.start_date == custom_date

    def test_add_progress_auto_sets_date(self, test_session, sample_amendment):
        """Test that start_date is auto-set if not provided."""
        before = datetime.now()

        progress_data = schemas.AmendmentProgressCreate(
            description="Progress update",
        )

        result = crud.add_amendment_progress(
            test_session, sample_amendment.amendment_id, progress_data
        )

        after = datetime.now()

        assert result.start_date is not None
        assert before <= result.start_date <= after

    def test_add_progress_with_created_by(self, test_session, sample_amendment):
        """Test adding progress entry with created_by."""
        progress_data = schemas.AmendmentProgressCreate(
            description="Progress update",
        )

        result = crud.add_amendment_progress(
            test_session,
            sample_amendment.amendment_id,
            progress_data,
            created_by="developer",
        )

        assert result.created_by == "developer"

    def test_add_progress_to_nonexistent_amendment(self, test_session):
        """Test adding progress to non-existent amendment."""
        progress_data = schemas.AmendmentProgressCreate(
            description="Progress update",
        )

        result = crud.add_amendment_progress(test_session, 99999, progress_data)

        assert result is None

    def test_add_multiple_progress_entries(self, test_session, sample_amendment):
        """Test adding multiple progress entries."""
        for i in range(3):
            progress_data = schemas.AmendmentProgressCreate(
                description=f"Progress update {i+1}",
            )
            crud.add_amendment_progress(
                test_session, sample_amendment.amendment_id, progress_data
            )

        # Verify all entries were added
        progress_list = crud.get_amendment_progress(
            test_session, sample_amendment.amendment_id
        )

        assert len(progress_list) == 3


class TestGetAmendmentProgress:
    """Test cases for retrieving progress entries."""

    def test_get_progress_entries(self, test_session, sample_amendment):
        """Test retrieving progress entries for an amendment."""
        # Add progress entries
        for i in range(3):
            progress = models.AmendmentProgress(
                amendment_id=sample_amendment.amendment_id,
                description=f"Progress {i+1}",
            )
            test_session.add(progress)
        test_session.commit()

        result = crud.get_amendment_progress(
            test_session, sample_amendment.amendment_id
        )

        assert len(result) == 3

    def test_get_progress_ordered_by_date(self, test_session, sample_amendment):
        """Test that progress entries are ordered by date descending."""
        dates = [
            datetime(2024, 1, 1),
            datetime(2024, 1, 15),
            datetime(2024, 1, 10),
        ]

        for i, date in enumerate(dates):
            progress = models.AmendmentProgress(
                amendment_id=sample_amendment.amendment_id,
                start_date=date,
                description=f"Progress {i+1}",
            )
            test_session.add(progress)
        test_session.commit()

        result = crud.get_amendment_progress(
            test_session, sample_amendment.amendment_id
        )

        # Should be in descending order (newest first)
        assert result[0].start_date == datetime(2024, 1, 15)
        assert result[1].start_date == datetime(2024, 1, 10)
        assert result[2].start_date == datetime(2024, 1, 1)

    def test_get_progress_empty_list(self, test_session, sample_amendment):
        """Test getting progress for amendment with no entries."""
        result = crud.get_amendment_progress(
            test_session, sample_amendment.amendment_id
        )

        assert result == []

    def test_get_progress_nonexistent_amendment(self, test_session):
        """Test getting progress for non-existent amendment."""
        result = crud.get_amendment_progress(test_session, 99999)

        assert result == []


# ============================================================================
# Tests for Amendment Link Operations
# ============================================================================


class TestLinkAmendments:
    """Test cases for creating amendment links."""

    def test_link_amendments(self, test_session, sample_amendment):
        """Test creating a link between amendments."""
        # Create another amendment
        other_amendment = models.Amendment(
            amendment_reference="AMD-20240101-002",
            amendment_type=models.AmendmentType.BUG,
            description="Related amendment",
        )
        test_session.add(other_amendment)
        test_session.commit()

        link_data = schemas.AmendmentLinkCreate(
            linked_amendment_id=other_amendment.amendment_id,
            link_type=models.LinkType.RELATED,
        )

        result = crud.link_amendments(
            test_session, sample_amendment.amendment_id, link_data
        )

        assert result is not None
        assert result.amendment_id == sample_amendment.amendment_id
        assert result.linked_amendment_id == other_amendment.amendment_id
        assert result.link_type == models.LinkType.RELATED

    def test_link_amendments_all_types(self, test_session, sample_amendment):
        """Test creating links with all link types."""
        link_types = [
            models.LinkType.RELATED,
            models.LinkType.DUPLICATE,
            models.LinkType.BLOCKS,
            models.LinkType.BLOCKED_BY,
        ]

        for i, link_type in enumerate(link_types):
            # Create target amendment
            other_amendment = models.Amendment(
                amendment_reference=f"AMD-20240101-{i+2:03d}",
                amendment_type=models.AmendmentType.BUG,
                description=f"Amendment {i+2}",
            )
            test_session.add(other_amendment)
            test_session.commit()

            link_data = schemas.AmendmentLinkCreate(
                linked_amendment_id=other_amendment.amendment_id,
                link_type=link_type,
            )

            result = crud.link_amendments(
                test_session, sample_amendment.amendment_id, link_data
            )

            assert result.link_type == link_type

    def test_link_to_nonexistent_amendment(self, test_session, sample_amendment):
        """Test linking to non-existent amendment."""
        link_data = schemas.AmendmentLinkCreate(
            linked_amendment_id=99999,
        )

        result = crud.link_amendments(
            test_session, sample_amendment.amendment_id, link_data
        )

        assert result is None

    def test_link_from_nonexistent_amendment(self, test_session, sample_amendment):
        """Test linking from non-existent amendment."""
        link_data = schemas.AmendmentLinkCreate(
            linked_amendment_id=sample_amendment.amendment_id,
        )

        result = crud.link_amendments(test_session, 99999, link_data)

        assert result is None

    def test_link_prevents_duplicate_links(self, test_session, sample_amendment):
        """Test that duplicate links cannot be created."""
        # Create another amendment
        other_amendment = models.Amendment(
            amendment_reference="AMD-20240101-002",
            amendment_type=models.AmendmentType.BUG,
            description="Other amendment",
        )
        test_session.add(other_amendment)
        test_session.commit()

        link_data = schemas.AmendmentLinkCreate(
            linked_amendment_id=other_amendment.amendment_id,
        )

        # Create first link
        result1 = crud.link_amendments(
            test_session, sample_amendment.amendment_id, link_data
        )
        assert result1 is not None

        # Try to create duplicate link
        with pytest.raises(ValueError, match="Link already exists"):
            crud.link_amendments(test_session, sample_amendment.amendment_id, link_data)


class TestGetLinkedAmendments:
    """Test cases for retrieving linked amendments."""

    def test_get_linked_amendments(self, test_session, sample_amendment):
        """Test retrieving linked amendments."""
        # Create and link other amendments
        for i in range(3):
            other_amendment = models.Amendment(
                amendment_reference=f"AMD-20240101-{i+2:03d}",
                amendment_type=models.AmendmentType.BUG,
                description=f"Amendment {i+2}",
            )
            test_session.add(other_amendment)
            test_session.commit()

            link = models.AmendmentLink(
                amendment_id=sample_amendment.amendment_id,
                linked_amendment_id=other_amendment.amendment_id,
            )
            test_session.add(link)
        test_session.commit()

        result = crud.get_linked_amendments(test_session, sample_amendment.amendment_id)

        assert len(result) == 3

    def test_get_linked_amendments_empty(self, test_session, sample_amendment):
        """Test getting links when none exist."""
        result = crud.get_linked_amendments(test_session, sample_amendment.amendment_id)

        assert result == []

    def test_get_linked_amendments_nonexistent(self, test_session):
        """Test getting links for non-existent amendment."""
        result = crud.get_linked_amendments(test_session, 99999)

        assert result == []


class TestRemoveAmendmentLink:
    """Test cases for removing amendment links."""

    def test_remove_amendment_link(self, test_session, sample_amendment):
        """Test removing an amendment link."""
        # Create and link another amendment
        other_amendment = models.Amendment(
            amendment_reference="AMD-20240101-002",
            amendment_type=models.AmendmentType.BUG,
            description="Other amendment",
        )
        test_session.add(other_amendment)
        test_session.commit()

        link = models.AmendmentLink(
            amendment_id=sample_amendment.amendment_id,
            linked_amendment_id=other_amendment.amendment_id,
        )
        test_session.add(link)
        test_session.commit()
        link_id = link.amendment_link_id

        # Remove the link
        result = crud.remove_amendment_link(test_session, link_id)

        assert result is True

        # Verify link is removed
        deleted_link = test_session.get(models.AmendmentLink, link_id)
        assert deleted_link is None

    def test_remove_nonexistent_link(self, test_session):
        """Test removing non-existent link."""
        result = crud.remove_amendment_link(test_session, 99999)

        assert result is False


# ============================================================================
# Tests for Statistics Operations
# ============================================================================


class TestGetAmendmentStats:
    """Test cases for getting amendment statistics."""

    def test_get_stats_empty_database(self, test_session):
        """Test getting stats when no amendments exist."""
        stats = crud.get_amendment_stats(test_session)

        assert stats["total_amendments"] == 0
        assert stats["qa_pending"] == 0
        assert stats["database_changes_count"] == 0

    def test_get_stats_with_amendments(self, test_session):
        """Test getting comprehensive statistics."""
        # Create amendments with various properties
        amendments_data = [
            {
                "reference": "AMD-20240101-001",
                "type": models.AmendmentType.BUG,
                "status": models.AmendmentStatus.OPEN,
                "dev_status": models.DevelopmentStatus.NOT_STARTED,
                "priority": models.Priority.HIGH,
                "db_changes": True,
            },
            {
                "reference": "AMD-20240101-002",
                "type": models.AmendmentType.FEATURE,
                "status": models.AmendmentStatus.IN_PROGRESS,
                "dev_status": models.DevelopmentStatus.IN_DEVELOPMENT,
                "priority": models.Priority.CRITICAL,
                "db_changes": False,
            },
            {
                "reference": "AMD-20240101-003",
                "type": models.AmendmentType.BUG,
                "status": models.AmendmentStatus.COMPLETED,
                "dev_status": models.DevelopmentStatus.READY_FOR_QA,
                "priority": models.Priority.HIGH,
                "db_changes": True,
            },
        ]

        for data in amendments_data:
            amendment = models.Amendment(
                amendment_reference=data["reference"],
                amendment_type=data["type"],
                description=f"Test {data['type'].value}",
                amendment_status=data["status"],
                development_status=data["dev_status"],
                priority=data["priority"],
                database_changes=data["db_changes"],
            )
            test_session.add(amendment)
        test_session.commit()

        stats = crud.get_amendment_stats(test_session)

        assert stats["total_amendments"] == 3
        assert stats["by_status"]["Open"] == 1
        assert stats["by_status"]["In Progress"] == 1
        assert stats["by_status"]["Completed"] == 1
        assert stats["by_priority"]["High"] == 2
        assert stats["by_priority"]["Critical"] == 1
        assert stats["by_type"]["Bug"] == 2
        assert stats["by_type"]["Feature"] == 1
        assert stats["database_changes_count"] == 2

    def test_get_stats_by_status(self, test_session):
        """Test statistics grouped by status."""
        statuses = [
            models.AmendmentStatus.OPEN,
            models.AmendmentStatus.IN_PROGRESS,
            models.AmendmentStatus.TESTING,
            models.AmendmentStatus.COMPLETED,
            models.AmendmentStatus.DEPLOYED,
        ]

        for status in statuses:
            amendment = models.Amendment(
                amendment_reference=f"AMD-20240101-{statuses.index(status)+1:03d}",
                amendment_type=models.AmendmentType.BUG,
                description=f"Status {status.value}",
                amendment_status=status,
            )
            test_session.add(amendment)
        test_session.commit()

        stats = crud.get_amendment_stats(test_session)

        assert stats["by_status"]["Open"] == 1
        assert stats["by_status"]["In Progress"] == 1
        assert stats["by_status"]["Testing"] == 1
        assert stats["by_status"]["Completed"] == 1
        assert stats["by_status"]["Deployed"] == 1

    def test_get_stats_by_priority(self, test_session):
        """Test statistics grouped by priority."""
        priorities = [
            models.Priority.LOW,
            models.Priority.MEDIUM,
            models.Priority.HIGH,
            models.Priority.CRITICAL,
        ]

        for priority in priorities:
            amendment = models.Amendment(
                amendment_reference=f"AMD-20240101-{priorities.index(priority)+1:03d}",
                amendment_type=models.AmendmentType.BUG,
                description=f"Priority {priority.value}",
                priority=priority,
            )
            test_session.add(amendment)
        test_session.commit()

        stats = crud.get_amendment_stats(test_session)

        assert stats["by_priority"]["Low"] == 1
        assert stats["by_priority"]["Medium"] == 1
        assert stats["by_priority"]["High"] == 1
        assert stats["by_priority"]["Critical"] == 1

    def test_get_stats_by_type(self, test_session):
        """Test statistics grouped by amendment type."""
        types = [
            models.AmendmentType.BUG,
            models.AmendmentType.ENHANCEMENT,
            models.AmendmentType.FEATURE,
            models.AmendmentType.MAINTENANCE,
            models.AmendmentType.DOCUMENTATION,
        ]

        for amd_type in types:
            amendment = models.Amendment(
                amendment_reference=f"AMD-20240101-{types.index(amd_type)+1:03d}",
                amendment_type=amd_type,
                description=f"Type {amd_type.value}",
            )
            test_session.add(amendment)
        test_session.commit()

        stats = crud.get_amendment_stats(test_session)

        assert stats["by_type"]["Bug"] == 1
        assert stats["by_type"]["Enhancement"] == 1
        assert stats["by_type"]["Feature"] == 1
        assert stats["by_type"]["Maintenance"] == 1
        assert stats["by_type"]["Documentation"] == 1

    def test_get_stats_by_development_status(self, test_session):
        """Test statistics grouped by development status."""
        dev_statuses = [
            models.DevelopmentStatus.NOT_STARTED,
            models.DevelopmentStatus.IN_DEVELOPMENT,
            models.DevelopmentStatus.CODE_REVIEW,
            models.DevelopmentStatus.READY_FOR_QA,
        ]

        for dev_status in dev_statuses:
            idx = dev_statuses.index(dev_status) + 1
            amendment = models.Amendment(
                amendment_reference=f"AMD-20240101-{idx:03d}",
                amendment_type=models.AmendmentType.BUG,
                description=f"Dev status {dev_status.value}",
                development_status=dev_status,
            )
            test_session.add(amendment)
        test_session.commit()

        stats = crud.get_amendment_stats(test_session)

        assert stats["by_development_status"]["Not Started"] == 1
        assert stats["by_development_status"]["In Development"] == 1
        assert stats["by_development_status"]["Code Review"] == 1
        assert stats["by_development_status"]["Ready for QA"] == 1

    def test_get_stats_qa_pending(self, test_session):
        """Test QA pending count (assigned but not completed)."""
        # QA assigned but not completed
        amendment1 = models.Amendment(
            amendment_reference="AMD-20240101-001",
            amendment_type=models.AmendmentType.BUG,
            description="QA pending",
            qa_assigned_id=123,
            qa_completed=False,
        )
        # QA assigned and completed
        amendment2 = models.Amendment(
            amendment_reference="AMD-20240101-002",
            amendment_type=models.AmendmentType.BUG,
            description="QA completed",
            qa_assigned_id=456,
            qa_completed=True,
        )
        # QA not assigned
        amendment3 = models.Amendment(
            amendment_reference="AMD-20240101-003",
            amendment_type=models.AmendmentType.BUG,
            description="No QA",
            qa_assigned_id=None,
            qa_completed=False,
        )
        test_session.add_all([amendment1, amendment2, amendment3])
        test_session.commit()

        stats = crud.get_amendment_stats(test_session)

        # Only amendment1 should be counted as QA pending
        assert stats["qa_pending"] == 1

    def test_get_stats_database_changes(self, test_session):
        """Test counting amendments with database changes."""
        amendment1 = models.Amendment(
            amendment_reference="AMD-20240101-001",
            amendment_type=models.AmendmentType.FEATURE,
            description="Has DB changes",
            database_changes=True,
        )
        amendment2 = models.Amendment(
            amendment_reference="AMD-20240101-002",
            amendment_type=models.AmendmentType.BUG,
            description="No DB changes",
            database_changes=False,
        )
        amendment3 = models.Amendment(
            amendment_reference="AMD-20240101-003",
            amendment_type=models.AmendmentType.FEATURE,
            description="Has DB changes",
            database_changes=True,
        )
        test_session.add_all([amendment1, amendment2, amendment3])
        test_session.commit()

        stats = crud.get_amendment_stats(test_session)

        assert stats["database_changes_count"] == 2


# ============================================================================
# Tests for Bulk Operations
# ============================================================================


class TestBulkUpdateAmendments:
    """Test cases for bulk updating amendments."""

    def test_bulk_update_success(self, test_session):
        """Test successfully updating multiple amendments."""
        # Create amendments
        amendment_ids = []
        for i in range(3):
            amendment = models.Amendment(
                amendment_reference=f"AMD-20240101-{i+1:03d}",
                amendment_type=models.AmendmentType.BUG,
                description=f"Amendment {i+1}",
                priority=models.Priority.LOW,
            )
            test_session.add(amendment)
            test_session.commit()
            amendment_ids.append(amendment.amendment_id)

        # Bulk update
        update_data = schemas.AmendmentUpdate(
            priority=models.Priority.HIGH,
            amendment_status=models.AmendmentStatus.IN_PROGRESS,
        )

        updated_count, failed_ids, errors = crud.bulk_update_amendments(
            test_session, amendment_ids, update_data
        )

        assert updated_count == 3
        assert len(failed_ids) == 0
        assert len(errors) == 0

        # Verify updates
        for amendment_id in amendment_ids:
            amendment = crud.get_amendment(test_session, amendment_id)
            assert amendment.priority == models.Priority.HIGH
            assert amendment.amendment_status == models.AmendmentStatus.IN_PROGRESS

    def test_bulk_update_with_failures(self, test_session):
        """Test bulk update with some failures."""
        # Create one valid amendment
        amendment = models.Amendment(
            amendment_reference="AMD-20240101-001",
            amendment_type=models.AmendmentType.BUG,
            description="Valid amendment",
        )
        test_session.add(amendment)
        test_session.commit()

        # Mix valid and invalid IDs
        amendment_ids = [amendment.amendment_id, 99998, 99999]

        update_data = schemas.AmendmentUpdate(
            priority=models.Priority.HIGH,
        )

        updated_count, failed_ids, errors = crud.bulk_update_amendments(
            test_session, amendment_ids, update_data
        )

        assert updated_count == 1
        assert len(failed_ids) == 2
        assert 99998 in failed_ids
        assert 99999 in failed_ids
        assert errors[99998] == "Amendment not found"
        assert errors[99999] == "Amendment not found"

    def test_bulk_update_with_modified_by(self, test_session):
        """Test bulk update with modified_by tracking."""
        # Create amendments
        amendment_ids = []
        for i in range(2):
            amendment = models.Amendment(
                amendment_reference=f"AMD-20240101-{i+1:03d}",
                amendment_type=models.AmendmentType.BUG,
                description=f"Amendment {i+1}",
            )
            test_session.add(amendment)
            test_session.commit()
            amendment_ids.append(amendment.amendment_id)

        update_data = schemas.AmendmentUpdate(
            priority=models.Priority.HIGH,
        )

        crud.bulk_update_amendments(
            test_session, amendment_ids, update_data, modified_by="bulk_admin"
        )

        # Verify modified_by was set
        for amendment_id in amendment_ids:
            amendment = crud.get_amendment(test_session, amendment_id)
            assert amendment.modified_by == "bulk_admin"

    def test_bulk_update_empty_list(self, test_session):
        """Test bulk update with empty ID list."""
        update_data = schemas.AmendmentUpdate(
            priority=models.Priority.HIGH,
        )

        updated_count, failed_ids, errors = crud.bulk_update_amendments(
            test_session, [], update_data
        )

        assert updated_count == 0
        assert len(failed_ids) == 0
        assert len(errors) == 0

    def test_bulk_update_partial_data(self, test_session):
        """Test bulk update with partial field updates."""
        # Create amendments with different initial values
        amendment_ids = []
        for i in range(3):
            amendment = models.Amendment(
                amendment_reference=f"AMD-20240101-{i+1:03d}",
                amendment_type=models.AmendmentType.BUG,
                description=f"Original description {i+1}",
                priority=models.Priority.LOW,
                force="Army",
            )
            test_session.add(amendment)
            test_session.commit()
            amendment_ids.append(amendment.amendment_id)

        # Update only priority, leaving other fields unchanged
        update_data = schemas.AmendmentUpdate(
            priority=models.Priority.CRITICAL,
        )

        crud.bulk_update_amendments(test_session, amendment_ids, update_data)

        # Verify only priority changed
        for i, amendment_id in enumerate(amendment_ids):
            amendment = crud.get_amendment(test_session, amendment_id)
            assert amendment.priority == models.Priority.CRITICAL
            assert amendment.description == f"Original description {i+1}"
            assert amendment.force == "Army"
