"""Core learning goal model with rubric-based evaluation."""

import json
from datetime import datetime
from models import db


class CoreLearningGoal(db.Model):
    """Core learning goals with rubrics for rubric-based learning evaluation."""

    __tablename__ = 'core_learning_goals'

    id = db.Column(db.Integer, primary_key=True)
    learning_goal_id = db.Column(db.Integer, db.ForeignKey('learning_goals.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    rubric_json = db.Column(db.Text, nullable=False)  # JSON array of rubric items
    order_index = db.Column(db.Integer, default=0)
    gem_color = db.Column(db.String(20), default='blue')
    certification_days = db.Column(db.Integer, default=90)  # How many days until expiration
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    learning_goal = db.relationship('LearningGoal', backref=db.backref(
        'core_learning_goals', lazy='dynamic', order_by='CoreLearningGoal.order_index'
    ))

    def get_rubric(self):
        """Parse and return the rubric JSON."""
        if not self.rubric_json:
            return {"items": []}
        return json.loads(self.rubric_json)

    def get_rubric_item(self, item_id):
        """Get a specific rubric item by ID."""
        rubric = self.get_rubric()
        for item in rubric.get('items', []):
            if item.get('id') == item_id:
                return item
        return None

    def get_rubric_items(self):
        """Get all rubric items."""
        return self.get_rubric().get('items', [])

    def to_dict(self, include_rubric=True):
        """Convert to dictionary."""
        result = {
            'id': self.id,
            'learning_goal_id': self.learning_goal_id,
            'title': self.title,
            'description': self.description,
            'order_index': self.order_index,
            'gem_color': self.gem_color,
            'certification_days': self.certification_days,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
            'updated_at': self.updated_at.isoformat() + 'Z' if self.updated_at else None,
        }
        if include_rubric:
            result['rubric'] = self.get_rubric()
        return result

    def __repr__(self):
        return f'<CoreLearningGoal {self.title}>'
