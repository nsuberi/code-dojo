"""AI feedback model."""

from datetime import datetime
from models import db


class AIFeedback(db.Model):
    """AI-generated feedback for a submission."""

    __tablename__ = 'ai_feedbacks'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False, unique=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'submission_id': self.submission_id,
            'content': self.content,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
        }

    def __repr__(self):
        return f'<AIFeedback for Submission {self.submission_id}>'
