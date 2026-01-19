"""Challenge rubric model for multi-approach evaluation."""

import json
from datetime import datetime
from models import db


class ChallengeRubric(db.Model):
    """Multi-approach rubric for challenge evaluation."""

    __tablename__ = 'challenge_rubrics'

    id = db.Column(db.Integer, primary_key=True)
    learning_goal_id = db.Column(db.Integer, db.ForeignKey('learning_goals.id'), unique=True)
    title = db.Column(db.String(200), nullable=False)
    rubric_json = db.Column(db.Text, nullable=False)  # Multi-approach schema
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    learning_goal = db.relationship('LearningGoal', backref=db.backref('rubric', uselist=False))

    def get_rubric(self):
        """Parse and return the rubric JSON."""
        return json.loads(self.rubric_json) if self.rubric_json else None

    def set_rubric(self, rubric_dict):
        """Set the rubric from a dictionary."""
        self.rubric_json = json.dumps(rubric_dict)

    def get_valid_approaches(self):
        """Get list of valid approaches for this challenge."""
        rubric = self.get_rubric()
        if rubric:
            return rubric.get('valid_approaches', [])
        return []

    def get_approach_by_id(self, approach_id):
        """Get a specific approach by its ID."""
        for approach in self.get_valid_approaches():
            if approach.get('id') == approach_id:
                return approach
        return None

    def get_universal_criteria(self):
        """Get criteria that apply to all approaches."""
        rubric = self.get_rubric()
        if rubric:
            return rubric.get('universal_criteria', [])
        return []

    def get_approach_criteria(self, approach_id):
        """Get criteria specific to an approach."""
        rubric = self.get_rubric()
        if rubric:
            approach_specific = rubric.get('approach_specific_criteria', {})
            return approach_specific.get(approach_id, [])
        return []

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'learning_goal_id': self.learning_goal_id,
            'title': self.title,
            'rubric': self.get_rubric(),
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
        }

    def __repr__(self):
        return f'<ChallengeRubric {self.title}>'
