"""Submission model."""

from datetime import datetime
from models import db


class Submission(db.Model):
    """A student's code submission for a learning goal."""

    __tablename__ = 'submissions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    goal_id = db.Column(db.Integer, db.ForeignKey('learning_goals.id'), nullable=False)
    repo_url = db.Column(db.String(500), nullable=False)
    branch = db.Column(db.String(100), default='main')
    status = db.Column(db.String(50), default='pending')  # pending, ai_complete, feedback_requested, reviewed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    ai_feedback = db.relationship('AIFeedback', backref='submission', uselist=False)
    instructor_feedback = db.relationship('InstructorFeedback', backref='submission', uselist=False)

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'goal_id': self.goal_id,
            'repo_url': self.repo_url,
            'branch': self.branch,
            'status': self.status,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
            'ai_feedback': self.ai_feedback.to_dict() if self.ai_feedback else None,
            'instructor_feedback': self.instructor_feedback.to_dict() if self.instructor_feedback else None,
        }

    def __repr__(self):
        return f'<Submission {self.id} by User {self.user_id}>'
