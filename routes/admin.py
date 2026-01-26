"""Admin and instructor routes."""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db
from models.user import User
from models.submission import Submission
from models.instructor_feedback import InstructorFeedback
from models.goal import LearningGoal
from models.anatomy_topic import AnatomyTopic
from models.anatomy_conversation import AnatomyConversation
from models.scheduled_session import ScheduledSession
from models.goal_progress import GoalProgress
from models.agent_session import AgentSession
from middleware.auth import require_admin, require_instructor
from services.github import fetch_github_diff, calculate_diff_stats

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/')
@require_admin
def dashboard():
    """Admin dashboard showing all students and submissions."""
    students = User.query.filter(User.role == 'student').order_by(User.created_at.desc()).all()
    submissions = Submission.query.order_by(Submission.created_at.desc()).all()
    pending_reviews = Submission.query.filter_by(status='feedback_requested').count()

    # Query uncompleted scheduled sessions
    scheduled_sessions = ScheduledSession.query.filter(
        ScheduledSession.session_completed_at.is_(None)
    ).order_by(ScheduledSession.scheduled_at.desc()).all()

    return render_template('admin/dashboard.html',
                           students=students,
                           submissions=submissions,
                           pending_reviews=pending_reviews,
                           scheduled_sessions=scheduled_sessions)


@admin_bp.route('/submissions/<int:submission_id>/review', methods=['GET', 'POST'])
@require_instructor
def review_submission(submission_id):
    """Instructor view for reviewing a submission."""
    submission = Submission.query.get_or_404(submission_id)
    goal = submission.goal

    # Try to get the diff for display
    diff_content = None
    diff_stats = {'file_count': 0, 'total_additions': 0, 'total_deletions': 0}
    try:
        diff_content = fetch_github_diff(goal.starter_repo, submission.repo_url, submission.branch)
        if diff_content:
            diff_stats = calculate_diff_stats(diff_content)
    except Exception:
        pass

    if request.method == 'POST':
        comment = request.form.get('comment', '').strip()
        passed = request.form.get('passed') == 'true'

        # Check if feedback already exists
        if submission.instructor_feedback:
            # Update existing feedback
            submission.instructor_feedback.comment = comment
            submission.instructor_feedback.passed = passed
            submission.instructor_feedback.instructor_id = current_user.id
        else:
            # Create new feedback
            feedback = InstructorFeedback(
                submission_id=submission.id,
                instructor_id=current_user.id,
                comment=comment,
                passed=passed
            )
            db.session.add(feedback)

        submission.status = 'reviewed'
        db.session.commit()
        flash('Review saved successfully!', 'success')
        return redirect(url_for('admin.dashboard'))

    return render_template('submissions/instructor_view.html',
                           submission=submission,
                           diff_content=diff_content,
                           file_count=diff_stats['file_count'],
                           total_additions=diff_stats['total_additions'],
                           total_deletions=diff_stats['total_deletions'])


@admin_bp.route('/goals/<int:goal_id>/anatomy-topics', methods=['GET', 'POST'])
@require_admin
def anatomy_topics(goal_id):
    """Manage anatomy topics for a learning goal."""
    goal = LearningGoal.query.get_or_404(goal_id)

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            suggested_analogies = request.form.get('suggested_analogies', '').strip()

            if name:
                # Get max order for this goal
                max_order = db.session.query(db.func.max(AnatomyTopic.order)).filter_by(goal_id=goal_id).scalar() or 0
                topic = AnatomyTopic(
                    goal_id=goal_id,
                    name=name,
                    description=description,
                    suggested_analogies=suggested_analogies,
                    order=max_order + 1
                )
                db.session.add(topic)
                db.session.commit()
                flash(f'Topic "{name}" added successfully!', 'success')
            else:
                flash('Topic name is required.', 'danger')

        elif action == 'update':
            topic_id = request.form.get('topic_id')
            topic = AnatomyTopic.query.get_or_404(topic_id)

            topic.name = request.form.get('name', '').strip()
            topic.description = request.form.get('description', '').strip()
            topic.suggested_analogies = request.form.get('suggested_analogies', '').strip()
            db.session.commit()
            flash('Topic updated successfully!', 'success')

        elif action == 'delete':
            topic_id = request.form.get('topic_id')
            topic = AnatomyTopic.query.get_or_404(topic_id)
            db.session.delete(topic)
            db.session.commit()
            flash('Topic deleted successfully!', 'success')

        elif action == 'reorder':
            order_data = request.form.get('order', '')
            if order_data:
                for idx, topic_id in enumerate(order_data.split(',')):
                    topic = AnatomyTopic.query.get(int(topic_id))
                    if topic:
                        topic.order = idx
                db.session.commit()

        return redirect(url_for('admin.anatomy_topics', goal_id=goal_id))

    topics = AnatomyTopic.query.filter_by(goal_id=goal_id).order_by(AnatomyTopic.order).all()
    return render_template('admin/anatomy_topics.html', goal=goal, topics=topics)


@admin_bp.route('/submissions/<int:submission_id>/conversations')
@require_instructor
def submission_conversations(submission_id):
    """View anatomy conversations for a submission."""
    submission = Submission.query.get_or_404(submission_id)
    conversations = submission.anatomy_conversations.order_by(AnatomyConversation.created_at.desc()).all()

    return render_template('admin/submission_conversations.html',
                           submission=submission,
                           conversations=conversations)


@admin_bp.route('/scheduled-sessions/<int:session_id>')
@require_instructor
def view_scheduled_session(session_id):
    """View full details of a scheduled session including goal progress and conversations."""
    scheduled_session = ScheduledSession.query.get_or_404(session_id)
    submission = scheduled_session.submission
    user = scheduled_session.user

    # Get current goal progress for this submission's learning goals
    core_goal_ids = [g.id for g in submission.goal.core_learning_goals]
    current_goal_progress = GoalProgress.query.filter(
        GoalProgress.user_id == user.id,
        GoalProgress.core_goal_id.in_(core_goal_ids)
    ).all() if core_goal_ids else []

    # Get agent sessions for this user and submission
    agent_sessions = AgentSession.query.filter(
        AgentSession.user_id == user.id,
        AgentSession.submission_id == submission.id
    ).order_by(AgentSession.created_at.desc()).all()

    # Get anatomy conversations (already scoped to submission)
    conversations = submission.anatomy_conversations.order_by(
        AnatomyConversation.created_at.desc()
    ).all()

    return render_template('admin/scheduled_session_detail.html',
                           scheduled_session=scheduled_session,
                           submission=submission,
                           user=user,
                           current_goal_progress=current_goal_progress,
                           agent_sessions=agent_sessions,
                           conversations=conversations)


@admin_bp.route('/scheduled-sessions/<int:session_id>/complete', methods=['POST'])
@require_instructor
def complete_scheduled_session(session_id):
    """Mark a scheduled session as completed."""
    scheduled_session = ScheduledSession.query.get_or_404(session_id)

    scheduled_session.session_completed_at = datetime.utcnow()
    scheduled_session.notes = request.form.get('notes', '').strip() or None

    db.session.commit()
    flash('Session marked as completed.', 'success')
    return redirect(url_for('admin.dashboard'))
