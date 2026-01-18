"""Anatomy conversation models for tracking Socratic dialogues."""

import uuid
from datetime import datetime
from models import db


class AnatomyConversation(db.Model):
    """Conversation tracking for anatomy discussions."""

    __tablename__ = 'anatomy_conversations'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('anatomy_topics.id'), nullable=True)
    topic_name = db.Column(db.String(200))  # For AI-detected topics (no topic_id)
    status = db.Column(db.String(20), default='active')  # active, ended
    synthesis_markdown = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)

    # Relationships
    submission = db.relationship('Submission', backref=db.backref('anatomy_conversations', lazy='dynamic'))
    topic = db.relationship('AnatomyTopic')
    messages = db.relationship('ConversationMessage', backref='conversation', lazy='dynamic', order_by='ConversationMessage.created_at')
    realizations = db.relationship('StudentRealization', backref='conversation', lazy='dynamic', order_by='StudentRealization.detected_at')

    def to_dict(self, include_messages=False, include_realizations=False):
        """Convert to dictionary."""
        result = {
            'id': self.id,
            'submission_id': self.submission_id,
            'topic_id': self.topic_id,
            'topic_name': self.topic_name,
            'status': self.status,
            'synthesis_markdown': self.synthesis_markdown,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
            'ended_at': self.ended_at.isoformat() + 'Z' if self.ended_at else None,
        }
        if include_messages:
            result['messages'] = [m.to_dict() for m in self.messages.all()]
        if include_realizations:
            result['realizations'] = [r.to_dict() for r in self.realizations.all()]
        return result

    def __repr__(self):
        return f'<AnatomyConversation {self.id}>'


class ConversationMessage(db.Model):
    """Individual messages in an anatomy conversation."""

    __tablename__ = 'conversation_messages'

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.String(36), db.ForeignKey('anatomy_conversations.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # user, assistant
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'role': self.role,
            'content': self.content,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
        }

    def __repr__(self):
        return f'<ConversationMessage {self.id} ({self.role})>'


class StudentRealization(db.Model):
    """Tracked realizations from anatomy conversations."""

    __tablename__ = 'student_realizations'

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.String(36), db.ForeignKey('anatomy_conversations.id'), nullable=False)
    topic = db.Column(db.String(200))  # The topic area of the realization
    description = db.Column(db.Text, nullable=False)  # What the student realized
    detected_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'topic': self.topic,
            'description': self.description,
            'detected_at': self.detected_at.isoformat() + 'Z' if self.detected_at else None,
        }

    def __repr__(self):
        return f'<StudentRealization {self.id}>'
