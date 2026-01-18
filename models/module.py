"""Learning module model."""

from models import db


class LearningModule(db.Model):
    """A learning module containing multiple goals."""

    __tablename__ = 'learning_modules'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)

    # Relationships
    goals = db.relationship('LearningGoal', backref='module', lazy='dynamic', order_by='LearningGoal.order')

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'order': self.order,
            'goal_count': self.goals.count(),
        }

    def __repr__(self):
        return f'<LearningModule {self.title}>'
