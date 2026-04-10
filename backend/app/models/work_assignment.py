from datetime import UTC, date, datetime

from app import db
from sqlalchemy.types import String, TypeDecorator


class FlexibleDate(TypeDecorator):
    impl = String(32)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value in (None, ""):
            return None
        if isinstance(value, datetime):
            return value.date().isoformat()
        if isinstance(value, date):
            return value.isoformat()
        return str(value)

    def process_result_value(self, value, dialect):
        return value


class WorkAssignment(db.Model):
    __tablename__ = "work_assignments"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    assigned_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    assigned_to_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    expected_units = db.Column(db.Float, nullable=False, default=0)
    weight = db.Column(db.Float, nullable=False, default=1.0)
    due_date = db.Column(FlexibleDate(), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="pending")
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    progress_updates = db.relationship(
        "WorkProgressUpdate",
        backref="assignment",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="WorkProgressUpdate.created_at.desc()",
    )

    def total_completed_units(self):
        return float(sum(update.completed_units or 0 for update in self.progress_updates))

    def normalized_due_date(self):
        if self.due_date in (None, ""):
            return None
        if isinstance(self.due_date, datetime):
            return self.due_date.date()
        if isinstance(self.due_date, date):
            return self.due_date
        if isinstance(self.due_date, str):
            try:
                return date.fromisoformat(self.due_date[:10])
            except ValueError:
                return None
        return None

    def compute_kpi(self):
        expected_units = float(self.expected_units or 0)
        total_completed_units = self.total_completed_units()
        completion_ratio = (total_completed_units / expected_units) if expected_units > 0 else 0.0
        weighted_score = min(completion_ratio, 1.0) * float(self.weight or 0)
        return {
            "expected_units": round(expected_units, 4),
            "total_completed_units": round(total_completed_units, 4),
            "completion_ratio": round(completion_ratio, 4),
            "weighted_score": round(weighted_score, 4),
        }

    def sync_status_from_progress(self):
        total_completed_units = self.total_completed_units()
        expected_units = float(self.expected_units or 0)

        if expected_units > 0 and total_completed_units >= expected_units:
            self.status = "completed"
        elif self.status == "blocked":
            return
        elif total_completed_units > 0:
            self.status = "in_progress"
        elif self.status == "todo":
            return
        else:
            self.status = "pending"

    def to_dict(self, include_progress=False):
        due_date = self.normalized_due_date()
        payload = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "assigned_by_user_id": self.assigned_by_user_id,
            "assigned_to_user_id": self.assigned_to_user_id,
            "expected_units": float(self.expected_units or 0),
            "weight": float(self.weight or 0),
            "due_date": due_date.isoformat() if due_date else None,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "kpi": self.compute_kpi(),
        }
        if include_progress:
            payload["progress_updates"] = [update.to_dict() for update in self.progress_updates]
        return payload
