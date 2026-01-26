"""Authentication routes."""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db
from models.user import User
from models.scheduled_session import ScheduledSession

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration page."""
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validation
        errors = []
        if not email:
            errors.append('Email is required.')
        if not password:
            errors.append('Password is required.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters.')

        # Check for existing user
        if User.query.filter_by(email=email).first():
            errors.append('An account with this email already exists.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/signup.html', email=email)

        # Create user
        user = User.create(email=email, password=password)
        login_user(user)
        flash('Account created successfully!', 'success')
        return redirect(url_for('home'))

    return render_template('auth/signup.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page."""
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.authenticate(email, password)
        if user:
            login_user(user)
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


@auth_bp.route('/account')
@login_required
def account():
    """User account page showing submission history."""
    submissions = current_user.submissions.order_by(db.desc('created_at')).all()

    # Get upcoming scheduled sessions
    scheduled_sessions = ScheduledSession.query.filter(
        ScheduledSession.user_id == current_user.id,
        ScheduledSession.session_completed_at.is_(None)
    ).order_by(ScheduledSession.scheduled_at.desc()).all()

    return render_template('account.html',
                           submissions=submissions,
                           scheduled_sessions=scheduled_sessions)


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Password reset page (stub for demo)."""
    if request.method == 'POST':
        flash('Password reset functionality is a stub for this demo.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html')
