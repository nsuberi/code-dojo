"""Anatomy topic model for admin-configured discussion topics."""

from models import db


class AnatomyTopic(db.Model):
    """Admin-configured anatomy topics per learning goal."""

    __tablename__ = 'anatomy_topics'

    id = db.Column(db.Integer, primary_key=True)
    goal_id = db.Column(db.Integer, db.ForeignKey('learning_goals.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # e.g., "Flask Routes", "Authentication"
    description = db.Column(db.Text)  # What students should understand
    suggested_analogies = db.Column(db.Text)  # Analogies for Socratic teaching
    order = db.Column(db.Integer, default=0)

    # Relationships
    goal = db.relationship('LearningGoal', backref=db.backref('anatomy_topics', lazy='dynamic', order_by='AnatomyTopic.order'))

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'goal_id': self.goal_id,
            'name': self.name,
            'description': self.description,
            'suggested_analogies': self.suggested_analogies,
            'order': self.order,
        }

    def __repr__(self):
        return f'<AnatomyTopic {self.name}>'
