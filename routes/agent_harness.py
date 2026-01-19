"""API routes for agent harness (planning and articulation)."""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db
from models.submission import Submission
from models.goal import LearningGoal
from models.goal_progress import GoalProgress
from models.core_learning_goal import CoreLearningGoal
from models.agent_session import AgentSession
from services.planning_harness import PlanningHarness
from services.articulation_harness import ArticulationHarness
from services.whisper_transcription import (
    transcribe_audio,
    record_voice_offer,
    record_voice_decline,
    get_user_voice_stats
)

agent_bp = Blueprint('agent', __name__, url_prefix='/api/agent')

# Active harness instances (in production, use Redis or similar)
_active_harnesses = {}


def get_harness(session_id):
    """Get an active harness by session ID."""
    return _active_harnesses.get(session_id)


def store_harness(session_id, harness):
    """Store an active harness."""
    _active_harnesses[session_id] = harness


# ==================== Planning Endpoints ====================

@agent_bp.route('/goals/<int:goal_id>/plan/start', methods=['POST'])
@login_required
def start_planning_session(goal_id):
    """Start a new planning session for a learning goal."""
    goal = LearningGoal.query.get_or_404(goal_id)

    try:
        harness = PlanningHarness(
            learning_goal_id=goal_id,
            user_id=current_user.id
        )
        result = harness.start_session()

        if 'error' in result:
            return jsonify({'error': result['error']}), 400

        # Store harness for future requests
        store_harness(result['session_id'], harness)

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@agent_bp.route('/goals/<int:goal_id>/plan/message', methods=['POST'])
@login_required
def send_planning_message(goal_id):
    """Send a message in an existing planning session."""
    data = request.get_json()
    session_id = data.get('session_id')
    message = data.get('message')

    if not session_id or not message:
        return jsonify({'error': 'session_id and message are required'}), 400

    harness = get_harness(session_id)
    if not harness:
        # Try to reconstruct harness from session
        session = AgentSession.query.get(session_id)
        if not session or session.user_id != current_user.id:
            return jsonify({'error': 'Session not found'}), 404

        harness = PlanningHarness(
            learning_goal_id=goal_id,
            user_id=current_user.id
        )
        # Ensure session stays attached to db.session for lazy loading
        db.session.add(session)
        harness.session = session
        # Also load the plan
        from models.challenge_plan import ChallengePlan
        harness.plan = ChallengePlan.query.filter_by(
            user_id=current_user.id,
            learning_goal_id=goal_id
        ).first()
        store_harness(session_id, harness)

    try:
        result = harness.process_message(message)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@agent_bp.route('/goals/<int:goal_id>/plan/update', methods=['PUT'])
@login_required
def update_plan(goal_id):
    """Update the plan content directly."""
    data = request.get_json()
    session_id = data.get('session_id')
    content = data.get('content')

    if not session_id:
        return jsonify({'error': 'session_id is required'}), 400

    harness = get_harness(session_id)
    if not harness:
        return jsonify({'error': 'Session not found'}), 404

    try:
        result = harness.update_plan(content)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@agent_bp.route('/goals/<int:goal_id>/plan/generate', methods=['POST'])
@login_required
def generate_plan(goal_id):
    """Generate a structured plan from the conversation."""
    data = request.get_json()
    session_id = data.get('session_id')

    if not session_id:
        return jsonify({'error': 'session_id is required'}), 400

    harness = get_harness(session_id)
    if not harness:
        return jsonify({'error': 'Session not found'}), 404

    try:
        result = harness.generate_plan_from_conversation()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@agent_bp.route('/goals/<int:goal_id>/plan/export', methods=['GET'])
@login_required
def export_plan(goal_id):
    """Export the plan as markdown."""
    session_id = request.args.get('session_id')

    harness = get_harness(session_id) if session_id else None

    if not harness:
        # Create a temporary harness to export
        harness = PlanningHarness(
            learning_goal_id=goal_id,
            user_id=current_user.id
        )

    try:
        goal = LearningGoal.query.get(goal_id)
        result = harness.export_plan(challenge_title=goal.title if goal else None)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@agent_bp.route('/goals/<int:goal_id>/plan/coverage', methods=['GET'])
@login_required
def get_plan_coverage(goal_id):
    """Get the current plan coverage for a learning goal."""
    harness = PlanningHarness(
        learning_goal_id=goal_id,
        user_id=current_user.id
    )

    try:
        result = harness.evaluate_plan_coverage()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Articulation Endpoints ====================

@agent_bp.route('/submissions/<int:submission_id>/articulation/start', methods=['POST'])
@login_required
def start_articulation_session(submission_id):
    """Start a new articulation session for a submission."""
    submission = Submission.query.get_or_404(submission_id)

    if submission.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        harness = ArticulationHarness(
            submission_id=submission_id,
            user_id=current_user.id
        )

        # Get diff content if available from request
        data = request.get_json() or {}
        if data.get('diff_content'):
            harness.set_diff_content(data['diff_content'])

        result = harness.start_session()

        if 'error' in result:
            return jsonify({'error': result['error']}), 400

        # Store harness
        store_harness(result['session_id'], harness)

        return jsonify(result)

    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@agent_bp.route('/submissions/<int:submission_id>/articulation/message', methods=['POST'])
@login_required
def send_articulation_message(submission_id):
    """Send a message in an existing articulation session."""
    data = request.get_json()
    session_id = data.get('session_id')
    message = data.get('message')
    input_mode = data.get('input_mode', 'text')

    if not session_id or not message:
        return jsonify({'error': 'session_id and message are required'}), 400

    harness = get_harness(session_id)
    if not harness:
        # Try to reconstruct harness
        session = AgentSession.query.get(session_id)
        if not session or session.user_id != current_user.id:
            return jsonify({'error': 'Session not found'}), 404

        harness = ArticulationHarness(
            submission_id=submission_id,
            user_id=current_user.id
        )
        # Ensure session stays attached to db.session for lazy loading
        db.session.add(session)
        harness.session = session
        store_harness(session_id, harness)

    try:
        result = harness.process_message(message, input_mode=input_mode)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@agent_bp.route('/submissions/<int:submission_id>/articulation/voice', methods=['POST'])
@login_required
def process_voice_input(submission_id):
    """Process voice input for articulation."""
    session_id = request.form.get('session_id')

    if not session_id:
        return jsonify({'error': 'session_id is required'}), 400

    if 'audio' not in request.files:
        return jsonify({'error': 'audio file is required'}), 400

    harness = get_harness(session_id)
    if not harness:
        session = AgentSession.query.get(session_id)
        if not session or session.user_id != current_user.id:
            return jsonify({'error': 'Session not found'}), 404

        harness = ArticulationHarness(
            submission_id=submission_id,
            user_id=current_user.id
        )
        # Ensure session stays attached to db.session for lazy loading
        db.session.add(session)
        harness.session = session
        store_harness(session_id, harness)

    try:
        audio_file = request.files['audio']
        audio_data = audio_file.read()

        result = harness.process_voice_input(audio_data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Progress & Gems Endpoints ====================

@agent_bp.route('/submissions/<int:submission_id>/progress', methods=['GET'])
@login_required
def get_submission_progress(submission_id):
    """Get all goal progress and gem states for a submission."""
    submission = Submission.query.get_or_404(submission_id)

    if submission.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    harness = ArticulationHarness(
        submission_id=submission_id,
        user_id=current_user.id
    )

    try:
        progress = harness.get_all_progress()
        engagement = harness.calculate_engagement_stats()

        return jsonify({
            'progress': progress,
            'engagement': engagement
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@agent_bp.route('/goals/<int:goal_id>/progress', methods=['GET'])
@login_required
def get_goal_progress(goal_id):
    """Get progress for a specific learning goal."""
    core_goals = CoreLearningGoal.query.filter_by(learning_goal_id=goal_id).all()

    progress_list = []
    for core_goal in core_goals:
        progress = GoalProgress.query.filter_by(
            user_id=current_user.id,
            core_goal_id=core_goal.id
        ).first()

        progress_list.append({
            'core_goal': core_goal.to_dict(include_rubric=False),
            'progress': progress.to_dict() if progress else {
                'status': 'locked',
                'effective_status': 'locked',
                'is_expired': False
            }
        })

    return jsonify({'progress': progress_list})


@agent_bp.route('/submissions/<int:submission_id>/can-request-instructor', methods=['GET'])
@login_required
def can_request_instructor(submission_id):
    """Check if student can request instructor feedback."""
    submission = Submission.query.get_or_404(submission_id)

    if submission.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    harness = ArticulationHarness(
        submission_id=submission_id,
        user_id=current_user.id
    )

    engagement = harness.calculate_engagement_stats()

    return jsonify({
        'can_request': engagement['can_request_instructor'],
        'engagement': engagement
    })


@agent_bp.route('/submissions/<int:submission_id>/skip', methods=['POST'])
@login_required
def skip_to_instructor(submission_id):
    """Override to request instructor feedback early."""
    submission = Submission.query.get_or_404(submission_id)

    if submission.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json() or {}
    reason = data.get('reason', 'No reason provided')

    # Log the skip for analytics
    # In production, track this in a separate table

    return jsonify({
        'success': True,
        'message': 'Instructor feedback request allowed',
        'reason_logged': reason
    })


# ==================== Voice Input Endpoints ====================

@agent_bp.route('/voice/transcribe', methods=['POST'])
@login_required
def transcribe_voice():
    """Transcribe audio using Whisper API."""
    if 'audio' not in request.files:
        return jsonify({'error': 'audio file is required'}), 400

    try:
        audio_file = request.files['audio']
        audio_data = audio_file.read()

        result = transcribe_audio(
            audio_data,
            user_id=current_user.id,
            session_id=request.form.get('session_id')
        )

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@agent_bp.route('/voice/offer', methods=['POST'])
@login_required
def record_voice_offered():
    """Record that voice input was offered."""
    data = request.get_json() or {}
    session_id = data.get('session_id')

    record_voice_offer(current_user.id, session_id)
    return jsonify({'success': True})


@agent_bp.route('/voice/decline', methods=['POST'])
@login_required
def record_voice_declined():
    """Record that user declined voice input."""
    data = request.get_json() or {}
    session_id = data.get('session_id')

    record_voice_decline(current_user.id, session_id)
    return jsonify({'success': True})


@agent_bp.route('/voice/stats', methods=['GET'])
@login_required
def get_voice_stats():
    """Get voice input statistics for the current user."""
    stats = get_user_voice_stats(current_user.id)
    return jsonify(stats)


# ==================== Session Management ====================

@agent_bp.route('/sessions/<session_id>', methods=['GET'])
@login_required
def get_session(session_id):
    """Get session details."""
    session = AgentSession.query.get_or_404(session_id)

    if session.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    return jsonify(session.to_dict(include_messages=True))


@agent_bp.route('/sessions/<session_id>/end', methods=['POST'])
@login_required
def end_session(session_id):
    """End an active session."""
    session = AgentSession.query.get_or_404(session_id)

    if session.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    harness = get_harness(session_id)
    if harness:
        result = harness.end_session()
        # Clean up
        del _active_harnesses[session_id]
        return jsonify(result)

    # Manual session end
    from datetime import datetime
    session.status = 'completed'
    session.completed_at = datetime.utcnow()
    db.session.commit()

    return jsonify({'success': True})
