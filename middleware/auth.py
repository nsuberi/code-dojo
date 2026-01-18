"""Authentication middleware decorators."""

from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user


def require_auth(f):
    """Decorator that requires user to be authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def require_admin(f):
    """Decorator that requires user to be an admin."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            flash('Admin access required.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated


def require_instructor(f):
    """Decorator that requires user to be an instructor or admin."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if not current_user.is_instructor:
            flash('Instructor access required.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated
