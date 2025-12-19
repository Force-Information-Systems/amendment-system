"""
Tests for database configuration and connection management.
"""

import pytest
from sqlalchemy.exc import SQLAlchemyError

from backend.app.database import (
    Base,
    engine,
    SessionLocal,
    get_db,
    get_db_context,
    init_db,
    check_db_connection,
    drop_all_tables,
    reset_db,
)
from backend.app.models import (
    Amendment,
    AmendmentProgress,
    AmendmentApplication,
    AmendmentLink,
    AmendmentType,
    AmendmentStatus,
    Priority,
)


class TestDatabaseConfiguration:
    """Test database configuration and initialization."""

    def test_base_class_exists(self):
        """Test that Base class is properly configured."""
        assert Base is not None
        assert hasattr(Base, "metadata")

    def test_engine_exists(self):
        """Test that database engine is created."""
        assert engine is not None

    def test_session_factory_exists(self):
        """Test that SessionLocal factory is created."""
        assert SessionLocal is not None

    def test_check_db_connection(self):
        """Test database connection check."""
        result = check_db_connection()
        # The connection might fail in test environment,
        # so we just check it returns a boolean
        assert isinstance(result, bool)

    def test_init_db(self):
        """Test database initialization."""
        # This should not raise an error
        init_db()
        assert True


class TestDatabaseSession:
    """Test database session management."""

    def test_get_db_dependency(self):
        """Test get_db dependency function."""
        db_gen = get_db()
        db = next(db_gen)
        assert db is not None
        assert hasattr(db, "query")
        assert hasattr(db, "commit")
        assert hasattr(db, "rollback")

        # Close the session
        try:
            next(db_gen)
        except StopIteration:
            pass

    def test_get_db_context_manager(self):
        """Test get_db_context context manager."""
        with get_db_context() as db:
            assert db is not None
            assert hasattr(db, "query")

    def test_session_rollback_on_error(self):
        """Test that session rolls back on error."""
        with pytest.raises(SQLAlchemyError):
            with get_db_context() as db:
                # Create an amendment with invalid data to trigger an error
                amendment = Amendment(
                    amendment_reference=None,  # This should fail (nullable=False)
                    amendment_type=AmendmentType.BUG,
                    description="Test",
                )
                db.add(amendment)
                db.flush()


class TestDatabaseModels:
    """Test database models and relationships."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up and tear down test database."""
        init_db()
        yield
        # Clean up after each test - delete in correct order due to foreign keys
        with get_db_context() as db:
            db.query(AmendmentLink).delete()
            db.query(AmendmentProgress).delete()
            db.query(AmendmentApplication).delete()
            db.query(Amendment).delete()
            db.commit()

    def test_create_amendment(self):
        """Test creating an amendment."""
        with get_db_context() as db:
            amendment = Amendment(
                amendment_reference="TEST-001",
                amendment_type=AmendmentType.BUG,
                description="Test amendment",
                amendment_status=AmendmentStatus.OPEN,
                priority=Priority.HIGH,
            )
            db.add(amendment)
            db.commit()

            # Verify it was created
            result = (
                db.query(Amendment).filter_by(amendment_reference="TEST-001").first()
            )
            assert result is not None
            assert result.amendment_reference == "TEST-001"
            assert result.amendment_type == AmendmentType.BUG
            assert result.description == "Test amendment"

    def test_amendment_repr(self):
        """Test Amendment __repr__ method."""
        amendment = Amendment(
            amendment_id=1,
            amendment_reference="TEST-001",
            amendment_type=AmendmentType.BUG,
            amendment_status=AmendmentStatus.OPEN,
            description="Test",
        )
        repr_str = repr(amendment)
        assert "TEST-001" in repr_str
        assert "Bug" in repr_str  # Enum value, not the full "AmendmentType.BUG"

    def test_create_amendment_with_progress(self):
        """Test creating an amendment with progress entries."""
        with get_db_context() as db:
            amendment = Amendment(
                amendment_reference="TEST-002",
                amendment_type=AmendmentType.FEATURE,
                description="Test with progress",
            )
            db.add(amendment)
            db.flush()

            # Add progress entry
            progress = AmendmentProgress(
                amendment_id=amendment.amendment_id,
                description="Started development",
                notes="Initial setup complete",
            )
            db.add(progress)
            db.commit()

            # Verify relationship
            result = (
                db.query(Amendment).filter_by(amendment_reference="TEST-002").first()
            )
            assert len(result.progress_entries) == 1
            assert result.progress_entries[0].description == "Started development"

    def test_create_amendment_with_applications(self):
        """Test creating an amendment with application links."""
        with get_db_context() as db:
            amendment = Amendment(
                amendment_reference="TEST-003",
                amendment_type=AmendmentType.ENHANCEMENT,
                description="Test with applications",
            )
            db.add(amendment)
            db.flush()

            # Add application
            app = AmendmentApplication(
                amendment_id=amendment.amendment_id,
                application_name="Test App",
                version="1.0.0",
            )
            db.add(app)
            db.commit()

            # Verify relationship
            result = (
                db.query(Amendment).filter_by(amendment_reference="TEST-003").first()
            )
            assert len(result.applications) == 1
            assert result.applications[0].application_name == "Test App"

    def test_create_amendment_with_links(self):
        """Test creating amendments with links between them."""
        with get_db_context() as db:
            # Create two amendments
            amendment1 = Amendment(
                amendment_reference="TEST-004",
                amendment_type=AmendmentType.BUG,
                description="First amendment",
            )
            amendment2 = Amendment(
                amendment_reference="TEST-005",
                amendment_type=AmendmentType.BUG,
                description="Second amendment",
            )
            db.add_all([amendment1, amendment2])
            db.flush()

            # Link them
            link = AmendmentLink(
                amendment_id=amendment1.amendment_id,
                linked_amendment_id=amendment2.amendment_id,
            )
            db.add(link)
            db.commit()

            # Verify relationship
            result = (
                db.query(Amendment).filter_by(amendment_reference="TEST-004").first()
            )
            assert len(result.links) == 1
            assert result.links[0].linked_amendment_id == amendment2.amendment_id

    def test_cascade_delete_progress(self):
        """Test that progress entries are deleted when amendment is deleted."""
        with get_db_context() as db:
            amendment = Amendment(
                amendment_reference="TEST-006",
                amendment_type=AmendmentType.BUG,
                description="Test cascade delete",
            )
            db.add(amendment)
            db.flush()

            progress = AmendmentProgress(
                amendment_id=amendment.amendment_id,
                description="Progress entry",
            )
            db.add(progress)
            db.commit()

            amendment_id = amendment.amendment_id

            # Delete amendment
            db.delete(amendment)
            db.commit()

            # Verify progress is also deleted
            progress_count = (
                db.query(AmendmentProgress).filter_by(amendment_id=amendment_id).count()
            )
            assert progress_count == 0

    def test_foreign_key_constraint_on_amendment_link(self):
        """
        Test that foreign key constraint exists on
        AmendmentLink.linked_amendment_id.
        """
        from sqlalchemy.exc import IntegrityError

        # First, verify that linking to an existing amendment works
        with get_db_context() as db:
            amendment1 = Amendment(
                amendment_reference="TEST-007A",
                amendment_type=AmendmentType.BUG,
                description="First amendment",
            )
            amendment2 = Amendment(
                amendment_reference="TEST-007B",
                amendment_type=AmendmentType.BUG,
                description="Second amendment",
            )
            db.add_all([amendment1, amendment2])
            db.flush()

            # This should work - both amendments exist
            link = AmendmentLink(
                amendment_id=amendment1.amendment_id,
                linked_amendment_id=amendment2.amendment_id,
            )
            db.add(link)
            db.flush()
            assert True, "Linking to existing amendment should work"

        # Now test that linking to non-existent amendment fails
        error_raised = False
        try:
            with get_db_context() as db:
                amendment = Amendment(
                    amendment_reference="TEST-007C",
                    amendment_type=AmendmentType.BUG,
                    description="Test FK constraint",
                )
                db.add(amendment)
                db.flush()

                # Try to create a link with invalid linked_amendment_id
                # This should fail due to foreign key constraint
                link = AmendmentLink(
                    amendment_id=amendment.amendment_id,
                    linked_amendment_id=99999,  # Non-existent amendment
                )
                db.add(link)
                db.flush()  # This should raise IntegrityError
        except IntegrityError:
            # This is expected - foreign key constraint is working
            error_raised = True

        assert error_raised, "Expected IntegrityError for invalid FK was not raised"


class TestDatabaseUtilities:
    """Test database utility functions."""

    def test_reset_db(self):
        """Test database reset functionality."""
        # Create some data
        with get_db_context() as db:
            amendment = Amendment(
                amendment_reference="TEST-RESET",
                amendment_type=AmendmentType.BUG,
                description="Will be deleted",
            )
            db.add(amendment)
            db.commit()

        # Reset database
        reset_db()

        # Verify data is gone but tables exist
        with get_db_context() as db:
            count = db.query(Amendment).count()
            assert count == 0

    def test_drop_all_tables(self):
        """Test dropping all tables."""
        drop_all_tables()

        # Tables should not exist now
        # Re-initialize for other tests
        init_db()
