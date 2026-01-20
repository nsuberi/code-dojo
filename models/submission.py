"""Submission model."""

from datetime import datetime
from models import db


class Submission(db.Model):
    """A student's code submission for a learning goal."""

    __tablename__ = 'submissions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    goal_id = db.Column(db.Integer, db.ForeignKey('learning_goals.id'), nullable=False)
    pr_url = db.Column(db.String(500), nullable=False)
    pr_number = db.Column(db.Integer)  # Extracted from URL for easy reference
    pr_title = db.Column(db.String(500))  # Cached for display
    pr_state = db.Column(db.String(20))  # open, closed, merged
    pr_base_sha = db.Column(db.String(40))  # Base commit SHA
    pr_head_sha = db.Column(db.String(40))  # Head commit SHA
    status = db.Column(db.String(50), default='pending')  # pending, ai_complete, feedback_requested, reviewed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    ai_feedback = db.relationship('AIFeedback', backref='submission', uselist=False)
    instructor_feedback = db.relationship('InstructorFeedback', backref='submission', uselist=False)
    arch_analysis = db.relationship('ArchitecturalAnalysis', backref='submission', uselist=False)

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'goal_id': self.goal_id,
            'pr_url': self.pr_url,
            'pr_number': self.pr_number,
            'pr_title': self.pr_title,
            'pr_state': self.pr_state,
            'pr_base_sha': self.pr_base_sha,
            'pr_head_sha': self.pr_head_sha,
            'status': self.status,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
            'ai_feedback': self.ai_feedback.to_dict() if self.ai_feedback else None,
            'instructor_feedback': self.instructor_feedback.to_dict() if self.instructor_feedback else None,
        }

    def __repr__(self):
        return f'<Submission {self.id} by User {self.user_id}>'
