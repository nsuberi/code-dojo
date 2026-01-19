"""Submission routes."""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db
from models.submission import Submission
from models.goal import LearningGoal
from models.ai_feedback import AIFeedback
from models.core_learning_goal import CoreLearningGoal
from models.goal_progress import GoalProgress
from models.challenge_rubric import ChallengeRubric
from services.github import fetch_github_diff
from services.ai_feedback import generate_ai_feedback

submissions_bp = Blueprint('submissions', __name__, url_prefix='/submissions')


def check_instructor_unlock_threshold(user_id, learning_goal_id):
    """Check if user has met 50% engagement threshold for instructor feedback.

    Returns:
        Tuple of (can_unlock, stats_dict)
    """
    core_goals = CoreLearningGoal.query.filter_by(learning_goal_id=learning_goal_id).all()

    if not core_goals:
        # No core goals defined - allow by default
        return True, {'total': 0, 'valid': 0, 'threshold_met': True}

    total = len(core_goals)
    valid_count = 0

    for goal in core_goals:
        progress = GoalProgress.query.filter_by(
            user_id=user_id,
            core_goal_id=goal.id
        ).first()

        if progress and progress.can_unlock_instructor():
            valid_count += 1

    threshold_met = valid_count / total >= 0.5 if total > 0 else True

    return threshold_met, {
        'total': total,
        'valid': valid_count,
        'threshold_met': threshold_met,
        'needed': max(0, (total // 2 + 1) - valid_count)
    }


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

        # Get challenge rubric if available for agentic review (Section 3)
        challenge_rubric = ChallengeRubric.query.filter_by(learning_goal_id=goal.id).first()

        if diff_content:
            ai_result = generate_ai_feedback(
                challenge_description=goal.challenge_md,
                diff_content=diff_content,
                challenge_rubric=challenge_rubric,
                submission_id=submission.id
            )

            # Handle dict response from agentic review vs string from simple review
            if isinstance(ai_result, dict):
                import json
                ai_feedback = AIFeedback(
                    submission_id=submission.id,
                    content=ai_result.get('content', ''),
                    detected_approach=ai_result.get('detected_approach'),
                    evaluation_json=json.dumps(ai_result.get('evaluation')) if ai_result.get('evaluation') else None,
                    alternative_approaches_json=json.dumps(ai_result.get('alternatives')) if ai_result.get('alternatives') else None,
                    line_references_json=json.dumps(ai_result.get('line_references')) if ai_result.get('line_references') else None
                )
            else:
                ai_feedback = AIFeedback(
                    submission_id=submission.id,
                    content=ai_result
                )

            db.session.add(ai_feedback)
            submission.status = 'ai_complete'
            db.session.commit()
            flash('Submission received! AI feedback is ready.', 'success')
        else:
            flash('Could not fetch diff from GitHub. Please check your repository URL and branch.', 'warning')

    except Exception as e:
        flash(f'Error processing submission: {str(e)}', 'danger')

    return redirect(url_for('modules.goal_detail', module_id=goal.module_id, goal_id=goal.id) + '#tab-review')


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

    # Check if user has met the engagement threshold
    force_skip = request.form.get('force_skip') == 'true'
    can_unlock, stats = check_instructor_unlock_threshold(current_user.id, submission.goal_id)

    if not can_unlock and not force_skip:
        flash(f'Please explore at least {stats["needed"]} more concepts with the Digi-Trainer before requesting Sensei feedback. '
              f'(Current progress: {stats["valid"]}/{stats["total"]})', 'warning')
        return redirect(url_for('submissions.view_submission', submission_id=submission_id))

    submission.status = 'feedback_requested'
    db.session.commit()

    if force_skip:
        flash('Instructor feedback requested! Note: You skipped the engagement threshold.', 'info')
    else:
        flash('Instructor feedback requested! Great job engaging with the material first.', 'success')

    return redirect(url_for('submissions.view_submission', submission_id=submission_id))


@submissions_bp.route('/<int:submission_id>/check-instructor-unlock')
@login_required
def check_instructor_unlock(submission_id):
    """Check if user can request instructor feedback (API endpoint)."""
    submission = Submission.query.get_or_404(submission_id)

    if submission.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    can_unlock, stats = check_instructor_unlock_threshold(current_user.id, submission.goal_id)

    return jsonify({
        'can_unlock': can_unlock,
        'stats': stats
    })


@submissions_bp.route('/<int:submission_id>/diff')
@login_required
def get_submission_diff(submission_id):
    """Get the diff content for a submission (API endpoint)."""
    submission = Submission.query.get_or_404(submission_id)

    # Only allow owner or instructors to view
    if submission.user_id != current_user.id and not current_user.is_instructor:
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        diff_content = fetch_github_diff(
            submission.goal.starter_repo,
            submission.repo_url,
            submission.branch
        )

        if diff_content:
            return jsonify({'diff': diff_content})
        else:
            return jsonify({'error': 'Could not fetch diff from GitHub'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500
