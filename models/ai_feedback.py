"""AI feedback model."""

import json
from datetime import datetime
from models import db


class AIFeedback(db.Model):
    """AI-generated feedback for a submission."""

    __tablename__ = 'ai_feedbacks'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False, unique=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Enhanced fields for agentic review (Section 3.1)
    detected_approach = db.Column(db.String(100))  # Which approach was detected (api_key, basic_auth, jwt)
    evaluation_json = db.Column(db.Text)  # Structured rubric evaluation results
    alternative_approaches_json = db.Column(db.Text)  # Discussion of other valid solutions
    line_references_json = db.Column(db.Text)  # Specific line references for feedback

    def get_evaluation(self):
        """Parse and return the evaluation JSON."""
        return json.loads(self.evaluation_json) if self.evaluation_json else None

    def set_evaluation(self, evaluation_dict):
        """Set the evaluation from a dictionary."""
        self.evaluation_json = json.dumps(evaluation_dict)

    def get_alternative_approaches(self):
        """Parse and return alternative approaches JSON."""
        return json.loads(self.alternative_approaches_json) if self.alternative_approaches_json else None

    def set_alternative_approaches(self, approaches_dict):
        """Set alternative approaches from a dictionary."""
        self.alternative_approaches_json = json.dumps(approaches_dict)

    def get_line_references(self):
        """Parse and return line references JSON."""
        return json.loads(self.line_references_json) if self.line_references_json else None

    def set_line_references(self, references_list):
        """Set line references from a list."""
        self.line_references_json = json.dumps(references_list)

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'submission_id': self.submission_id,
            'content': self.content,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
            'detected_approach': self.detected_approach,
            'evaluation': self.get_evaluation(),
            'alternative_approaches': self.get_alternative_approaches(),
            'line_references': self.get_line_references(),
        }

    def __repr__(self):
        return f'<AIFeedback for Submission {self.submission_id}>'
