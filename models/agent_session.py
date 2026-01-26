"""Agent session models for tracking harness conversations."""

import uuid
from datetime import datetime
from models import db


class AgentSession(db.Model):
    """Tracks agent harness sessions for planning and articulation."""

    __tablename__ = 'agent_sessions'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    learning_goal_id = db.Column(db.Integer, db.ForeignKey('learning_goals.id'), nullable=False)
    core_goal_id = db.Column(db.Integer, db.ForeignKey('core_learning_goals.id'))
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'))  # NULL if pre-coding
    harness_type = db.Column(db.String(20), nullable=False)  # 'planning' or 'articulation'
    context = db.Column(db.String(20), nullable=False)  # 'pre_coding' or 'post_submission'
    status = db.Column(db.String(20), default='active')  # active, completed, abandoned
    guide_me_mode = db.Column(db.Boolean, default=False)
    langsmith_run_id = db.Column(db.String(100))
    langsmith_trace_headers = db.Column(db.Text)  # Store serialized headers for parent context
    current_topic_thread_id = db.Column(db.String(100))  # Current topic's thread ID for tracing
    current_topic_trace_headers = db.Column(db.Text)  # Store serialized headers for topic context
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    # State tracking
    current_goal_index = db.Column(db.Integer)
    current_rubric_item_index = db.Column(db.Integer, default=0)
    current_attempts = db.Column(db.Integer, default=0)
    goals_passed = db.Column(db.Integer, default=0)
    goals_engaged = db.Column(db.Integer, default=0)
    total_goals = db.Column(db.Integer, default=0)

    # Relationships
    user = db.relationship('User', backref=db.backref('agent_sessions', lazy='dynamic'))
    learning_goal = db.relationship('LearningGoal', backref=db.backref('agent_sessions', lazy='dynamic'))
    core_goal = db.relationship('CoreLearningGoal', backref=db.backref('agent_sessions', lazy='dynamic'))
    submission = db.relationship('Submission', backref=db.backref('agent_sessions', lazy='dynamic'))
    messages = db.relationship('AgentMessage', backref='session', lazy='dynamic', order_by='AgentMessage.created_at')

    def calculate_engagement_percent(self):
        """Calculate the percentage of goals engaged or passed."""
        if self.total_goals == 0:
            return 0
        return (self.goals_engaged + self.goals_passed) / self.total_goals

    def can_request_instructor(self):
        """Check if student has met the 50% engagement threshold."""
        return self.calculate_engagement_percent() >= 0.5

    def to_dict(self, include_messages=False):
        """Convert to dictionary."""
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'learning_goal_id': self.learning_goal_id,
            'core_goal_id': self.core_goal_id,
            'submission_id': self.submission_id,
            'harness_type': self.harness_type,
            'context': self.context,
            'status': self.status,
            'guide_me_mode': self.guide_me_mode,
            'langsmith_run_id': self.langsmith_run_id,
            'langsmith_trace_headers': self.langsmith_trace_headers,
            'current_topic_thread_id': self.current_topic_thread_id,
            'current_topic_trace_headers': self.current_topic_trace_headers,
            'current_goal_index': self.current_goal_index,
            'current_rubric_item_index': self.current_rubric_item_index,
            'current_attempts': self.current_attempts,
            'goals_passed': self.goals_passed,
            'goals_engaged': self.goals_engaged,
            'total_goals': self.total_goals,
            'engagement_percent': self.calculate_engagement_percent(),
            'can_request_instructor': self.can_request_instructor(),
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
            'completed_at': self.completed_at.isoformat() + 'Z' if self.completed_at else None,
        }
        if include_messages:
            result['messages'] = [m.to_dict() for m in self.messages.all()]
        return result

    def __repr__(self):
        return f'<AgentSession {self.id} type={self.harness_type}>'


class AgentMessage(db.Model):
    """Individual messages in an agent session."""

    __tablename__ = 'agent_messages'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), db.ForeignKey('agent_sessions.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # user, assistant, system
    content = db.Column(db.Text, nullable=False)
    input_mode = db.Column(db.String(10))  # 'voice' | 'text'
    voice_duration_seconds = db.Column(db.Integer)
    original_transcription = db.Column(db.Text)  # Raw transcription before edits
    metadata_json = db.Column(db.Text)  # rubric item ID, attempt number, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convert to dictionary."""
        import json
        return {
            'id': self.id,
            'session_id': self.session_id,
            'role': self.role,
            'content': self.content,
            'input_mode': self.input_mode,
            'voice_duration_seconds': self.voice_duration_seconds,
            'original_transcription': self.original_transcription,
            'metadata': json.loads(self.metadata_json) if self.metadata_json else None,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
        }

    def __repr__(self):
        return f'<AgentMessage {self.id} ({self.role})>'
