"""Scheduled session model for tracking student scheduling requests."""

from datetime import datetime
from models import db


class ScheduledSession(db.Model):
    """Tracks when students initiate scheduling with an instructor."""

    __tablename__ = 'scheduled_sessions'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    eligibility_reason = db.Column(db.String(50))  # 'needs_work_feedback' or 'digi_trainer_engagement'
    goals_passed = db.Column(db.Integer, default=0)
    goals_engaged = db.Column(db.Integer, default=0)
    total_goals = db.Column(db.Integer, default=0)
    scheduled_at = db.Column(db.DateTime, default=datetime.utcnow)
    session_completed_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)

    submission = db.relationship('Submission', backref=db.backref('scheduled_sessions', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('scheduled_sessions', lazy='dynamic'))

    def engagement_percent(self):
        if self.total_goals == 0:
            return 0
        return round((self.goals_engaged + self.goals_passed) / self.total_goals * 100)
