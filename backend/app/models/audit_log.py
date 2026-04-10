from datetime import UTC, datetime

from app import db


class _AuditLogMessageAccessor:
    def __get__(self, instance, owner):
        if instance is None:
            return db.session.query(owner)
        return instance.query_text

    def __set__(self, instance, value):
        instance.query_text = value


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    username         = db.Column(db.String(80), nullable=False)
    role             = db.Column(db.String(20), nullable=False)
    query_text       = db.Column("query", db.Text, nullable=False)
    ai_response      = db.Column(db.Text, nullable=True)
    filtered_response= db.Column(db.Text, nullable=True)
    status           = db.Column(db.String(20), nullable=False)   # allowed / filtered / blocked
    risk_score       = db.Column(db.Float, default=0.0)

    # v2 additions ─────────────────────────────────────────────────────────
    risk_level       = db.Column(db.String(10), default="low")    # low / medium / high
    reason           = db.Column(db.Text, nullable=True)          # explainability text
    triggered_rules  = db.Column(db.Text, nullable=True)          # JSON list of matched rules
    validator_notes  = db.Column(db.Text, nullable=True)          # JSON list from layer-2
    is_high_risk     = db.Column(db.Boolean, default=False)       # alert flag
    # ───────────────────────────────────────────────────────────────────────

    timestamp        = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    query            = _AuditLogMessageAccessor()

    def to_dict(self):
        import json
        def _parse(val):
            if not val:
                return []
            try:
                return json.loads(val)
            except Exception:
                return [val]

        return {
            "id":               self.id,
            "user_id":          self.user_id,
            "username":         self.username,
            "role":             self.role,
            "query":            self.query,
            "ai_response":      self.ai_response,
            "filtered_response":self.filtered_response,
            "status":           self.status,
            "risk_score":       self.risk_score,
            "risk_level":       self.risk_level,
            "reason":           self.reason,
            "triggered_rules":  _parse(self.triggered_rules),
            "validator_notes":  _parse(self.validator_notes),
            "is_high_risk":     self.is_high_risk,
            "timestamp":        self.timestamp.isoformat(),
        }
