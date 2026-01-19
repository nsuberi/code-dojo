"""Sensei evaluation model for post-session assessment."""

import json
from datetime import datetime
from models import db


class SenseiEvaluation(db.Model):
    """Captures a Sensei's evaluation of a student after a session."""

    __tablename__ = 'sensei_evaluations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sensei_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'))
    session_date = db.Column(db.DateTime, default=datetime.utcnow)

    # Sensei's assessment
    journey_stage = db.Column(db.String(50))  # 'beginning', 'developing', 'proficient', 'mastery'
    session_notes = db.Column(db.Text)  # Private notes from the session

    # Concepts the student is still working to embody
    concepts_in_progress_json = db.Column(db.Text)  # ["decorator patterns", "error handling"]

    # Recommended next steps
    recommended_challenges_json = db.Column(db.Text)  # [goal_id, goal_id, ...]
    custom_exercises_json = db.Column(db.Text)  # Free-form suggestions

    # Certification (if applicable)
    certification_granted = db.Column(db.Boolean, default=False)
    certification_level = db.Column(db.String(50))  # 'bronze', 'silver', 'gold'

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student = db.relationship('User', foreign_keys=[user_id], backref='sensei_evaluations_received')
    sensei = db.relationship('User', foreign_keys=[sensei_id], backref='sensei_evaluations_given')
    submission = db.relationship('Submission', backref='sensei_evaluation')

    def get_concepts_in_progress(self):
        """Parse and return concepts in progress."""
        return json.loads(self.concepts_in_progress_json) if self.concepts_in_progress_json else []

    def set_concepts_in_progress(self, concepts_list):
        """Set concepts in progress from a list."""
        self.concepts_in_progress_json = json.dumps(concepts_list)

    def get_recommended_challenges(self):
        """Parse and return recommended challenge IDs."""
        return json.loads(self.recommended_challenges_json) if self.recommended_challenges_json else []

    def set_recommended_challenges(self, challenge_ids):
        """Set recommended challenges from a list of IDs."""
        self.recommended_challenges_json = json.dumps(challenge_ids)

    def get_custom_exercises(self):
        """Parse and return custom exercises."""
        return json.loads(self.custom_exercises_json) if self.custom_exercises_json else []

    def set_custom_exercises(self, exercises_list):
        """Set custom exercises from a list."""
        self.custom_exercises_json = json.dumps(exercises_list)

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'sensei_id': self.sensei_id,
            'submission_id': self.submission_id,
            'session_date': self.session_date.isoformat() + 'Z' if self.session_date else None,
            'journey_stage': self.journey_stage,
            'session_notes': self.session_notes,
            'concepts_in_progress': self.get_concepts_in_progress(),
            'recommended_challenges': self.get_recommended_challenges(),
            'custom_exercises': self.get_custom_exercises(),
            'certification_granted': self.certification_granted,
            'certification_level': self.certification_level,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
        }

    def __repr__(self):
        return f'<SenseiEvaluation for User {self.user_id} by Sensei {self.sensei_id}>'
