from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models.user import User
from app.services.face_attendance import match_face

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")
    role = data.get("role", "intern")

    if not username or not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    if role not in ("admin", "hr", "intern"):
        role = "intern"

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already taken"}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        role=role,
    )
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict()}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "")

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict()}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": user.to_dict()}), 200


@auth_bp.route("/face-verify", methods=["POST"])
@jwt_required()
def face_verify():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
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
