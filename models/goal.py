"""Learning goal model."""

from models import db


class LearningGoal(db.Model):
    """A specific learning goal within a module."""

    __tablename__ = 'learning_goals'

    id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, db.ForeignKey('learning_modules.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    video_url = db.Column(db.String(500))  # YouTube embed URL
    challenge_md = db.Column(db.Text)  # Challenge description in markdown
    starter_repo = db.Column(db.String(500))  # GitHub repo URL for diff comparison
    order = db.Column(db.Integer, default=0)

    # Relationships
    submissions = db.relationship('Submission', backref='goal', lazy='dynamic')

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'module_id': self.module_id,
            'title': self.title,
            'video_url': self.video_url,
            'challenge_md': self.challenge_md,
            'starter_repo': self.starter_repo,
            'order': self.order,
        }

    def __repr__(self):
        return f'<LearningGoal {self.title}>'
