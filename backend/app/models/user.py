from app import db
from datetime import datetime


class User(db.Model):
    __tablename__ = "users"

    id                   = db.Column(db.Integer, primary_key=True)
    username             = db.Column(db.String(80), unique=True, nullable=False)
    email                = db.Column(db.String(120), unique=True, nullable=False)
    password_hash        = db.Column(db.String(256), nullable=False)
    role                 = db.Column(db.String(20), nullable=False, default="intern")
    created_at           = db.Column(db.DateTime, default=datetime.utcnow)
    is_active            = db.Column(db.Boolean, default=True)

    # v2: suspicious-user tracking ─────────────────────────────────────────
    sensitive_query_count = db.Column(db.Integer, default=0)   # cumulative sensitive queries
    is_suspicious         = db.Column(db.Boolean, default=False)
    flagged_at            = db.Column(db.DateTime, nullable=True)
    # ───────────────────────────────────────────────────────────────────────

    def to_dict(self):
        return {
            "id":                   self.id,
            "username":             self.username,
            "email":                self.email,
            "role":                 self.role,
            "created_at":           self.created_at.isoformat(),
            "is_active":            self.is_active,
            "sensitive_query_count":self.sensitive_query_count,
            "is_suspicious":        self.is_suspicious,
            "flagged_at":           self.flagged_at.isoformat() if self.flagged_at else None,
        }
