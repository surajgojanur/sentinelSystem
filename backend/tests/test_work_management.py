from app import db
from app.models.audit_log import AuditLog
from app.models import WorkAssignment, WorkProgressUpdate
import pytest


def _create_assignment(app, **overrides):
    payload = {
        "title": "Process Support Tickets",
        "description": "Handle inbound support queue",
        "assigned_by_user_id": overrides.pop("assigned_by_user_id"),
        "assigned_to_user_id": overrides.pop("assigned_to_user_id"),
        "expected_units": 50,
        "weight": 0.4,
        "status": "pending",
    }
    payload.update(overrides)

    with app.app_context():
        assignment = WorkAssignment(**payload)
        db.session.add(assignment)
        db.session.commit()
        db.session.refresh(assignment)
        return assignment.id


def _add_progress(app, assignment_id, reported_by_user_id, completed_units, note=None):
    with app.app_context():
        update = WorkProgressUpdate(
            assignment_id=assignment_id,
            reported_by_user_id=reported_by_user_id,
            completed_units=completed_units,
            note=note,
        )
        db.session.add(update)
        db.session.commit()
        return update.id


def test_assignment_model_defaults(app, users):
    assignment_id = _create_assignment(
        app,
        assigned_by_user_id=users["admin"],
        assigned_to_user_id=users["intern_bob"],
        title="Review Customer Replies",
        expected_units=10,
    )

    with app.app_context():
        assignment = WorkAssignment.query.get(assignment_id)
        assert assignment.status == "pending"
        assert assignment.weight == 0.4
        assert assignment.expected_units == 10


def test_admin_and_hr_can_create_assignment(client, auth_headers, users, app):
    for username, password in (("admin", "admin123"), ("hr_jane", "hr123")):
        response = client.post(
            "/api/work/assignments",
            headers=auth_headers(username, password),
            json={
                "title": f"Assignment from {username}",
                "assigned_to_user_id": users["intern_bob"],
                "expected_units": 12,
                "weight": 0.5,
                "due_date": "2026-05-01",
            },
        )
        assert response.status_code == 201, response.get_json()
        body = response.get_json()["assignment"]
        assert body["title"] == f"Assignment from {username}"
        assert body["status"] == "pending"
        assert body["kpi"]["expected_units"] == 12
        assert body["kpi"]["total_completed_units"] == 0

    with app.app_context():
        audit_queries = [
            row.query
            for row in db.session.query(AuditLog).order_by(AuditLog.id.asc()).all()
        ]
        assert len(audit_queries) == 2
        assert "Created work assignment" in audit_queries[0]
        assert "Created work assignment" in audit_queries[1]


def test_non_privileged_user_cannot_create_assignment(client, auth_headers, users):
    response = client.post(
        "/api/work/assignments",
        headers=auth_headers("intern_bob", "intern123"),
        json={
            "title": "Unauthorized Assignment",
            "assigned_to_user_id": users["intern_amy"],
            "expected_units": 10,
            "weight": 0.2,
        },
    )
    assert response.status_code == 403
    assert response.get_json()["error"] == "Admin/HR access required"


def test_assignee_list_is_scoped_and_kpi_is_aggregated(client, auth_headers, users, app):
    bob_assignment_id = _create_assignment(
        app,
        assigned_by_user_id=users["admin"],
        assigned_to_user_id=users["intern_bob"],
        title="Bob Assignment",
        expected_units=50,
        weight=0.4,
    )
    _create_assignment(
        app,
        assigned_by_user_id=users["admin"],
        assigned_to_user_id=users["intern_amy"],
        title="Amy Assignment",
        expected_units=20,
        weight=0.7,
    )
    _add_progress(app, bob_assignment_id, users["intern_bob"], 15, "Morning batch")
    _add_progress(app, bob_assignment_id, users["intern_bob"], 25, "Afternoon batch")

    response = client.get(
        "/api/work/assignments",
        headers=auth_headers("intern_bob", "intern123"),
    )

    assert response.status_code == 200
    assignments = response.get_json()["assignments"]
    assert len(assignments) == 1
    assignment = assignments[0]
    assert assignment["title"] == "Bob Assignment"
    assert assignment["kpi"]["expected_units"] == 50
    assert assignment["kpi"]["total_completed_units"] == 40
    assert assignment["kpi"]["completion_ratio"] == 0.8
    assert assignment["kpi"]["weighted_score"] == pytest.approx(0.32)


def test_assignee_can_submit_progress_and_status_transitions(client, auth_headers, users, app):
    assignment_id = _create_assignment(
        app,
        assigned_by_user_id=users["admin"],
        assigned_to_user_id=users["intern_bob"],
        expected_units=10,
        weight=0.5,
    )

    first = client.post(
        f"/api/work/assignments/{assignment_id}/progress",
        headers=auth_headers("intern_bob", "intern123"),
        json={"completed_units": 4},
    )
    assert first.status_code == 201, first.get_json()
    assert first.get_json()["progress_update"]["note"] is None
    assert first.get_json()["assignment"]["status"] == "in_progress"

    second = client.post(
        f"/api/work/assignments/{assignment_id}/progress",
        headers=auth_headers("intern_bob", "intern123"),
        json={"completed_units": 6, "note": "Closed remaining tickets"},
    )
    assert second.status_code == 201, second.get_json()
    assert second.get_json()["assignment"]["status"] == "completed"
    assert second.get_json()["assignment"]["kpi"]["total_completed_units"] == 10


def test_non_assignee_cannot_submit_progress(client, auth_headers, users, app):
    assignment_id = _create_assignment(
        app,
        assigned_by_user_id=users["admin"],
        assigned_to_user_id=users["intern_bob"],
    )

    response = client.post(
        f"/api/work/assignments/{assignment_id}/progress",
        headers=auth_headers("intern_amy", "intern456"),
        json={"completed_units": 3, "note": "Should fail"},
    )

    assert response.status_code == 403
    assert response.get_json()["error"] == "Only the assignee can submit progress"


def test_kpi_endpoint_returns_correct_values(client, auth_headers, users, app):
    assignment_id = _create_assignment(
        app,
        assigned_by_user_id=users["hr_jane"],
        assigned_to_user_id=users["intern_bob"],
        expected_units=25,
        weight=0.6,
    )
    _add_progress(app, assignment_id, users["intern_bob"], 10)
    _add_progress(app, assignment_id, users["intern_bob"], 5)

    response = client.get(
        f"/api/work/assignments/{assignment_id}/kpi",
        headers=auth_headers("intern_bob", "intern123"),
    )

    assert response.status_code == 200
    assert response.get_json()["kpi"] == {
        "expected_units": 25,
        "total_completed_units": 15,
        "completion_ratio": 0.6,
        "weighted_score": 0.36,
    }


def test_invalid_payloads_and_assignment_ids_are_rejected(client, auth_headers, users, app):
    admin_headers = auth_headers("admin", "admin123")

    bad_due_date = client.post(
        "/api/work/assignments",
        headers=admin_headers,
        json={
            "title": "Bad Due Date",
            "assigned_to_user_id": users["intern_bob"],
            "expected_units": 10,
            "weight": 0.3,
            "due_date": "not-a-date",
        },
    )
    assert bad_due_date.status_code == 400
    assert "due_date" in bad_due_date.get_json()["error"]

    bad_expected_units = client.post(
        "/api/work/assignments",
        headers=admin_headers,
        json={
            "title": "Bad Units",
            "assigned_to_user_id": users["intern_bob"],
            "expected_units": 0,
            "weight": 0.3,
        },
    )
    assert bad_expected_units.status_code == 400
    assert "expected_units" in bad_expected_units.get_json()["error"]

    missing_assignment_progress = client.post(
        "/api/work/assignments/9999/progress",
        headers=auth_headers("intern_bob", "intern123"),
        json={"completed_units": 1},
    )
    assert missing_assignment_progress.status_code == 404

    missing_assignment_kpi = client.get(
        "/api/work/assignments/9999/kpi",
        headers=admin_headers,
    )
    assert missing_assignment_kpi.status_code == 404


def test_compute_kpi_handles_zero_expected_units_and_over_completion(app, users):
    zero_assignment_id = _create_assignment(
        app,
        assigned_by_user_id=users["admin"],
        assigned_to_user_id=users["intern_bob"],
        title="Zero Target",
        expected_units=0,
        weight=0.9,
    )
    over_assignment_id = _create_assignment(
        app,
        assigned_by_user_id=users["admin"],
        assigned_to_user_id=users["intern_bob"],
        title="Over Completion",
        expected_units=5,
        weight=0.5,
    )
    _add_progress(app, over_assignment_id, users["intern_bob"], 7)

    with app.app_context():
        zero_assignment = WorkAssignment.query.get(zero_assignment_id)
        over_assignment = WorkAssignment.query.get(over_assignment_id)

        assert zero_assignment.compute_kpi() == {
            "expected_units": 0,
            "total_completed_units": 0,
            "completion_ratio": 0.0,
            "weighted_score": 0.0,
        }
        assert over_assignment.compute_kpi() == {
            "expected_units": 5,
            "total_completed_units": 7,
            "completion_ratio": 1.4,
            "weighted_score": 0.5,
        }
