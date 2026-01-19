"""Voice input metrics model for analytics."""

from datetime import datetime
from models import db


class VoiceInputMetrics(db.Model):
    """Tracks voice input usage for analytics."""

    __tablename__ = 'voice_input_metrics'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(36), db.ForeignKey('agent_sessions.id'))
    offered_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    response = db.Column(db.String(20))  # 'accepted' | 'declined'
    voice_duration_seconds = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('voice_metrics', lazy='dynamic'))
    session = db.relationship('AgentSession', backref=db.backref('voice_metrics', lazy='dynamic'))

    @classmethod
    def record_offer(cls, user_id, session_id=None):
        """Record that voice input was offered to the user."""
        metric = cls(
            user_id=user_id,
            session_id=session_id,
            offered_at=datetime.utcnow()
        )
        db.session.add(metric)
        db.session.commit()
        return metric

    @classmethod
    def record_acceptance(cls, user_id, session_id=None, duration_seconds=None):
        """Record that user accepted voice input."""
        metric = cls(
            user_id=user_id,
            session_id=session_id,
            offered_at=datetime.utcnow(),
            response='accepted',
            voice_duration_seconds=duration_seconds
        )
        db.session.add(metric)
        db.session.commit()
        return metric

    @classmethod
    def record_decline(cls, user_id, session_id=None):
        """Record that user declined voice input."""
        metric = cls(
            user_id=user_id,
            session_id=session_id,
            offered_at=datetime.utcnow(),
            response='declined'
        )
        db.session.add(metric)
        db.session.commit()
        return metric

    @classmethod
    def get_skip_rate(cls, user_id=None):
        """Calculate the voice input skip rate."""
        query = cls.query.filter(cls.response.isnot(None))
        if user_id:
            query = query.filter_by(user_id=user_id)

        total = query.count()
        if total == 0:
            return 0

        declined = query.filter_by(response='declined').count()
        return declined / total

    @classmethod
    def get_user_stats(cls, user_id):
        """Get voice input statistics for a user."""
        metrics = cls.query.filter_by(user_id=user_id).all()

        total_offered = len(metrics)
        accepted = sum(1 for m in metrics if m.response == 'accepted')
        declined = sum(1 for m in metrics if m.response == 'declined')
        total_duration = sum(m.voice_duration_seconds or 0 for m in metrics if m.response == 'accepted')

        return {
            'total_offered': total_offered,
            'accepted': accepted,
            'declined': declined,
            'skip_rate': declined / total_offered if total_offered > 0 else 0,
            'total_duration_seconds': total_duration,
            'avg_duration_seconds': total_duration / accepted if accepted > 0 else 0
        }

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'offered_at': self.offered_at.isoformat() + 'Z' if self.offered_at else None,
            'response': self.response,
            'voice_duration_seconds': self.voice_duration_seconds,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
        }

    def __repr__(self):
        return f'<VoiceInputMetrics user={self.user_id} response={self.response}>'
