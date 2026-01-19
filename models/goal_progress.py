"""Goal progress model for tracking rubric-based evaluation."""

import json
from datetime import datetime, timedelta
from models import db


class GoalProgress(db.Model):
    """Tracks user progress on core learning goals with expiration."""

    __tablename__ = 'goal_progress'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    learning_goal_id = db.Column(db.Integer, db.ForeignKey('learning_goals.id'), nullable=False)
    core_goal_id = db.Column(db.Integer, db.ForeignKey('core_learning_goals.id'), nullable=False)
    status = db.Column(db.String(20), default='locked')  # locked, in_progress, engaged, passed, expired
    attempts = db.Column(db.Integer, default=0)
    rubric_results_json = db.Column(db.Text)  # JSON with per-item results
    last_explored_submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'))
    unlocked_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)  # When certification expires
    certification_count = db.Column(db.Integer, default=0)  # How many times re-certified
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('user_id', 'core_goal_id', name='unique_user_core_goal'),
    )

    # Relationships
    user = db.relationship('User', backref=db.backref('goal_progress', lazy='dynamic'))
    learning_goal = db.relationship('LearningGoal', backref=db.backref('goal_progress', lazy='dynamic'))
    core_goal = db.relationship('CoreLearningGoal', backref=db.backref('progress_records', lazy='dynamic'))
    last_submission = db.relationship('Submission', foreign_keys=[last_explored_submission_id])

    def get_rubric_results(self):
        """Parse and return the rubric results JSON."""
        if not self.rubric_results_json:
            return {"items": [], "overall_status": "not_started", "pass_count": 0, "fail_count": 0, "total_items": 0}
        return json.loads(self.rubric_results_json)

    def set_rubric_results(self, results):
        """Set rubric results from a dictionary."""
        self.rubric_results_json = json.dumps(results)

    def increment_attempts(self):
        """Increment the attempt count."""
        self.attempts = (self.attempts or 0) + 1
        self.updated_at = datetime.utcnow()

    def mark_item_passed(self, item_id, student_response, evaluation):
        """Mark a specific rubric item as passed."""
        results = self.get_rubric_results()

        # Find or create item result
        item_found = False
        for item in results.get('items', []):
            if item.get('id') == item_id:
                item['status'] = 'passed'
                item['student_response'] = student_response
                item['evaluation'] = evaluation
                item_found = True
                break

        if not item_found:
            if 'items' not in results:
                results['items'] = []
            results['items'].append({
                'id': item_id,
                'status': 'passed',
                'attempts': self.attempts,
                'student_response': student_response,
                'evaluation': evaluation
            })

        # Update pass count
        results['pass_count'] = sum(1 for item in results['items'] if item.get('status') == 'passed')
        self.set_rubric_results(results)

    def mark_item_engaged(self, item_id, student_response, evaluation):
        """Mark a specific rubric item as engaged (tried but not passed)."""
        results = self.get_rubric_results()

        # Find or create item result
        item_found = False
        for item in results.get('items', []):
            if item.get('id') == item_id:
                item['status'] = 'engaged'
                item['student_response'] = student_response
                item['evaluation'] = evaluation
                item_found = True
                break

        if not item_found:
            if 'items' not in results:
                results['items'] = []
            results['items'].append({
                'id': item_id,
                'status': 'engaged',
                'attempts': self.attempts,
                'student_response': student_response,
                'evaluation': evaluation
            })

        self.set_rubric_results(results)

    def is_expired(self):
        """Check if this certification has expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    def set_expiration(self, certification_days):
        """Set the expiration date based on certification days."""
        if certification_days is None:
            self.expires_at = None  # Never expires
        else:
            self.expires_at = datetime.utcnow() + timedelta(days=certification_days)

    def renew_certification(self, certification_days):
        """Renew the certification with a new expiration date."""
        self.certification_count = (self.certification_count or 0) + 1
        self.set_expiration(certification_days)
        self.updated_at = datetime.utcnow()

    def get_effective_status(self):
        """Get the effective status considering expiration."""
        if self.status in ['passed', 'engaged'] and self.is_expired():
            return 'expired'
        return self.status

    def can_unlock_instructor(self):
        """Check if this progress contributes to instructor unlock threshold."""
        return self.status in ['passed', 'engaged'] and not self.is_expired()

    def to_dict(self, include_rubric_results=True):
        """Convert to dictionary."""
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'learning_goal_id': self.learning_goal_id,
            'core_goal_id': self.core_goal_id,
            'status': self.status,
            'effective_status': self.get_effective_status(),
            'attempts': self.attempts,
            'last_explored_submission_id': self.last_explored_submission_id,
            'unlocked_at': self.unlocked_at.isoformat() + 'Z' if self.unlocked_at else None,
            'expires_at': self.expires_at.isoformat() + 'Z' if self.expires_at else None,
            'is_expired': self.is_expired(),
            'certification_count': self.certification_count,
            'completed_at': self.completed_at.isoformat() + 'Z' if self.completed_at else None,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
            'updated_at': self.updated_at.isoformat() + 'Z' if self.updated_at else None,
        }
        if include_rubric_results:
            result['rubric_results'] = self.get_rubric_results()
        return result

    def __repr__(self):
        return f'<GoalProgress user={self.user_id} core_goal={self.core_goal_id} status={self.status}>'
