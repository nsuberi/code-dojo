"""Submission routes."""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db
from models.submission import Submission
from models.goal import LearningGoal
from models.ai_feedback import AIFeedback
from services.github import fetch_github_diff
from services.ai_feedback import generate_ai_feedback

submissions_bp = Blueprint('submissions', __name__, url_prefix='/submissions')


@submissions_bp.route('/create', methods=['POST'])
@login_required
def create_submission():
    """Create a new submission."""
    goal_id = request.form.get('goal_id')
    repo_url = request.form.get('repo_url', '').strip()
    branch = request.form.get('branch', 'main').strip() or 'main'

    # Validation
    if not goal_id or not repo_url:
        flash('Please provide a GitHub repository URL.', 'danger')
        return redirect(request.referrer or url_for('home'))

    goal = LearningGoal.query.get_or_404(goal_id)

    # Create submission
    submission = Submission(
        user_id=current_user.id,
        goal_id=goal.id,
        repo_url=repo_url,
        branch=branch,
        status='pending'
    )
    db.session.add(submission)
    db.session.commit()

    # Fetch diff and generate AI feedback
    try:
        diff_content = fetch_github_diff(goal.starter_repo, repo_url, branch)

        if diff_content:
            ai_content = generate_ai_feedback(
                challenge_description=goal.challenge_md,
                diff_content=diff_content
            )

            ai_feedback = AIFeedback(
                submission_id=submission.id,
                content=ai_content
            )
            db.session.add(ai_feedback)
            submission.status = 'ai_complete'
            db.session.commit()
            flash('Submission received! AI feedback is ready.', 'success')
        else:
            flash('Could not fetch diff from GitHub. Please check your repository URL and branch.', 'warning')

    except Exception as e:
        flash(f'Error processing submission: {str(e)}', 'danger')

    return redirect(url_for('submissions.view_submission', submission_id=submission.id))


@submissions_bp.route('/<int:submission_id>')
@login_required
def view_submission(submission_id):
    """View a submission (student view)."""
    submission = Submission.query.get_or_404(submission_id)

    # Only allow owner or instructors to view
    if submission.user_id != current_user.id and not current_user.is_instructor:
        flash('You do not have permission to view this submission.', 'danger')
        return redirect(url_for('home'))

    return render_template('submissions/student_view.html', submission=submission)


@submissions_bp.route('/<int:submission_id>/request-feedback', methods=['POST'])
@login_required
def request_instructor_feedback(submission_id):
    """Request instructor feedback for a submission."""
    submission = Submission.query.get_or_404(submission_id)

    if submission.user_id != current_user.id:
        flash('You can only request feedback for your own submissions.', 'danger')
        return redirect(url_for('home'))

    if submission.status not in ('ai_complete', 'feedback_requested'):
        flash('Submission must have AI feedback before requesting instructor review.', 'warning')
        return redirect(url_for('submissions.view_submission', submission_id=submission_id))

    submission.status = 'feedback_requested'
    db.session.commit()
    flash('Instructor feedback requested!', 'success')
    return redirect(url_for('submissions.view_submission', submission_id=submission_id))
