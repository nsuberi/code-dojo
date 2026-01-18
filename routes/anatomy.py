"""Anatomy discussion routes for Socratic dialogue feature."""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models.submission import Submission
from models.anatomy_conversation import AnatomyConversation
from services.anatomy_analyzer import get_anatomy_menu
from services.socratic_chat import (
    start_conversation,
    send_message,
    end_conversation,
    get_conversation_history
)
from services.github import fetch_github_diff

anatomy_bp = Blueprint('anatomy', __name__, url_prefix='/submissions')


@anatomy_bp.route('/<int:submission_id>/anatomy', methods=['GET'])
@login_required
def get_anatomy_elements(submission_id):
    """
    Get the anatomy menu for a submission.
    Combines admin-configured topics with AI-detected patterns.
    """
    submission = Submission.query.get_or_404(submission_id)

    # Check access: user owns submission or is instructor/admin
    if submission.user_id != current_user.id and current_user.role not in ['instructor', 'admin']:
        return jsonify({'error': 'Access denied'}), 403

    # Get the diff content
    goal = submission.goal
    diff_content = None
    try:
        diff_content = fetch_github_diff(goal.starter_repo, submission.repo_url, submission.branch)
    except Exception:
        pass

    # Get anatomy menu
    menu_items = get_anatomy_menu(goal, diff_content)

    # Get any active conversations for this submission
    active_conversations = AnatomyConversation.query.filter_by(
        submission_id=submission_id,
        status='active'
    ).all()

    active_conv_dict = {
        conv.topic_name: conv.id for conv in active_conversations
    }

    # Mark menu items with active conversation
    for item in menu_items:
        if item['name'] in active_conv_dict:
            item['active_conversation_id'] = active_conv_dict[item['name']]
        else:
            item['active_conversation_id'] = None

    return jsonify({
        'submission_id': submission_id,
        'elements': menu_items,
    })


@anatomy_bp.route('/<int:submission_id>/anatomy/chat', methods=['POST'])
@login_required
def chat(submission_id):
    """
    Send a message or start a new conversation.

    Request body:
    - conversation_id (optional): Existing conversation ID to continue
    - message: The user's message
    - topic_id (optional): Admin topic ID for new conversation
    - topic_name (optional): Topic name for new conversation (if no topic_id)
    - topic_description (optional): Description for AI-detected topics
    - analogies (optional): Suggested analogies for AI-detected topics
    """
    submission = Submission.query.get_or_404(submission_id)

    # Check access
    if submission.user_id != current_user.id and current_user.role not in ['instructor', 'admin']:
        return jsonify({'error': 'Access denied'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request body'}), 400

    conversation_id = data.get('conversation_id')
    message = data.get('message', '').strip()

    # Get diff content for context
    goal = submission.goal
    diff_content = None
    try:
        diff_content = fetch_github_diff(goal.starter_repo, submission.repo_url, submission.branch)
    except Exception:
        pass

    # If continuing existing conversation
    if conversation_id:
        if not message:
            return jsonify({'error': 'Message is required'}), 400

        success, response = send_message(conversation_id, message, diff_content)

        if success:
            # Get updated conversation with realizations
            conv_data = get_conversation_history(conversation_id)
            return jsonify({
                'success': True,
                'response': response,
                'conversation': conv_data
            })
        else:
            return jsonify({'error': response}), 400

    # Starting new conversation
    topic_id = data.get('topic_id')
    topic_name = data.get('topic_name')
    topic_description = data.get('topic_description', '')
    analogies = data.get('analogies', '')

    if not topic_id and not topic_name:
        return jsonify({'error': 'Either topic_id or topic_name is required'}), 400

    conversation, opening_response = start_conversation(
        submission=submission,
        topic_id=topic_id,
        topic_name=topic_name,
        topic_description=topic_description,
        analogies=analogies,
        diff_content=diff_content
    )

    if conversation:
        conv_data = get_conversation_history(conversation.id)
        return jsonify({
            'success': True,
            'conversation_id': conversation.id,
            'response': opening_response,
            'conversation': conv_data
        })
    else:
        return jsonify({'error': opening_response}), 400


@anatomy_bp.route('/<int:submission_id>/anatomy/end', methods=['POST'])
@login_required
def end_chat(submission_id):
    """
    End a conversation and get the learning synthesis.

    Request body:
    - conversation_id: The conversation to end
    """
    submission = Submission.query.get_or_404(submission_id)

    # Check access
    if submission.user_id != current_user.id and current_user.role not in ['instructor', 'admin']:
        return jsonify({'error': 'Access denied'}), 403

    data = request.get_json()
    if not data or not data.get('conversation_id'):
        return jsonify({'error': 'conversation_id is required'}), 400

    conversation_id = data['conversation_id']

    # Verify conversation belongs to this submission
    conversation = AnatomyConversation.query.get(conversation_id)
    if not conversation or conversation.submission_id != submission_id:
        return jsonify({'error': 'Conversation not found'}), 404

    success, synthesis = end_conversation(conversation_id)

    if success:
        conv_data = get_conversation_history(conversation_id)
        return jsonify({
            'success': True,
            'synthesis': synthesis,
            'conversation': conv_data
        })
    else:
        return jsonify({'error': synthesis}), 400


@anatomy_bp.route('/<int:submission_id>/anatomy/conversations', methods=['GET'])
@login_required
def list_conversations(submission_id):
    """
    List all anatomy conversations for a submission.
    """
    submission = Submission.query.get_or_404(submission_id)

    # Check access
    if submission.user_id != current_user.id and current_user.role not in ['instructor', 'admin']:
        return jsonify({'error': 'Access denied'}), 403

    conversations = AnatomyConversation.query.filter_by(
        submission_id=submission_id
    ).order_by(AnatomyConversation.created_at.desc()).all()

    return jsonify({
        'submission_id': submission_id,
        'conversations': [
            conv.to_dict(include_realizations=True)
            for conv in conversations
        ]
    })


@anatomy_bp.route('/<int:submission_id>/anatomy/conversation/<conversation_id>', methods=['GET'])
@login_required
def get_conversation(submission_id, conversation_id):
    """
    Get a specific conversation with full history.
    """
    submission = Submission.query.get_or_404(submission_id)

    # Check access
    if submission.user_id != current_user.id and current_user.role not in ['instructor', 'admin']:
        return jsonify({'error': 'Access denied'}), 403

    conversation = AnatomyConversation.query.get(conversation_id)
    if not conversation or conversation.submission_id != submission_id:
        return jsonify({'error': 'Conversation not found'}), 404

    return jsonify({
        'success': True,
        'conversation': conversation.to_dict(include_messages=True, include_realizations=True)
    })
