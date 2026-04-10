from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_socketio import SocketIO
from dotenv import load_dotenv
import os
from importlib import import_module

load_dotenv()

db = SQLAlchemy()
jwt = JWTManager()
socketio = SocketIO()


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
    from app.routes.chat import chat_bp
    from app.routes.logs import logs_bp
    from app.routes.users import users_bp
    from app.routes.messages import messages_bp
    from app.routes.attendance import attendance_bp
    from ghost_routes import ghost_bp
    from attack_routes import attack_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(chat_bp, url_prefix="/api")
    app.register_blueprint(logs_bp, url_prefix="/api")
    app.register_blueprint(users_bp, url_prefix="/api")
    app.register_blueprint(messages_bp, url_prefix="/api")
    app.register_blueprint(attendance_bp, url_prefix="/api")
    app.register_blueprint(ghost_bp, url_prefix="/api")
    app.register_blueprint(attack_bp, url_prefix="/api")
    # Socket events
    from app.routes import socket_events  # noqa
    import_module("app.models")

    with app.app_context():
        db.create_all()
        _seed_demo_users()

    return app


def _seed_demo_users():
    from app.models.user import User
    from werkzeug.security import generate_password_hash

    demo_users = [
        {"username": "admin", "email": "admin@secureai.com", "password": "admin123", "role": "admin"},
        {"username": "hr_jane", "email": "hr@secureai.com", "password": "hr123", "role": "hr"},
        {"username": "intern_bob", "email": "intern@secureai.com", "password": "intern123", "role": "intern"},
    ]
    for u in demo_users:
        if not User.query.filter_by(username=u["username"]).first():
            user = User(
                username=u["username"],
                email=u["email"],
                password_hash=generate_password_hash(u["password"]),
                role=u["role"],
            )
            db.session.add(user)
    db.session.commit()
