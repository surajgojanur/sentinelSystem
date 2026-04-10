from datetime import UTC, datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy.orm import joinedload

from app import db
from app.models.attendance_record import AttendanceRecord
from app.models.audit_log import AuditLog
from app.models.user import User
from app.models.work_assignment import WorkAssignment
from app.models.work_escalation import WorkEscalation
from app.models.work_progress_update import WorkProgressUpdate

work_management_bp = Blueprint("work_management", __name__)

ALLOWED_STATUSES = {"pending", "in_progress", "completed"}
BOARD_ALLOWED_STATUSES = {"todo", "in_progress", "blocked", "completed"}
RISK_LEVEL_ORDER = {"low": 0, "medium": 1, "high": 2}


def _current_user():
    user_id = int(get_jwt_identity())
    return db.session.get(User, user_id)


def _is_admin_or_hr(user: User | None) -> bool:
    return bool(user and user.role in ("admin", "hr"))


def _parse_due_date(value):
    if value in (None, ""):
        return None

    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _compute_kpi(assignment: WorkAssignment):
    return assignment.compute_kpi()


def _board_status(value: str | None):
    if value == "pending":
        return "todo"
    return value or "todo"


def _compute_capacity_risk(assignment: WorkAssignment):
    kpi = _compute_kpi(assignment)
    completion_ratio = float(kpi["completion_ratio"] or 0)
    today = datetime.now(UTC).date()

    risk_level = "low"
    reasons = []

    def elevate(level: str, reason: str):
        nonlocal risk_level
        if RISK_LEVEL_ORDER[level] > RISK_LEVEL_ORDER[risk_level]:
            risk_level = level
        reasons.append(reason)

    due_date = assignment.normalized_due_date()
    if due_date and assignment.status != "completed":
        days_until_due = (due_date - today).days
        if days_until_due < 0:
            elevate("high", "Overdue and not completed.")
        elif days_until_due <= 2 and completion_ratio < 0.5:
            elevate("high", "Due within 2 days with low completion.")
        elif days_until_due <= 5 and completion_ratio < 0.75:
            elevate("medium", "Due soon with below-target completion.")

    if assignment.status != "completed":
        attendance_cutoff = datetime.now(UTC) - timedelta(days=3)
        recent_attendance = (
            AttendanceRecord.query
            .filter(
                AttendanceRecord.user_id == assignment.assigned_to_user_id,
                AttendanceRecord.created_at >= attendance_cutoff,
            )
            .order_by(AttendanceRecord.created_at.desc())
            .first()
        )
        if not recent_attendance:
            if risk_level == "high":
                elevate("high", "No recent attendance signal for assignee.")
            else:
                elevate("medium", "No recent attendance signal for assignee.")

        active_incomplete_count = (
            WorkAssignment.query
            .filter(
                WorkAssignment.assigned_to_user_id == assignment.assigned_to_user_id,
                WorkAssignment.status != "completed",
            )
            .count()
        )
        if active_incomplete_count >= 3:
            elevate("medium", "Assignee has many active incomplete assignments.")

    return {
        "level": risk_level,
        "reasons": reasons,
        "signals": {
            "completion_ratio": round(completion_ratio, 4),
            "days_until_due": (due_date - today).days if due_date else None,
        },
    }


def _serialize_assignment(assignment: WorkAssignment, include_progress=False, board_view=False):
    payload = assignment.to_dict(include_progress=include_progress)
    assigned_by = db.session.get(User, assignment.assigned_by_user_id)
    assigned_to = db.session.get(User, assignment.assigned_to_user_id)
    payload["assigned_by_username"] = assigned_by.username if assigned_by else None
    payload["assigned_to_username"] = assigned_to.username if assigned_to else None
    payload["assigned_by_user"] = assigned_by.to_dict() if assigned_by else None
    payload["assigned_to_user"] = assigned_to.to_dict() if assigned_to else None
    payload["capacity_risk"] = _compute_capacity_risk(assignment)
    open_escalation = next((item for item in assignment.escalations if item.status == "open"), None)
    payload["open_escalation"] = _serialize_escalation(open_escalation) if open_escalation else None
    if board_view:
        payload["status"] = _board_status(payload.get("status"))
    return payload


def _serialize_escalation(escalation: WorkEscalation | None):
    if not escalation:
        return None
    payload = escalation.to_dict()
    assignment = escalation.assignment
    if assignment:
        payload["assignment"] = {
            "id": assignment.id,
            "title": assignment.title,
            "status": assignment.status,
        }
    else:
        payload["assignment"] = None
    return payload


def _write_audit_log(user: User, query: str):
    db.session.add(
        AuditLog(
            user_id=user.id,
            username=user.username,
            role=user.role,
            query=query,
            ai_response="work_management",
            filtered_response=None,
            status="allowed",
            risk_score=0.0,
            risk_level="low",
            reason="work-management action",
            triggered_rules="[]",
            validator_notes="[]",
            is_high_risk=False,
        )
    )


@work_management_bp.route("/work/assignments", methods=["POST"])
@jwt_required()
def create_assignment():
    actor = _current_user()
    if not _is_admin_or_hr(actor):
        return jsonify({"error": "Admin/HR access required"}), 403

    data = request.get_json() or {}
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip() or None
    assigned_to_user_id = data.get("assigned_to_user_id")

    if not title:
        return jsonify({"error": "title is required"}), 400

    if not assigned_to_user_id:
        return jsonify({"error": "assigned_to_user_id is required"}), 400

    try:
        assigned_to_user_id = int(assigned_to_user_id)
        expected_units = float(data.get("expected_units", 0))
        weight = float(data.get("weight", 1))
    except (TypeError, ValueError):
        return jsonify({"error": "expected_units, weight, and assigned_to_user_id must be numeric"}), 400

    if expected_units <= 0:
        return jsonify({"error": "expected_units must be greater than 0"}), 400
    if weight < 0:
        return jsonify({"error": "weight must be 0 or greater"}), 400

    due_date = _parse_due_date(data.get("due_date"))
    if data.get("due_date") and not due_date:
        return jsonify({"error": "due_date must be in YYYY-MM-DD format"}), 400

    status = (data.get("status") or "pending").strip()
    if status not in ALLOWED_STATUSES:
        return jsonify({"error": "Invalid status"}), 400

    assignee = db.session.get(User, assigned_to_user_id)
    if not assignee or not assignee.is_active:
        return jsonify({"error": "Assigned user not found"}), 404

    assignment = WorkAssignment(
        title=title,
        description=description,
        assigned_by_user_id=actor.id,
        assigned_to_user_id=assignee.id,
        expected_units=expected_units,
        weight=weight,
        due_date=due_date,
        status=status,
    )
    assignment.sync_status_from_progress()

    db.session.add(assignment)
    _write_audit_log(actor, f"Created work assignment '{title}' for {assignee.username}")
    db.session.commit()

    return jsonify({
        "message": "Assignment created",
        "assignment": _serialize_assignment(assignment, include_progress=True),
    }), 201


@work_management_bp.route("/work/assignments", methods=["GET"])
@jwt_required()
def list_assignments():
    actor = _current_user()
    if not actor:
        return jsonify({"error": "User not found"}), 404

    query = (
        WorkAssignment.query
        .options(joinedload(WorkAssignment.progress_updates))
        .order_by(WorkAssignment.created_at.desc())
    )

    if not _is_admin_or_hr(actor):
        query = query.filter_by(assigned_to_user_id=actor.id)

    assignments = query.all()
    for assignment in assignments:
        assignment.sync_status_from_progress()
    db.session.commit()

    return jsonify({
        "assignments": [_serialize_assignment(item, include_progress=True) for item in assignments],
        "count": len(assignments),
    }), 200


@work_management_bp.route("/work/board", methods=["GET"])
@jwt_required()
def get_work_board():
    actor = _current_user()
    if not _is_admin_or_hr(actor):
        return jsonify({"error": "Admin/HR access required"}), 403

    assignments = (
        WorkAssignment.query
        .options(joinedload(WorkAssignment.progress_updates))
        .order_by(WorkAssignment.created_at.desc())
        .all()
    )
    for assignment in assignments:
        assignment.sync_status_from_progress()
    db.session.commit()

    return jsonify({
        "assignments": [_serialize_assignment(item, include_progress=True, board_view=True) for item in assignments],
        "columns": ["todo", "in_progress", "blocked", "completed"],
        "count": len(assignments),
    }), 200


@work_management_bp.route("/work/assignments/<int:assignment_id>/progress", methods=["POST"])
@jwt_required()
def submit_progress_update(assignment_id):
    actor = _current_user()
    if not actor:
        return jsonify({"error": "User not found"}), 404

    assignment = (
        WorkAssignment.query
        .options(joinedload(WorkAssignment.progress_updates))
        .filter_by(id=assignment_id)
        .first()
    )
    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    if assignment.assigned_to_user_id != actor.id:
        return jsonify({"error": "Only the assignee can submit progress"}), 403

    data = request.get_json() or {}
    try:
        completed_units = float(data.get("completed_units", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "completed_units must be numeric"}), 400

    if completed_units <= 0:
        return jsonify({"error": "completed_units must be greater than 0"}), 400

    note = (data.get("note") or "").strip() or None

    update = WorkProgressUpdate(
        assignment_id=assignment.id,
        reported_by_user_id=actor.id,
        completed_units=completed_units,
        note=note,
    )
    db.session.add(update)
    assignment.progress_updates.append(update)
    db.session.flush()

    assignment.sync_status_from_progress()
    _write_audit_log(actor, f"Submitted progress for assignment '{assignment.title}' ({completed_units} units)")
    db.session.commit()

    return jsonify({
        "message": "Progress update submitted",
        "progress_update": update.to_dict(),
        "assignment": _serialize_assignment(assignment, include_progress=True),
    }), 201


@work_management_bp.route("/work/assignments/<int:assignment_id>/status", methods=["PATCH"])
@jwt_required()
def update_assignment_status(assignment_id):
    actor = _current_user()
    if not _is_admin_or_hr(actor):
        return jsonify({"error": "Admin/HR access required"}), 403

    assignment = (
        WorkAssignment.query
        .options(joinedload(WorkAssignment.progress_updates))
        .filter_by(id=assignment_id)
        .first()
    )
    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    data = request.get_json() or {}
    status = (data.get("status") or "").strip()
    if status not in BOARD_ALLOWED_STATUSES:
        return jsonify({"error": "Invalid status"}), 400

    assignment.status = status
    assignment.sync_status_from_progress()
    _write_audit_log(actor, f"Updated assignment '{assignment.title}' status to {assignment.status}")
    db.session.commit()

    return jsonify({
        "message": "Assignment status updated",
        "assignment": _serialize_assignment(assignment, include_progress=True, board_view=True),
    }), 200


@work_management_bp.route("/work/escalations", methods=["POST"])
@jwt_required()
def create_work_escalation():
    actor = _current_user()
    if not _is_admin_or_hr(actor):
        return jsonify({"error": "Admin/HR access required"}), 403

    data = request.get_json() or {}
    assignment_id = data.get("assignment_id")
    if not assignment_id:
        return jsonify({"error": "assignment_id is required"}), 400

    try:
        assignment_id = int(assignment_id)
    except (TypeError, ValueError):
        return jsonify({"error": "assignment_id must be numeric"}), 400

    assignment = db.session.get(WorkAssignment, assignment_id)
    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    existing_open = (
        WorkEscalation.query
        .filter_by(assignment_id=assignment.id, status="open")
        .order_by(WorkEscalation.created_at.desc())
        .first()
    )
    if existing_open:
        return jsonify({"error": "An open escalation already exists for this assignment"}), 400

    escalation = WorkEscalation(
        assignment_id=assignment.id,
        created_by_user_id=actor.id,
        reason=(data.get("reason") or data.get("note") or "").strip() or None,
        status="open",
    )
    db.session.add(escalation)
    _write_audit_log(actor, f"Escalated assignment '{assignment.title}'")
    db.session.commit()

    return jsonify({
        "message": "Escalation created",
        "escalation": _serialize_escalation(escalation),
    }), 201


@work_management_bp.route("/work/escalations", methods=["GET"])
@jwt_required()
def list_work_escalations():
    actor = _current_user()
    if not _is_admin_or_hr(actor):
        return jsonify({"error": "Admin/HR access required"}), 403

    escalations = (
        WorkEscalation.query
        .options(joinedload(WorkEscalation.assignment))
        .order_by(WorkEscalation.created_at.desc())
        .all()
    )

    return jsonify({
        "escalations": [_serialize_escalation(item) for item in escalations],
        "count": len(escalations),
    }), 200


@work_management_bp.route("/work/escalations/<int:escalation_id>", methods=["PATCH"])
@jwt_required()
def update_work_escalation(escalation_id):
    actor = _current_user()
    if not _is_admin_or_hr(actor):
        return jsonify({"error": "Admin/HR access required"}), 403

    escalation = (
        WorkEscalation.query
        .options(joinedload(WorkEscalation.assignment))
        .filter_by(id=escalation_id)
        .first()
    )
    if not escalation:
        return jsonify({"error": "Escalation not found"}), 404

    status = (request.get_json() or {}).get("status", "").strip()
    if status != "resolved":
        return jsonify({"error": "Only resolution to 'resolved' is supported"}), 400
    if escalation.status == "resolved":
        return jsonify({"error": "Escalation is already resolved"}), 400

    escalation.status = "resolved"
    _write_audit_log(actor, f"Resolved escalation for assignment '{escalation.assignment.title if escalation.assignment else escalation.assignment_id}'")
    db.session.commit()

    return jsonify({
        "message": "Escalation updated",
        "escalation": _serialize_escalation(escalation),
    }), 200


@work_management_bp.route("/work/assignments/<int:assignment_id>/kpi", methods=["GET"])
@jwt_required()
def get_assignment_kpi(assignment_id):
    actor = _current_user()
    if not actor:
        return jsonify({"error": "User not found"}), 404

    assignment = (
        WorkAssignment.query
        .options(joinedload(WorkAssignment.progress_updates))
        .filter_by(id=assignment_id)
        .first()
    )
    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    if not _is_admin_or_hr(actor) and assignment.assigned_to_user_id != actor.id:
        return jsonify({"error": "Access denied"}), 403

    assignment.sync_status_from_progress()
    db.session.commit()

    return jsonify({
        "assignment_id": assignment.id,
        "status": assignment.status,
        "kpi": _compute_kpi(assignment),
        "capacity_risk": _compute_capacity_risk(assignment),
    }), 200
