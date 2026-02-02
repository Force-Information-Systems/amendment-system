"""
Pytest configuration and fixtures for amendment system tests
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from fastapi.testclient import TestClient

from backend.app.database import Base, get_db
from backend.app import models
from backend.app.main import app


@pytest.fixture(scope="function")
def test_engine():
    """Create an in-memory SQLite database engine for testing"""
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_session(test_engine):
    """Create a new database session for each test"""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def client(test_session):
    """FastAPI test client with database override"""
    def override_get_db():
        # Yield the same session used by fixtures
        # This ensures all operations use the same in-memory database
        yield test_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_amendment_data():
    """Sample data for creating an amendment"""
    return {
        "amendment_reference": "AMN-2024-001",
        "amendment_type": models.AmendmentType.ENHANCEMENT,
        "description": "Test amendment description",
        "amendment_status": models.AmendmentStatus.OPEN,
        "development_status": models.DevelopmentStatus.NOT_STARTED,
        "priority": models.Priority.MEDIUM,
        "reported_by": "Test User",
        "assigned_to": "Developer 1",
        "date_reported": datetime(2024, 1, 1, 10, 0, 0),
    }


@pytest.fixture
def sample_amendment(test_session, sample_amendment_data):
    """Create and return a sample amendment"""
    amendment = models.Amendment(**sample_amendment_data)
    test_session.add(amendment)
    test_session.commit()
    test_session.refresh(amendment)
    return amendment


@pytest.fixture
def sample_employee(test_session):
    """Create and return a sample employee for QA assignment tests"""
    employee = models.Employee(
        employee_name="QA Tester",
        initials="QT",
        email="qa.tester@example.com",
        windows_login="qtester",
        is_active=True
    )
    test_session.add(employee)
    test_session.commit()
    test_session.refresh(employee)
    return employee


@pytest.fixture
def sample_amendment_with_qa(test_session, sample_amendment_data, sample_employee):
    """Create amendment with QA fields already populated"""
    amendment = models.Amendment(**sample_amendment_data)
    amendment.qa_status = "In Testing"
    amendment.qa_assigned_id = sample_employee.employee_id
    amendment.qa_assigned_date = datetime(2024, 1, 15, 9, 0, 0)
    amendment.qa_started_date = datetime(2024, 1, 16, 10, 0, 0)
    amendment.qa_test_plan_check = True

    test_session.add(amendment)
    test_session.commit()
    test_session.refresh(amendment)
    return amendment
