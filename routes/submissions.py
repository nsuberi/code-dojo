"""Submission routes."""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, Response, stream_with_context
from flask_login import login_required, current_user
import json
from models import db
from models.submission import Submission
from models.goal import LearningGoal
from models.ai_feedback import AIFeedback
from models.core_learning_goal import CoreLearningGoal
from models.goal_progress import GoalProgress
from models.challenge_rubric import ChallengeRubric
from services.github import fetch_github_diff, fetch_github_diff_from_pr
from services.github_pr import (
    parse_pr_url,
    validate_pr_url,
    fetch_pr_metadata,
    validate_pr_base,
    fetch_pr_files
)
from services.ai_feedback import generate_ai_feedback
from services.review_orchestrator import orchestrate_review_streaming, orchestrate_review_streaming_generator

submissions_bp = Blueprint('submissions', __name__, url_prefix='/submissions')


def get_or_create_ai_feedback(submission_id):
    """
    Get existing AIFeedback or create new one.
    Ensures we never violate UNIQUE constraint on submission_id.

    Returns: Tuple of (ai_feedback, created_new)
    """
    ai_feedback = AIFeedback.query.filter_by(submission_id=submission_id).first()

    if ai_feedback:
        return ai_feedback, False

    ai_feedback = AIFeedback(submission_id=submission_id)
    return ai_feedback, True


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
    pr_url = request.form.get('pr_url', '').strip()

    # Validation
    if not goal_id or not pr_url:
        flash('Please provide a GitHub Pull Request URL.', 'danger')
        return redirect(request.referrer or url_for('home'))

    goal = LearningGoal.query.get_or_404(goal_id)

    # Parse and validate PR URL
    parsed = parse_pr_url(pr_url)
    if not parsed:
        flash('Invalid GitHub PR URL format. Expected: https://github.com/owner/repo/pull/123', 'danger')
        return redirect(request.referrer or url_for('home'))

    # Fetch PR metadata
    pr_metadata = fetch_pr_metadata(parsed['owner'], parsed['repo'], parsed['pr_number'])
    if not pr_metadata:
        flash('Could not fetch PR information. Verify the URL is correct and the PR is accessible.', 'danger')
        return redirect(request.referrer or url_for('home'))

    # Validate PR base matches starter repo
    is_valid, error_msg = validate_pr_base(pr_metadata, goal.starter_repo)
    if not is_valid:
        flash(f'Invalid PR: {error_msg}', 'danger')
        return redirect(request.referrer or url_for('home'))

    # Create submission
    submission = Submission(
        user_id=current_user.id,
        goal_id=goal.id,
        pr_url=pr_url,
        pr_number=parsed['pr_number'],
        pr_title=pr_metadata['title'],
        pr_state=pr_metadata['state'],
        pr_base_sha=pr_metadata['base']['sha'],
        pr_head_sha=pr_metadata['head']['sha'],
        status='pending'
    )
    db.session.add(submission)
    db.session.commit()

    # Fetch diff and generate AI feedback
    try:
        diff_content, error = fetch_github_diff_from_pr(pr_url)

        # Get challenge rubric if available for agentic review (Section 3)
        challenge_rubric = ChallengeRubric.query.filter_by(learning_goal_id=goal.id).first()

        # Fetch PR files for enhanced architectural analysis
        pr_files = fetch_pr_files(parsed['owner'], parsed['repo'], parsed['pr_number'])

        if diff_content:
            ai_result = generate_ai_feedback(
                challenge_description=goal.challenge_md,
                diff_content=diff_content,
                challenge_rubric=challenge_rubric,
                submission_id=submission.id,
                pr_metadata=pr_metadata,
                pr_files=pr_files
            )

            # Handle dict response from agentic review vs string from simple review
            if isinstance(ai_result, dict):
                import json
                ai_feedback, created_new = get_or_create_ai_feedback(submission.id)
                ai_feedback.content = ai_result.get('content', '')
                ai_feedback.detected_approach = ai_result.get('detected_approach')
                ai_feedback.evaluation_json = json.dumps(ai_result.get('evaluation')) if ai_result.get('evaluation') else None
                ai_feedback.alternative_approaches_json = json.dumps(ai_result.get('alternatives')) if ai_result.get('alternatives') else None
                ai_feedback.line_references_json = json.dumps(ai_result.get('line_references')) if ai_result.get('line_references') else None

                if created_new:
                    db.session.add(ai_feedback)
            else:
                ai_feedback, created_new = get_or_create_ai_feedback(submission.id)
                ai_feedback.content = ai_result

                if created_new:
                    db.session.add(ai_feedback)
            submission.status = 'ai_complete'
            db.session.commit()
            flash('Submission received! AI feedback is ready.', 'success')
        else:
            flash(f'Could not fetch diff from PR: {error}', 'warning')

    except Exception as e:
        flash(f'Error processing submission: {str(e)}', 'danger')

    return redirect(url_for('modules.goal_detail', module_id=goal.module_id, goal_id=goal.id) + '#tab-review')


@submissions_bp.route('/<int:submission_id>')
@login_required
def view_submission(submission_id):
    """Redirect to goal page review tab (legacy endpoint for backward compatibility)."""
    submission = Submission.query.get_or_404(submission_id)

    # Only allow owner or instructors to view
    if submission.user_id != current_user.id and not current_user.is_instructor:
        flash('You do not have permission to view this submission.', 'danger')
        return redirect(url_for('home'))

    # Redirect to the goal page with review tab active
    return redirect(url_for('modules.goal_detail',
                           module_id=submission.goal.module_id,
                           goal_id=submission.goal_id) + '#tab-review')


@submissions_bp.route('/<int:submission_id>/progress-stream')
@login_required
def stream_analysis_progress(submission_id):
    """Server-Sent Events endpoint for real-time analysis progress."""
    submission = Submission.query.get_or_404(submission_id)

    # Security check - only owner or instructor can access
    if submission.user_id != current_user.id and not current_user.is_instructor:
        return jsonify({'error': 'Unauthorized'}), 403

    # Check if analysis is already complete
    if submission.status == 'ai_complete' and submission.ai_feedback:
        # Return immediate completion event
        def send_complete():
            yield f"data: {json.dumps({'step': 'complete', 'description': 'Analysis already complete', 'progress': 100, 'status': 'complete'})}\n\n"
        return Response(send_complete(), mimetype='text/event-stream')

    def event_generator():
        """Generator function for SSE."""
        try:
            # Get goal and rubric
            goal = LearningGoal.query.get(submission.goal_id)
            if not goal:
                yield f"data: {json.dumps({'step': 'error', 'description': 'Goal not found', 'progress': 0, 'status': 'error'})}\n\n"
                return

            # Get PR data
            parsed = parse_pr_url(submission.pr_url)
            pr_metadata = fetch_pr_metadata(parsed['owner'], parsed['repo'], parsed['pr_number'])
            pr_files = fetch_pr_files(parsed['owner'], parsed['repo'], parsed['pr_number'])
            diff_content, error = fetch_github_diff_from_pr(submission.pr_url)

            if not diff_content:
                yield f"data: {json.dumps({'step': 'error', 'description': f'Could not fetch diff: {error}', 'progress': 0, 'status': 'error'})}\n\n"
                return

            # Get challenge rubric
            challenge_rubric = ChallengeRubric.query.filter_by(learning_goal_id=goal.id).first()

            # Send initial event
            yield f"data: {json.dumps({'step': 'start', 'description': 'Starting analysis', 'progress': 0, 'status': 'running'})}\n\n"

            ai_result = None
            for item in orchestrate_review_streaming_generator(
                submission_id=submission.id,
                challenge_md=goal.challenge_md,
                diff_content=diff_content,
                rubric=challenge_rubric.get_rubric() if challenge_rubric else None,
                pr_metadata=pr_metadata,
                pr_files=pr_files
            ):
                # Check if this is the final result
                if isinstance(item, tuple) and item[0] == "RESULT":
                    ai_result = item[1]
                    break

                # Otherwise it's a progress event - stream to client (ephemeral, no DB writes)
                yield f"data: {json.dumps(item)}\n\n"

            # Save final result
            if isinstance(ai_result, dict):
                ai_feedback, created_new = get_or_create_ai_feedback(submission.id)
                ai_feedback.content = ai_result.get('content', '')
                ai_feedback.detected_approach = ai_result.get('detected_approach')
                ai_feedback.evaluation_json = json.dumps(ai_result.get('evaluation')) if ai_result.get('evaluation') else None
                ai_feedback.alternative_approaches_json = json.dumps(ai_result.get('alternatives')) if ai_result.get('alternatives') else None
                ai_feedback.line_references_json = json.dumps(ai_result.get('line_references')) if ai_result.get('line_references') else None

                if created_new:
                    db.session.add(ai_feedback)

                submission.status = 'ai_complete'
                db.session.commit()

        except Exception as e:
            # Send error event
            error_event = {
                'step': 'error',
                'description': f'Error during analysis: {str(e)}',
                'progress': 0,
                'status': 'error'
            }
            submission.analysis_status = 'error'
            db.session.commit()
            yield f"data: {json.dumps(error_event)}\n\n"

    return Response(event_generator(), mimetype='text/event-stream',
                   headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


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
        diff_content, error = fetch_github_diff_from_pr(submission.pr_url)

        if diff_content:
            # Apply format_diff filter to get formatted HTML
            format_diff = current_app.jinja_env.filters['format_diff']
            formatted_html = format_diff(diff_content)
            return jsonify({
                'diff': diff_content,  # Keep raw for backward compat
                'formatted_html': str(formatted_html)  # Add formatted version
            })
        else:
            return jsonify({'error': error or 'Could not fetch diff from GitHub'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@submissions_bp.route('/api/validate-pr', methods=['GET'])
@login_required
def validate_pr():
    """Validate PR URL and return metadata for preview."""
    pr_url = request.args.get('url', '').strip()
    goal_id = request.args.get('goal_id')

    parsed = parse_pr_url(pr_url)
    if not parsed:
        return jsonify({'valid': False, 'error': 'Invalid PR URL format'})

    pr_metadata = fetch_pr_metadata(parsed['owner'], parsed['repo'], parsed['pr_number'])
    if not pr_metadata:
        return jsonify({'valid': False, 'error': 'Could not fetch PR. It may not exist or may be private.'})

    # If goal_id provided, validate base matches starter repo
    if goal_id:
        goal = LearningGoal.query.get(goal_id)
        if goal:
            is_valid, error_msg = validate_pr_base(pr_metadata, goal.starter_repo)
            if not is_valid:
                return jsonify({'valid': False, 'error': error_msg})

    return jsonify({
        'valid': True,
        'pr': {
            'title': pr_metadata['title'],
            'number': pr_metadata['number'],
            'state': pr_metadata['state'],
            'merged': pr_metadata.get('merged', False),
            'commits': pr_metadata['commits'],
            'changed_files': pr_metadata['changed_files'],
            'additions': pr_metadata['additions'],
            'deletions': pr_metadata['deletions'],
            'html_url': pr_metadata['html_url']
        }
    })


@submissions_bp.route('/<int:submission_id>/files', methods=['GET'])
@login_required
def get_submission_files(submission_id):
    """Get list of files changed in PR."""
    submission = Submission.query.get_or_404(submission_id)

    # Only allow owner or instructors to view
    if submission.user_id != current_user.id and not current_user.is_instructor:
        return jsonify({'error': 'Unauthorized'}), 403

    parsed = parse_pr_url(submission.pr_url)
    if not parsed:
        return jsonify({'error': 'Invalid PR URL'}), 400

    files = fetch_pr_files(parsed['owner'], parsed['repo'], parsed['pr_number'])

    return jsonify({
        'files': [
            {
                'filename': f['filename'],
                'status': f['status'],
                'additions': f['additions'],
                'deletions': f['deletions'],
                'patch': f.get('patch', '')
            }
            for f in files
        ]
    })
