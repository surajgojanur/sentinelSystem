import csv
import io
import json
from datetime import datetime

from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models.audit_log import AuditLog
from app.models.favorite_question import FavoriteQuestion
from app.models.question_feedback import QuestionFeedback
from app.models.user import User
from app.services.ai_service import (
    add_mock_question,
    capture_unanswered_question,
    delete_mock_question,
    extract_questions_from_uploaded_file,
    export_mock_questions_csv,
    find_question_match_for_query,
    get_ai_response,
    get_question,
    get_suggested_questions,
    import_mock_questions,
    list_mock_questions,
    search_mock_questions,
    list_question_history,
    list_unanswered_questions,
    resolve_contextual_query,
    resolve_unanswered_question,
    serialize_question,
    update_mock_question,
)
from app.services.governance import (
    SUSPICIOUS_QUERY_THRESHOLD,
    apply_governance,
    compute_query_sensitivity,
)

chat_bp = Blueprint("chat", __name__)

_histories: dict = {}


def _get_user() -> User | None:
    user_id = int(get_jwt_identity())
    return User.query.get(user_id)


def _require_admin() -> User | None:
    user = _get_user()
    return user if user and user.role == "admin" else None


@chat_bp.route("/chat", methods=["POST"])
@jwt_required()
def chat():
    user = _get_user()
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json() or {}
    query = data.get("message", "").strip()
    if not query:
        return jsonify({"error": "Message is required"}), 400

    user_id = user.id
    if user_id not in _histories:
        _histories[user_id] = []
    _histories[user_id].append({"role": "user", "content": query})
    contextual_query = resolve_contextual_query(_histories[user_id])

    raw_response = get_ai_response(_histories[user_id])
    result = apply_governance(raw_response, query, user.role)
    matched_question = find_question_match_for_query(contextual_query or query, user.role)
    if not matched_question:
        capture_unanswered_question(contextual_query or query, user.role, user.username)

    _histories[user_id].append({"role": "assistant", "content": raw_response})
    if len(_histories[user_id]) > 20:
        _histories[user_id] = _histories[user_id][-20:]

    if compute_query_sensitivity(query):
        user.sensitive_query_count = (user.sensitive_query_count or 0) + 1
        if user.sensitive_query_count >= SUSPICIOUS_QUERY_THRESHOLD and not user.is_suspicious:
            user.is_suspicious = True
            user.flagged_at = datetime.utcnow()

    log = AuditLog(
        user_id=user.id,
        username=user.username,
        role=user.role,
        query=query,
        ai_response=raw_response,
        filtered_response=result.filtered_response,
        status=result.status,
        risk_score=result.risk_score,
        risk_level=result.risk_level,
        reason=result.reason,
        triggered_rules=json.dumps(result.triggered_rules),
        validator_notes=json.dumps(result.validator_notes),
        is_high_risk=result.is_high_risk_alert,
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({
        "log_id": log.id,
        "response": result.filtered_response,
        "status": result.status,
        "risk_score": result.risk_score,
        "risk_level": result.risk_level,
        "reason": result.reason,
        "triggered_rules": result.triggered_rules,
        "validator_notes": result.validator_notes,
        "is_high_risk": result.is_high_risk_alert,
        "role": user.role,
        "matched_question": serialize_question(matched_question) if matched_question else None,
        "suggested_questions": get_suggested_questions(contextual_query or query, user.role),
    }), 200


@chat_bp.route("/chat/clear", methods=["POST"])
@jwt_required()
def clear_history():
    user = _get_user()
    if not user:
        return jsonify({"error": "User not found"}), 404
    _histories.pop(user.id, None)
    return jsonify({"message": "Chat history cleared"}), 200


@chat_bp.route("/chat/questions", methods=["GET"])
@jwt_required()
def get_question_bank():
    user = _get_user()
    if not user:
        return jsonify({"error": "User not found"}), 404

    favorites = FavoriteQuestion.query.filter_by(user_id=user.id).all()
    favorite_ids = {item.question_id for item in favorites}
    questions = []
    for item in list_mock_questions(user.role):
        if user.role == "admin":
            full_question = get_question(item["id"])
            if full_question:
                item["answer"] = full_question["answer"]
        item["is_favorite"] = item["id"] in favorite_ids
        questions.append(item)
    return jsonify({"questions": questions}), 200


@chat_bp.route("/chat/questions/search", methods=["GET"])
@jwt_required()
def search_question_bank():
    user = _get_user()
    if not user:
        return jsonify({"error": "User not found"}), 404

    query = request.args.get("q", "").strip()
    limit = request.args.get("limit", default=25, type=int) or 25
    favorites = FavoriteQuestion.query.filter_by(user_id=user.id).all()
    favorite_ids = {item.question_id for item in favorites}

    questions = []
    for item in search_mock_questions(query, user.role, limit=min(max(limit, 1), 100)):
        if user.role == "admin":
            full_question = get_question(item["id"])
            if full_question:
                item["answer"] = full_question["answer"]
        item["is_favorite"] = item["id"] in favorite_ids
        questions.append(item)
    return jsonify({"questions": questions, "query": query}), 200


@chat_bp.route("/chat/questions", methods=["POST"])
@jwt_required()
def create_question():
    admin = _require_admin()
    if not admin:
        return jsonify({"error": "Only admins can add dataset questions"}), 403

    data = request.get_json() or {}
    try:
        entry = add_mock_question(
            data.get("question", ""),
            data.get("answer", ""),
            data.get("category", "General"),
            data.get("keywords", []),
            data.get("allowed_roles", []),
            actor=admin.username,
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify({"question": entry}), 201


@chat_bp.route("/chat/questions/<question_id>", methods=["PUT"])
@jwt_required()
def edit_question(question_id):
    admin = _require_admin()
    if not admin:
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json() or {}
    try:
        entry = update_mock_question(
            question_id,
            question=data.get("question", ""),
            answer=data.get("answer", ""),
            category=data.get("category", "General"),
            keywords=data.get("keywords", []),
            allowed_roles=data.get("allowed_roles", []),
            actor=admin.username,
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify({"question": entry}), 200


@chat_bp.route("/chat/questions/<question_id>", methods=["DELETE"])
@jwt_required()
def remove_question(question_id):
    admin = _require_admin()
    if not admin:
        return jsonify({"error": "Admin access required"}), 403

    try:
        delete_mock_question(question_id, actor=admin.username)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404
    return jsonify({"message": "Question deleted"}), 200


@chat_bp.route("/chat/questions/import", methods=["POST"])
@jwt_required()
def import_questions():
    admin = _require_admin()
    if not admin:
        return jsonify({"error": "Admin access required"}), 403

    try:
        if "file" in request.files:
            file_obj = request.files["file"]
            if not file_obj or not file_obj.filename:
                return jsonify({"error": "Please choose a .json or .pdf file to import"}), 400
            entries, metadata = extract_questions_from_uploaded_file(file_obj.filename, file_obj.read())
            result = import_mock_questions(entries, actor=admin.username)
            result["metadata"] = metadata
        else:
            data = request.get_json() or {}
            result = import_mock_questions(data.get("questions", []), actor=admin.username)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(result), 201


@chat_bp.route("/chat/questions/export", methods=["GET"])
@jwt_required()
def export_questions():
    user = _get_user()
    if not user:
        return jsonify({"error": "User not found"}), 404

    export_format = request.args.get("format", "json")
    questions = list_mock_questions(user.role)
    if export_format == "csv":
        csv_data = export_mock_questions_csv(user.role)
        response = make_response(csv_data)
        response.headers["Content-Type"] = "text/csv; charset=utf-8"
        response.headers["Content-Disposition"] = "attachment; filename=secureai-question-bank.csv"
        return response
    return jsonify({"questions": questions}), 200


@chat_bp.route("/chat/questions/history", methods=["GET"])
@jwt_required()
def question_history():
    admin = _require_admin()
    if not admin:
        return jsonify({"error": "Admin access required"}), 403
    return jsonify({"history": list_question_history()}), 200


@chat_bp.route("/chat/questions/review-queue", methods=["GET"])
@jwt_required()
def review_queue():
    admin = _require_admin()
    if not admin:
        return jsonify({"error": "Admin access required"}), 403
    return jsonify({"items": list_unanswered_questions(request.args.get("status"))}), 200


@chat_bp.route("/chat/questions/review-queue/<queue_id>", methods=["PATCH"])
@jwt_required()
def resolve_queue_item(queue_id):
    admin = _require_admin()
    if not admin:
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json() or {}
    try:
        item = resolve_unanswered_question(
            queue_id,
            data.get("status", "resolved"),
            data.get("resolution_note", ""),
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"item": item}), 200


@chat_bp.route("/chat/favorites", methods=["GET"])
@jwt_required()
def get_favorites():
    user = _get_user()
    if not user:
        return jsonify({"error": "User not found"}), 404

    favorites = FavoriteQuestion.query.filter_by(user_id=user.id).order_by(FavoriteQuestion.created_at.desc()).all()
    items = []
    for favorite in favorites:
        question = get_question(favorite.question_id)
        if question and user.role in question["allowed_roles"]:
            data = serialize_question(question)
            data["is_favorite"] = True
            items.append(data)
    return jsonify({"favorites": items}), 200


@chat_bp.route("/chat/favorites/<question_id>", methods=["POST"])
@jwt_required()
def add_favorite(question_id):
    user = _get_user()
    if not user:
        return jsonify({"error": "User not found"}), 404

    question = get_question(question_id)
    if not question or user.role not in question["allowed_roles"]:
        return jsonify({"error": "Question not available"}), 404

    favorite = FavoriteQuestion.query.filter_by(user_id=user.id, question_id=question_id).first()
    if not favorite:
        favorite = FavoriteQuestion(user_id=user.id, question_id=question_id)
        db.session.add(favorite)
        db.session.commit()
    return jsonify({"favorite": serialize_question(question)}), 201


@chat_bp.route("/chat/favorites/<question_id>", methods=["DELETE"])
@jwt_required()
def remove_favorite(question_id):
    user = _get_user()
    if not user:
        return jsonify({"error": "User not found"}), 404

    favorite = FavoriteQuestion.query.filter_by(user_id=user.id, question_id=question_id).first()
    if favorite:
        db.session.delete(favorite)
        db.session.commit()
    return jsonify({"message": "Favorite removed"}), 200


@chat_bp.route("/chat/feedback", methods=["POST"])
@jwt_required()
def submit_feedback():
    user = _get_user()
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json() or {}
    log_id = data.get("log_id")
    value = data.get("value", "").strip().lower()
    note = data.get("note", "").strip()
    if value not in {"helpful", "unhelpful"}:
        return jsonify({"error": "Feedback value must be helpful or unhelpful"}), 400

    log = db.session.get(AuditLog, log_id)
    if not log or log.user_id != user.id:
        return jsonify({"error": "Audit log not found"}), 404

    existing = QuestionFeedback.query.filter_by(audit_log_id=log.id, user_id=user.id).first()
    if existing:
        existing.value = value
        existing.note = note
        db.session.commit()
        return jsonify({"feedback": existing.to_dict()}), 200

    feedback = QuestionFeedback(audit_log_id=log.id, user_id=user.id, value=value, note=note)
    db.session.add(feedback)
    db.session.commit()
    return jsonify({"feedback": feedback.to_dict()}), 201


@chat_bp.route("/chat/export", methods=["GET"])
@jwt_required()
def export_conversation():
    user = _get_user()
    if not user:
        return jsonify({"error": "User not found"}), 404

    logs = (
        db.session.query(AuditLog)
        .filter_by(user_id=user.id)
        .order_by(AuditLog.timestamp.desc())
        .all()
    )
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=[
        "timestamp", "username", "role", "query", "response", "status", "risk_level", "risk_score",
    ])
    writer.writeheader()
    for log in logs:
        writer.writerow({
            "timestamp": log.timestamp.isoformat(),
            "username": log.username,
            "role": log.role,
            "query": log.query,
            "response": log.filtered_response or log.ai_response or "",
            "status": log.status,
            "risk_level": log.risk_level,
            "risk_score": log.risk_score,
        })

    response = make_response(buffer.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = "attachment; filename=secureai-conversation-export.csv"
    return response
