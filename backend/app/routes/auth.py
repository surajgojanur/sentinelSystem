from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models.user import User
from app.services.face_attendance import match_face

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    return jsonify({"error": "Public registration is disabled. Contact an admin to create your account."}), 403


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    login_code = data.get("login_code", "").strip()

    if not username or not login_code:
        return jsonify({"error": "Username and login code are required"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or user.login_code != login_code:
        return jsonify({"error": "Invalid username or login code"}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict()}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": user.to_dict()}), 200


@auth_bp.route("/face-verify", methods=["POST"])
@jwt_required()
def face_verify():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json() or {}
    image_payload = data.get("image_base64", "").strip()
    if not image_payload:
        return jsonify({"error": "image_base64 is required"}), 400

    try:
        profile, score = match_face(image_payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    if not profile:
        return jsonify({
            "error": "Face not recognized. Register your face in Attendance first.",
            "confidence": round(float(score), 4),
        }), 403

    if profile.user_id != user.id:
        return jsonify({
            "error": "Face does not match the logged in account.",
            "confidence": round(float(score), 4),
        }), 403

    return jsonify({
        "verified": True,
        "confidence": round(float(score), 4),
        "user": user.to_dict(),
    }), 200
