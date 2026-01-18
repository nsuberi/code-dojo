"""Scheduling routes for booking sessions with instructors."""

from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models.submission import Submission

scheduling_bp = Blueprint('scheduling', __name__, url_prefix='/schedule')


@scheduling_bp.route('/<int:submission_id>')
@login_required
def book(submission_id):
    """Display the Calendly booking page for a submission that needs more work."""
    submission = Submission.query.get_or_404(submission_id)

    # Validate submission belongs to current user
    if submission.user_id != current_user.id:
        flash('You can only schedule sessions for your own submissions.', 'danger')
        return redirect(url_for('home'))

    # Validate submission has "Needs Work" status (instructor feedback with passed=False)
    if not submission.instructor_feedback or submission.instructor_feedback.passed:
        flash('Scheduling is only available for submissions that need more work.', 'warning')
        return redirect(url_for('submissions.view_submission', submission_id=submission_id))

    # Get Calendly URL from config
    calendly_url = current_app.config.get('CALENDLY_URL', '')

    if not calendly_url:
        flash('Scheduling is not currently available. Please contact the instructor directly.', 'warning')
        return redirect(url_for('submissions.view_submission', submission_id=submission_id))

    return render_template(
        'scheduling/book.html',
        submission=submission,
        calendly_url=calendly_url,
        student_email=current_user.email,
        student_name=current_user.email.split('@')[0]  # Use email prefix as name
    )
