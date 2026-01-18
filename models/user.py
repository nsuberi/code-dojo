"""User model for authentication."""

from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from models import db


class User(UserMixin, db.Model):
    """User account for authentication and role management."""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # student, instructor, admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    submissions = db.relationship('Submission', backref='user', lazy='dynamic')
    instructor_feedbacks = db.relationship('InstructorFeedback', backref='instructor', lazy='dynamic')

    def set_password(self, password):
        """Hash and store the password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify a password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        """Check if user is an admin."""
        return self.role == 'admin'

    @property
    def is_instructor(self):
        """Check if user is an instructor or admin."""
        return self.role in ('instructor', 'admin')

    @staticmethod
    def create(email, password, role='student'):
        """Create a new user with the given credentials."""
        user = User(email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def authenticate(email, password):
        """Authenticate a user by email and password."""
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            return user
        return None

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
        }

    def __repr__(self):
        return f'<User {self.email}>'
