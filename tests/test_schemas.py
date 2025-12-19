"""
Quick test to validate Pydantic schemas work correctly.
This is a temporary test file for validation during development.
"""

from datetime import datetime
from backend.app.schemas import (
    AmendmentCreate,
    AmendmentUpdate,
    AmendmentFilter,
    AmendmentProgressCreate,
    AmendmentApplicationCreate,
    AmendmentLinkCreate,
    BulkUpdateRequest,
)
from backend.app.models import (
    AmendmentType,
    AmendmentStatus,
    DevelopmentStatus,
    Priority,
    LinkType,
)


def test_amendment_create():
    """Test AmendmentCreate schema validation."""
    print("Testing AmendmentCreate...")

    # Valid creation
    amendment = AmendmentCreate(
        amendment_type=AmendmentType.BUG,
        description="Test bug description",
        amendment_status=AmendmentStatus.OPEN,
        development_status=DevelopmentStatus.NOT_STARTED,
        priority=Priority.HIGH,
        force="Army",
        application="Test App",
        reported_by="John Doe",
        assigned_to="Jane Smith",
        date_reported=datetime.now(),
        created_by="admin",
    )

    print(f"  ✓ Valid amendment created: {amendment.description}")
    assert amendment.amendment_type == AmendmentType.BUG
    assert amendment.priority == Priority.HIGH

    # Test defaults
    amendment_minimal = AmendmentCreate(
        amendment_type=AmendmentType.FEATURE,
        description="Minimal amendment",
    )

    print(f"  ✓ Minimal amendment with defaults: status={amendment_minimal.amendment_status}")
    assert amendment_minimal.amendment_status == AmendmentStatus.OPEN
    assert amendment_minimal.development_status == DevelopmentStatus.NOT_STARTED
    assert amendment_minimal.priority == Priority.MEDIUM


def test_amendment_update():
    """Test AmendmentUpdate schema (partial updates)."""
    print("\nTesting AmendmentUpdate...")

    # Partial update
    update = AmendmentUpdate(
        amendment_status=AmendmentStatus.IN_PROGRESS,
        assigned_to="New Assignee",
        modified_by="admin",
    )

    print(f"  ✓ Partial update created: status={update.amendment_status}")
    assert update.amendment_status == AmendmentStatus.IN_PROGRESS
    assert update.description is None  # Not included in update


def test_amendment_filter():
    """Test AmendmentFilter schema for search queries."""
    print("\nTesting AmendmentFilter...")

    # Complex filter
    filter_query = AmendmentFilter(
        amendment_status=[AmendmentStatus.OPEN, AmendmentStatus.IN_PROGRESS],
        priority=[Priority.HIGH, Priority.CRITICAL],
        assigned_to=["John Doe", "Jane Smith"],
        date_reported_from=datetime(2024, 1, 1),
        date_reported_to=datetime(2024, 12, 31),
        search_text="bug fix",
        skip=0,
        limit=50,
        sort_by="priority",
        sort_order="desc",
    )

    print(f"  ✓ Complex filter created: {len(filter_query.amendment_status)} statuses")
    assert len(filter_query.amendment_status) == 2
    assert filter_query.limit == 50

    # Minimal filter with defaults
    minimal_filter = AmendmentFilter()
    print(f"  ✓ Minimal filter with defaults: skip={minimal_filter.skip}, limit={minimal_filter.limit}")
    assert minimal_filter.skip == 0
    assert minimal_filter.limit == 100


def test_progress_create():
    """Test AmendmentProgressCreate schema."""
    print("\nTesting AmendmentProgressCreate...")

    progress = AmendmentProgressCreate(
        start_date=datetime.now(),
        description="Started development work",
        notes="Initial setup complete",
        created_by="developer",
    )

    print(f"  ✓ Progress entry created: {progress.description}")
    assert progress.description == "Started development work"


def test_application_create():
    """Test AmendmentApplicationCreate schema."""
    print("\nTesting AmendmentApplicationCreate...")

    app = AmendmentApplicationCreate(
        application_name="Test Application",
        version="1.2.3",
    )

    print(f"  ✓ Application link created: {app.application_name} v{app.version}")
    assert app.application_name == "Test Application"


def test_link_create():
    """Test AmendmentLinkCreate schema."""
    print("\nTesting AmendmentLinkCreate...")

    link = AmendmentLinkCreate(
        linked_amendment_id=42,
        link_type=LinkType.BLOCKS,
    )

    print(f"  ✓ Amendment link created: type={link.link_type}")
    assert link.linked_amendment_id == 42
    assert link.link_type == LinkType.BLOCKS


def test_bulk_update():
    """Test BulkUpdateRequest schema."""
    print("\nTesting BulkUpdateRequest...")

    bulk = BulkUpdateRequest(
        amendment_ids=[1, 2, 3, 4, 5],
        updates=AmendmentUpdate(
            amendment_status=AmendmentStatus.COMPLETED,
            modified_by="admin",
        ),
    )

    print(f"  ✓ Bulk update created: {len(bulk.amendment_ids)} amendments")
    assert len(bulk.amendment_ids) == 5


def test_validation_errors():
    """Test that validation errors are raised correctly."""
    print("\nTesting validation errors...")

    try:
        # Missing required field (description)
        AmendmentCreate(amendment_type=AmendmentType.BUG)
        print("  ✗ Should have raised validation error")
        assert False
    except Exception as e:
        print(f"  ✓ Validation error raised correctly: {type(e).__name__}")

    try:
        # Invalid sort order
        AmendmentFilter(sort_order="invalid")
        print("  ✗ Should have raised validation error")
        assert False
    except Exception as e:
        print(f"  ✓ Validation error raised correctly: {type(e).__name__}")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Pydantic Schemas")
    print("=" * 60)

    test_amendment_create()
    test_amendment_update()
    test_amendment_filter()
    test_progress_create()
    test_application_create()
    test_link_create()
    test_bulk_update()
    test_validation_errors()

    print("\n" + "=" * 60)
    print("All schema tests passed! ✓")
    print("=" * 60)
