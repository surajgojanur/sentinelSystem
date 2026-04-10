from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_socketio import SocketIO
from dotenv import load_dotenv
from sqlalchemy import inspect, text
import os
import secrets
import string
from importlib import import_module

load_dotenv()

db = SQLAlchemy()
jwt = JWTManager()
socketio = SocketIO()
_LOGIN_CODE_ALPHABET = string.ascii_uppercase + string.digits


def create_app():
    app = Flask(__name__)

    # Config
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///secureai.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False  # No expiry for demo

    # Extensions
    db.init_app(app)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
    socketio.init_app(
        app,
        cors_allowed_origins="*",
        async_mode="eventlet",
        logger=False,
        engineio_logger=False,
    )

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.chat import chat_bp
    from app.routes.logs import logs_bp
    from app.routes.users import users_bp
    from app.routes.messages import messages_bp
    from app.routes.attendance import attendance_bp
    from app.routes.work_management import work_management_bp
    from app.routes.roles import roles_bp
    from app.routes.work_management import work_management_bp
    from ghost_routes import ghost_bp
    from attack_routes import attack_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(admin_bp, url_prefix="/api")
    app.register_blueprint(chat_bp, url_prefix="/api")
    app.register_blueprint(logs_bp, url_prefix="/api")
    app.register_blueprint(users_bp, url_prefix="/api")
    app.register_blueprint(messages_bp, url_prefix="/api")
    app.register_blueprint(attendance_bp, url_prefix="/api")
    app.register_blueprint(work_management_bp, url_prefix="/api")
    app.register_blueprint(roles_bp, url_prefix="/api")
    app.register_blueprint(work_management_bp, url_prefix="/api")
    app.register_blueprint(ghost_bp, url_prefix="/api")
    app.register_blueprint(attack_bp, url_prefix="/api")
    # Socket events
    from app.routes import socket_events  # noqa
    import_module("app.models")

    with app.app_context():
        db.create_all()
        _ensure_work_escalation_columns()
        _ensure_user_schema()
        _seed_roles()
        _seed_demo_users()
        _sync_users_to_roles()
        _ensure_user_login_codes()

    return app


def _normalize_role_name(value: str) -> str:
    normalized = (value or "").strip().lower()
    if normalized == "hr":
        return "HR"
    return normalized.title()


def _generate_login_code(length: int = 10) -> str:
    from app.models.user import User

    while True:
        candidate = ''.join(secrets.choice(_LOGIN_CODE_ALPHABET) for _ in range(length))
        if not User.query.filter_by(login_code=candidate).first():
            return candidate


def _ensure_user_schema():
    inspector = inspect(db.engine)
    columns = {column["name"] for column in inspector.get_columns("users")}
    if "role_id" not in columns:
        db.session.execute(text("ALTER TABLE users ADD COLUMN role_id INTEGER"))
        db.session.commit()
    if "login_code" not in columns:
        db.session.execute(text("ALTER TABLE users ADD COLUMN login_code VARCHAR(32)"))
        db.session.commit()


def _seed_roles():
    from app.models.role import Role

    role_names = [
        "Admin",
        "HR",
        "Intern",
        "Developer",
        "Manager",
        "Team Lead",
        "Finance",
        "Analyst",
        "Security",
    ]
    existing = {role.name for role in Role.query.all()}
    for name in role_names:
        if name not in existing:
            db.session.add(Role(name=name))
    db.session.commit()


def _seed_demo_users():
    from app.models.role import Role
    from app.models.user import User
    from werkzeug.security import generate_password_hash

    demo_users = [
        {"username": "admin", "email": "admin@secureai.com", "password": "admin123", "role": "admin", "login_code": "ADMINCODE1"},
        {"username": "hr_jane", "email": "hr@secureai.com", "password": "hr123", "role": "hr", "login_code": "HRCODE0001"},
        {"username": "intern_bob", "email": "intern@secureai.com", "password": "intern123", "role": "intern", "login_code": "INTCODE001"},
    ]
    for u in demo_users:
        existing_user = User.query.filter_by(username=u["username"]).first()
        role = Role.query.filter_by(name=_normalize_role_name(u["role"])).first()
        if not existing_user:
            user = User(
                username=u["username"],
                email=u["email"],
                password_hash=generate_password_hash(u["password"]),
                role=u["role"],
                role_id=role.id if role else None,
                login_code=u["login_code"],
            )
            db.session.add(user)
        elif not existing_user.login_code:
            existing_user.login_code = u["login_code"]
            if role and not existing_user.role_id:
                existing_user.role_id = role.id
    db.session.commit()


def _ensure_work_escalation_columns():
    inspector = inspect(db.engine)
    if not inspector.has_table("work_escalations"):
        return

    columns = {column["name"] for column in inspector.get_columns("work_escalations")}
    if "status" not in columns:
        db.session.execute(text("ALTER TABLE work_escalations ADD COLUMN status VARCHAR(20) DEFAULT 'open'"))
        db.session.execute(text("UPDATE work_escalations SET status = 'open' WHERE status IS NULL"))
        db.session.commit()


def _sync_users_to_roles():
    from app.models.role import Role
    from app.models.user import User

    role_map = {role.name.lower(): role.id for role in Role.query.all()}
    users = User.query.all()
    changed = False
    for user in users:
        normalized_role = (user.role or "").strip().lower() or "intern"
        desired_role_id = role_map.get(normalized_role)
        if user.role != normalized_role:
            user.role = normalized_role
            changed = True
        if desired_role_id and user.role_id != desired_role_id:
            user.role_id = desired_role_id
            changed = True
    if changed:
        db.session.commit()


def _ensure_user_login_codes():
    from app.models.user import User

    changed = False
    for user in User.query.all():
        if not user.login_code:
            user.login_code = _generate_login_code()
            changed = True
    if changed:
        db.session.commit()
