from datetime import datetime

from app import db


class WorkAssignment(db.Model):
    __tablename__ = "work_assignments"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    assigned_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    assigned_to_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    expected_units = db.Column(db.Float, nullable=False, default=0)
    weight = db.Column(db.Float, nullable=False, default=1.0)
    due_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="pending")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    progress_updates = db.relationship(
        "WorkProgressUpdate",
        backref="assignment",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="WorkProgressUpdate.created_at.desc()",
    )

    def total_completed_units(self):
        return float(sum(update.completed_units or 0 for update in self.progress_updates))

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
        elif total_completed_units > 0:
            self.status = "in_progress"
        else:
            self.status = "pending"

    def to_dict(self, include_progress=False):
        payload = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "assigned_by_user_id": self.assigned_by_user_id,
            "assigned_to_user_id": self.assigned_to_user_id,
            "expected_units": float(self.expected_units or 0),
            "weight": float(self.weight or 0),
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "kpi": self.compute_kpi(),
        }
        if include_progress:
            payload["progress_updates"] = [update.to_dict() for update in self.progress_updates]
        return payload
