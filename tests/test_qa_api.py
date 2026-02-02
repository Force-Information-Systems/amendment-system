"""
Integration tests for QA API endpoints.

Tests the PATCH /api/amendments/{id}/qa endpoint with comprehensive coverage
of all QA fields, status transitions, validation, and error cases.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from backend.app import models, schemas


# Test Cases: Happy Path

def test_patch_qa_endpoint_single_field(client, sample_amendment):
    """Test updating a single QA field"""
    response = client.patch(
        f"/api/amendments/{sample_amendment.amendment_id}/qa",
        json={"qa_status": "Assigned"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["qa_status"] == "Assigned"
    assert data["amendment_id"] == sample_amendment.amendment_id


def test_patch_qa_endpoint_multiple_fields(client, sample_amendment):
    """Test updating multiple QA fields at once"""
    response = client.patch(
        f"/api/amendments/{sample_amendment.amendment_id}/qa",
        json={
            "qa_status": "In Testing",
            "qa_test_plan_check": True,
            "qa_notes": "Started testing today"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["qa_status"] == "In Testing"
    assert data["qa_test_plan_check"] is True
    assert data["qa_notes"] == "Started testing today"


def test_patch_qa_endpoint_all_fields(client, sample_amendment):
    """Test updating all QA fields in a single request"""
    response = client.patch(
        f"/api/amendments/{sample_amendment.amendment_id}/qa",
        json={
            "qa_status": "Passed",
            "qa_assigned_id": 123,
            "qa_assigned_date": "2024-01-15T09:00:00",
            "qa_started_date": "2024-01-16T10:00:00",
            "qa_test_plan_check": True,
            "qa_test_release_notes_check": True,
            "qa_completed": True,
            "qa_signature": "Senior QA",
            "qa_completed_date": "2024-01-20T15:00:00",
            "qa_notes": "All tests passed successfully",
            "qa_test_plan_link": "https://testplan.example.com/123",
            "qa_blocked_reason": None,
            "modified_by": "test_user"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["qa_status"] == "Passed"
    assert data["qa_assigned_id"] == 123
    assert data["qa_test_plan_check"] is True
    assert data["qa_test_release_notes_check"] is True
    assert data["qa_completed"] is True
    assert data["qa_signature"] == "Senior QA"
    assert data["qa_notes"] == "All tests passed successfully"
    assert data["qa_test_plan_link"] == "https://testplan.example.com/123"


def test_patch_qa_endpoint_returns_full_amendment(client, sample_amendment):
    """Test that response includes full amendment object, not just QA fields"""
    response = client.patch(
        f"/api/amendments/{sample_amendment.amendment_id}/qa",
        json={"qa_status": "Assigned"}
    )

    assert response.status_code == 200
    data = response.json()

    # Verify non-QA fields are also present
    assert "amendment_reference" in data
    assert "description" in data
    assert "amendment_type" in data
    assert "priority" in data
    assert data["amendment_reference"] == sample_amendment.amendment_reference


# Test Cases: Status Workflow

def test_patch_qa_assign_tester(client, sample_amendment, sample_employee):
    """Test assigning a QA tester"""
    response = client.patch(
        f"/api/amendments/{sample_amendment.amendment_id}/qa",
        json={
            "qa_assigned_id": sample_employee.employee_id,
            "qa_assigned_date": datetime.now().isoformat(),
            "qa_status": "Assigned"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["qa_assigned_id"] == sample_employee.employee_id
    assert data["qa_status"] == "Assigned"
    assert data["qa_assigned_date"] is not None


def test_patch_qa_start_testing(client, sample_amendment_with_qa):
    """Test transitioning to In Testing status"""
    response = client.patch(
        f"/api/amendments/{sample_amendment_with_qa.amendment_id}/qa",
        json={
            "qa_status": "In Testing",
            "qa_started_date": datetime.now().isoformat()
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["qa_status"] == "In Testing"
    assert data["qa_started_date"] is not None


def test_patch_qa_mark_passed(client, sample_amendment_with_qa):
    """Test marking QA as Passed"""
    response = client.patch(
        f"/api/amendments/{sample_amendment_with_qa.amendment_id}/qa",
        json={
            "qa_status": "Passed",
            "qa_completed": True,
            "qa_completed_date": datetime.now().isoformat(),
            "qa_signature": "QA Engineer"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["qa_status"] == "Passed"
    assert data["qa_completed"] is True
    assert data["qa_completed_date"] is not None
    assert data["qa_signature"] == "QA Engineer"


def test_patch_qa_mark_failed(client, sample_amendment_with_qa):
    """Test marking QA as Failed"""
    response = client.patch(
        f"/api/amendments/{sample_amendment_with_qa.amendment_id}/qa",
        json={
            "qa_status": "Failed",
            "qa_completed": True,
            "qa_completed_date": datetime.now().isoformat(),
            "qa_notes": "Test failed: Critical bug found"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["qa_status"] == "Failed"
    assert data["qa_completed"] is True
    assert data["qa_notes"] == "Test failed: Critical bug found"


def test_patch_qa_mark_blocked(client, sample_amendment_with_qa):
    """Test marking QA as Blocked with reason"""
    response = client.patch(
        f"/api/amendments/{sample_amendment_with_qa.amendment_id}/qa",
        json={
            "qa_status": "Blocked",
            "qa_blocked_reason": "Test environment unavailable"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["qa_status"] == "Blocked"
    assert data["qa_blocked_reason"] == "Test environment unavailable"


# Test Cases: Checklist

def test_patch_qa_toggle_test_plan_check(client, sample_amendment):
    """Test toggling test plan checklist item"""
    # First toggle on
    response = client.patch(
        f"/api/amendments/{sample_amendment.amendment_id}/qa",
        json={"qa_test_plan_check": True}
    )

    assert response.status_code == 200
    assert response.json()["qa_test_plan_check"] is True

    # Then toggle off
    response = client.patch(
        f"/api/amendments/{sample_amendment.amendment_id}/qa",
        json={"qa_test_plan_check": False}
    )

    assert response.status_code == 200
    assert response.json()["qa_test_plan_check"] is False


def test_patch_qa_toggle_release_notes_check(client, sample_amendment):
    """Test toggling release notes checklist item"""
    response = client.patch(
        f"/api/amendments/{sample_amendment.amendment_id}/qa",
        json={"qa_test_release_notes_check": True}
    )

    assert response.status_code == 200
    assert response.json()["qa_test_release_notes_check"] is True


# Test Cases: Notes and Links

def test_patch_qa_add_notes(client, sample_amendment):
    """Test adding QA notes"""
    long_notes = "Comprehensive testing completed.\n\nAll test cases passed:\n- Login functionality\n- Data validation\n- API endpoints"

    response = client.patch(
        f"/api/amendments/{sample_amendment.amendment_id}/qa",
        json={"qa_notes": long_notes}
    )

    assert response.status_code == 200
    assert response.json()["qa_notes"] == long_notes


def test_patch_qa_add_test_plan_link(client, sample_amendment):
    """Test adding test plan link"""
    test_link = "https://testplan.example.com/plan-123"

    response = client.patch(
        f"/api/amendments/{sample_amendment.amendment_id}/qa",
        json={"qa_test_plan_link": test_link}
    )

    assert response.status_code == 200
    assert response.json()["qa_test_plan_link"] == test_link


def test_patch_qa_add_blocked_reason(client, sample_amendment):
    """Test adding blocked reason when status is Blocked"""
    response = client.patch(
        f"/api/amendments/{sample_amendment.amendment_id}/qa",
        json={
            "qa_status": "Blocked",
            "qa_blocked_reason": "Waiting for test data from client"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["qa_status"] == "Blocked"
    assert data["qa_blocked_reason"] == "Waiting for test data from client"


# Test Cases: Error Cases

def test_patch_qa_endpoint_invalid_amendment_id(client):
    """Test updating QA for non-existent amendment"""
    response = client.patch(
        "/api/amendments/999999/qa",
        json={"qa_status": "Passed"}
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_patch_qa_endpoint_invalid_field_type(client, sample_amendment):
    """Test validation error for invalid field type"""
    response = client.patch(
        f"/api/amendments/{sample_amendment.amendment_id}/qa",
        json={"qa_assigned_id": "not_a_number"}
    )

    assert response.status_code == 422


def test_patch_qa_endpoint_signature_too_long(client, sample_amendment):
    """Test validation error for signature exceeding max length"""
    long_signature = "A" * 101  # Max is 100

    response = client.patch(
        f"/api/amendments/{sample_amendment.amendment_id}/qa",
        json={"qa_signature": long_signature}
    )

    assert response.status_code == 422


def test_patch_qa_endpoint_test_plan_link_too_long(client, sample_amendment):
    """Test validation error for link exceeding max length"""
    long_link = "https://example.com/" + ("a" * 500)  # Max is 500

    response = client.patch(
        f"/api/amendments/{sample_amendment.amendment_id}/qa",
        json={"qa_test_plan_link": long_link}
    )

    assert response.status_code == 422


# Test Cases: Edge Cases

def test_patch_qa_endpoint_empty_body(client, sample_amendment):
    """Test PATCH with empty JSON body (no-op)"""
    response = client.patch(
        f"/api/amendments/{sample_amendment.amendment_id}/qa",
        json={}
    )

    # Should succeed with no changes
    assert response.status_code == 200
    data = response.json()
    assert data["amendment_id"] == sample_amendment.amendment_id


def test_patch_qa_endpoint_partial_update_preserves_fields(client, sample_amendment):
    """Test that partial update doesn't clear other QA fields"""
    # First, set multiple fields
    client.patch(
        f"/api/amendments/{sample_amendment.amendment_id}/qa",
        json={
            "qa_status": "Assigned",
            "qa_assigned_id": 789,
            "qa_notes": "Initial notes"
        }
    )

    # Then update only one field
    response = client.patch(
        f"/api/amendments/{sample_amendment.amendment_id}/qa",
        json={"qa_test_plan_check": True}
    )

    assert response.status_code == 200
    data = response.json()

    # New field updated
    assert data["qa_test_plan_check"] is True

    # Other fields preserved
    assert data["qa_status"] == "Assigned"
    assert data["qa_assigned_id"] == 789
    assert data["qa_notes"] == "Initial notes"


def test_patch_qa_endpoint_null_values(client, sample_amendment_with_qa):
    """Test setting fields to null/None"""
    response = client.patch(
        f"/api/amendments/{sample_amendment_with_qa.amendment_id}/qa",
        json={
            "qa_notes": None,
            "qa_blocked_reason": None
        }
    )

    assert response.status_code == 200
    data = response.json()
    # Null values should be accepted for optional fields
    assert data["qa_notes"] is None or data["qa_notes"] == ""
    assert data["qa_blocked_reason"] is None or data["qa_blocked_reason"] == ""


def test_patch_qa_endpoint_preserves_non_qa_fields(client, sample_amendment):
    """Test that QA updates don't affect non-QA fields"""
    original_description = sample_amendment.description
    original_priority = sample_amendment.priority

    response = client.patch(
        f"/api/amendments/{sample_amendment.amendment_id}/qa",
        json={"qa_status": "Assigned"}
    )

    assert response.status_code == 200
    data = response.json()

    # Non-QA fields should remain unchanged
    assert data["description"] == original_description
    assert data["priority"] == original_priority
