"""Scheduling routes for booking sessions with instructors."""

from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import db
from models.submission import Submission
from models.goal_progress import GoalProgress
from models.scheduled_session import ScheduledSession

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

    # Check two conditions for scheduling eligibility:
    # 1. Instructor feedback with "Needs Work" (passed=False)
    has_needs_work_feedback = (
        submission.instructor_feedback and
        not submission.instructor_feedback.passed
    )

    # 2. Digi-trainer engagement (at least one gem engaged/passed)
    core_goal_ids = [g.id for g in submission.goal.core_learning_goals]
    has_digi_trainer_engagement = GoalProgress.query.filter(
        GoalProgress.user_id == current_user.id,
        GoalProgress.core_goal_id.in_(core_goal_ids),
        GoalProgress.status.in_(['passed', 'engaged']),
        db.or_(
            GoalProgress.expires_at.is_(None),
            GoalProgress.expires_at > datetime.utcnow()
        )
    ).first() is not None

    # Allow scheduling if either condition is met
    if not has_needs_work_feedback and not has_digi_trainer_engagement:
        flash('Complete at least one gem or receive instructor feedback to schedule.', 'warning')
        return redirect(url_for('submissions.view_submission', submission_id=submission_id))

    # Get Calendly URL from config
    calendly_url = current_app.config.get('CALENDLY_URL', '')

    if not calendly_url:
        flash('Scheduling is not currently available. Please contact the instructor directly.', 'warning')
        return redirect(url_for('submissions.view_submission', submission_id=submission_id))

    # Check if already scheduled recently (within 1 hour) to avoid duplicates
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent_session = ScheduledSession.query.filter(
        ScheduledSession.submission_id == submission_id,
        ScheduledSession.user_id == current_user.id,
        ScheduledSession.scheduled_at > one_hour_ago
    ).first()

    if not recent_session:
        # Determine eligibility reason
        eligibility_reason = 'needs_work_feedback' if has_needs_work_feedback else 'digi_trainer_engagement'

        # Calculate goal progress stats
        goal_progress_list = GoalProgress.query.filter(
            GoalProgress.user_id == current_user.id,
            GoalProgress.core_goal_id.in_(core_goal_ids),
            db.or_(
                GoalProgress.expires_at.is_(None),
                GoalProgress.expires_at > datetime.utcnow()
            )
        ).all()

        goals_passed = sum(1 for gp in goal_progress_list if gp.status == 'passed')
        goals_engaged = sum(1 for gp in goal_progress_list if gp.status == 'engaged')
        total_goals = len(core_goal_ids)

        # Create scheduled session record
        scheduled_session = ScheduledSession(
            submission_id=submission_id,
            user_id=current_user.id,
            eligibility_reason=eligibility_reason,
            goals_passed=goals_passed,
            goals_engaged=goals_engaged,
            total_goals=total_goals,
            scheduled_at=datetime.utcnow()
        )
        db.session.add(scheduled_session)
        db.session.commit()

    return render_template(
        'scheduling/book.html',
        submission=submission,
        calendly_url=calendly_url,
        student_email=current_user.email,
        student_name=current_user.email.split('@')[0]  # Use email prefix as name
    )
