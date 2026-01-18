"""Instructor feedback model."""

from datetime import datetime
from models import db


class InstructorFeedback(db.Model):
    """Instructor's feedback and pass/fail decision for a submission."""

    __tablename__ = 'instructor_feedbacks'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False, unique=True)
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    comment = db.Column(db.Text)
    passed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'submission_id': self.submission_id,
            'instructor_id': self.instructor_id,
            'comment': self.comment,
            'passed': self.passed,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
        }

    def __repr__(self):
        return f'<InstructorFeedback for Submission {self.submission_id}>'
