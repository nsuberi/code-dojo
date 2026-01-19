"""Learning goal model."""

import json
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

    # Prerequisite and progression tracking (Section 13)
    prerequisites_json = db.Column(db.Text)  # [goal_id, goal_id, ...]
    difficulty_level = db.Column(db.Integer, default=1)  # 1-5
    category_tags_json = db.Column(db.Text)  # ["auth", "api", "security"]

    # Relationships
    submissions = db.relationship('Submission', backref='goal', lazy='dynamic')

    def get_prerequisites(self):
        """Parse and return prerequisite goal IDs."""
        return json.loads(self.prerequisites_json) if self.prerequisites_json else []

    def set_prerequisites(self, goal_ids):
        """Set prerequisites from a list of goal IDs."""
        self.prerequisites_json = json.dumps(goal_ids)

    def get_category_tags(self):
        """Parse and return category tags."""
        return json.loads(self.category_tags_json) if self.category_tags_json else []

    def set_category_tags(self, tags_list):
        """Set category tags from a list."""
        self.category_tags_json = json.dumps(tags_list)

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
            'prerequisites': self.get_prerequisites(),
            'difficulty_level': self.difficulty_level,
            'category_tags': self.get_category_tags(),
        }

    def __repr__(self):
        return f'<LearningGoal {self.title}>'
