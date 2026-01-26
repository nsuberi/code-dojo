"""Base class for Socratic harness implementations."""

import os
import uuid
import json
from datetime import datetime
from typing import List, Dict, Optional, TypedDict
from anthropic import Anthropic
from langsmith import traceable
from config import Config
from models import db
from models.core_learning_goal import CoreLearningGoal
from models.goal_progress import GoalProgress
from models.agent_session import AgentSession, AgentMessage
from services.socratic_chat import start_conversation, send_message, end_conversation as end_socratic_conversation

# Set up LangSmith environment variables
os.environ["LANGCHAIN_TRACING_V2"] = Config.LANGCHAIN_TRACING_V2
os.environ["LANGCHAIN_API_KEY"] = Config.LANGCHAIN_API_KEY
os.environ["LANGCHAIN_PROJECT"] = Config.LANGCHAIN_PROJECT


class AgentState(TypedDict):
    """State for agent harness."""
    session_id: str
    user_id: int
    learning_goal_id: int
    submission_id: Optional[int]
    learning_goals: List[dict]
    current_goal_index: Optional[int]
    current_rubric_item_index: int
    current_attempts: int
    active_conversation_id: Optional[str]
    agent_phase: str
    can_unlock_instructor: bool
    frustration_detected: bool
    guide_me_mode: bool
    last_assistant_message: Optional[str]
    last_student_message: Optional[str]
    last_assistant_response: Optional[str]


def format_goal_menu(goals):
    """Format learning goals as a numbered menu."""
    menu_items = []
    for i, goal in enumerate(goals, 1):
        menu_items.append(f"{i}. **{goal['title']}** - {goal['description'][:50]}...")
    return "\n".join(menu_items)


def parse_topic_selection(user_message, learning_goals):
    """Parse user's topic selection from their message.

    Only matches when:
    - Message is exactly a number (e.g., "1", "2")
    - Message starts with a number followed by space/punctuation (e.g., "1.", "2 -")
    - Message contains the goal title as a distinct phrase

    This prevents false matches like "401" being interpreted as topic "1".
    """
    import re

    message_lower = user_message.lower().strip()

    # Check for exact number match (message is just "1", "2", etc.)
    for i, goal in enumerate(learning_goals):
        num = str(i + 1)
        # Exact match or number at start followed by non-digit
        if message_lower == num or re.match(rf'^{num}(?:\.|,|\s|$)', message_lower):
            return i

    # Check for goal title (must be a significant portion of the message to avoid false matches)
    for i, goal in enumerate(learning_goals):
        title_lower = goal['title'].lower()
        # Title should be at least 50% of the message to count as a selection
        if title_lower in message_lower and len(title_lower) >= len(message_lower) * 0.5:
            return i

    return None


def get_remaining_goals(state):
    """Get goals that haven't been completed yet."""
    # This would check GoalProgress for the user
    return [g for i, g in enumerate(state['learning_goals']) if i != state['current_goal_index']]


def format_indicators(indicators):
    """Format pass indicators for evaluation prompt."""
    return "\n".join(f"- {indicator}" for indicator in indicators)


def evaluate_rubric_item(student_response, rubric_item, langsmith_extra=None):
    """Binary pass/fail evaluation using Claude.

    This is SEPARATE from the Socratic conversation.
    This is the agent's internal evaluation logic.

    Args:
        student_response: The student's articulation response
        rubric_item: The rubric item to evaluate against
        langsmith_extra: Optional dict with LangSmith config including:
            - metadata: dict with session_id for thread grouping
            - parent: trace headers for proper parent-child linking
    """
    from langsmith import trace

    api_key = Config.ANTHROPIC_API_KEY
    if not api_key:
        return False, "No API key configured"

    # Build metadata for LangSmith trace
    metadata = {"feature": "rubric_evaluation"}
    if langsmith_extra and "metadata" in langsmith_extra:
        metadata.update(langsmith_extra["metadata"])

    # Extract parent headers for proper trace nesting
    parent_headers = None
    if langsmith_extra and "parent" in langsmith_extra:
        parent_headers = langsmith_extra["parent"]

    # Use trace() context manager with parent headers for proper nesting
    with trace(
        name="evaluate_rubric_item",
        inputs={
            "student_response": student_response,
            "criterion": rubric_item['criterion'],
            "pass_indicators": rubric_item['pass_indicators']
        },
        metadata=metadata,
        parent=parent_headers  # Link to parent for proper nesting in LangSmith
    ) as eval_run_tree:
        prompt = f"""Evaluate if student demonstrates understanding of this criterion:

CRITERION: {rubric_item['criterion']}

PASS INDICATORS (must show at least 2 of these):
{format_indicators(rubric_item['pass_indicators'])}

STUDENT RESPONSE:
{student_response}

Evaluate objectively. Return JSON: {{"passed": true/false, "evaluation": "brief explanation"}}
Only return the JSON, nothing else."""

        try:
            client = Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )

            result = json.loads(response.content[0].text)
            eval_run_tree.outputs = {"passed": result['passed'], "evaluation": result.get('evaluation', '')}
            return result['passed'], result.get('evaluation', '')

        except Exception as e:
            eval_run_tree.outputs = {"passed": False, "error": str(e)}
            return False, f"Error evaluating: {str(e)}"


class SocraticHarnessBase:
    """Common functionality for both planning and articulation harnesses."""

    def __init__(self, learning_goal_id, user_id, submission_id=None, langsmith_project=None):
        self.learning_goal_id = learning_goal_id
        self.user_id = user_id
        self.submission_id = submission_id
        self.langsmith_project = langsmith_project or Config.LANGCHAIN_PROJECT
        self.session = None
        self.state = None

    def get_core_learning_goals(self):
        """Load all core learning goals for this learning goal."""
        goals = CoreLearningGoal.query.filter_by(
            learning_goal_id=self.learning_goal_id
        ).order_by(CoreLearningGoal.order_index).all()
        return [g.to_dict(include_rubric=True) for g in goals]

    def get_or_create_progress(self, core_goal_id):
        """Get or create a GoalProgress record for the user/goal."""
        progress = GoalProgress.query.filter_by(
            user_id=self.user_id,
            core_goal_id=core_goal_id
        ).first()

        if not progress:
            core_goal = CoreLearningGoal.query.get(core_goal_id)
            progress = GoalProgress(
                user_id=self.user_id,
                learning_goal_id=self.learning_goal_id,
                core_goal_id=core_goal_id,
                status='locked',
                created_at=datetime.utcnow()
            )
            db.session.add(progress)
            db.session.commit()

        return progress

    def update_gem_state(self, core_goal_id, status):
        """Update the gem state for a core learning goal."""
        progress = self.get_or_create_progress(core_goal_id)

        if status == 'passed':
            progress.status = 'passed'
            progress.completed_at = datetime.utcnow()
            core_goal = CoreLearningGoal.query.get(core_goal_id)
            progress.set_expiration(core_goal.certification_days)
        elif status == 'engaged':
            progress.status = 'engaged'
            core_goal = CoreLearningGoal.query.get(core_goal_id)
            progress.set_expiration(core_goal.certification_days)
        elif status == 'in_progress':
            progress.status = 'in_progress'
            if not progress.unlocked_at:
                progress.unlocked_at = datetime.utcnow()

        db.session.commit()
        return progress

    def check_negotiation_threshold(self):
        """Check if user has met the 50% engagement threshold."""
        goals = CoreLearningGoal.query.filter_by(
            learning_goal_id=self.learning_goal_id
        ).all()

        total = len(goals)
        if total == 0:
            return True

        valid_count = 0
        for goal in goals:
            progress = GoalProgress.query.filter_by(
                user_id=self.user_id,
                core_goal_id=goal.id
            ).first()
            if progress and progress.can_unlock_instructor():
                valid_count += 1

        return valid_count / total >= 0.5

    def detect_frustration(self, messages):
        """Detect user frustration from message patterns.

        Checks the last 5 messages for frustration signals. Returns True
        if any signal is found, indicating the user may need a different
        approach or wants to move on from the current topic.
        """
        frustration_signals = [
            # Original signals
            "i don't understand",
            "can we move on",
            "this is confusing",
            "skip this",
            "i give up",
            "this doesn't make sense",
            # New signals for broader detection
            "i'm lost",
            "too hard",
            "makes no sense",
            "forget it",
            "whatever",
            "just tell me",
            "i'm stuck",
            "help me",
            "i'm confused",
            "move on",
            "next topic",
        ]

        for msg in messages[-5:]:
            if any(signal in msg.lower() for signal in frustration_signals):
                return True

        return False

    def recommend_next_goal(self):
        """Recommend the next goal to explore based on progress."""
        goals = self.get_core_learning_goals()

        for i, goal in enumerate(goals):
            progress = GoalProgress.query.filter_by(
                user_id=self.user_id,
                core_goal_id=goal['id']
            ).first()

            if not progress or progress.status == 'locked':
                return i

        return None

    def create_welcome_message(self, goals):
        """Create the welcome message for the session."""
        return f"""Hello! I'm your Digi Trainer. I can help you explore {len(goals)} key learning concepts from this challenge:

{format_goal_menu(goals)}

How would you like to proceed?
1. Let me choose a topic to start with
2. Suggest a good starting point for me
3. Guide me through all of them in order"""

    def ensure_session_attached(self):
        """Ensure the session is attached to the current db.session."""
        if self.session and self.session not in db.session:
            db.session.add(self.session)

    def store_message(self, role, content, input_mode=None, voice_duration=None, metadata=None):
        """Store a message in the session."""
        if not self.session:
            return

        # Ensure session is attached for any relationships to work
        self.ensure_session_attached()

        msg = AgentMessage(
            session_id=self.session.id,
            role=role,
            content=content,
            input_mode=input_mode,
            voice_duration_seconds=voice_duration,
            metadata_json=json.dumps(metadata) if metadata else None,
            created_at=datetime.utcnow()
        )
        db.session.add(msg)
        db.session.commit()
        return msg

    def get_all_progress(self):
        """Get progress for all core learning goals."""
        goals = CoreLearningGoal.query.filter_by(
            learning_goal_id=self.learning_goal_id
        ).order_by(CoreLearningGoal.order_index).all()

        progress_list = []
        for goal in goals:
            progress = GoalProgress.query.filter_by(
                user_id=self.user_id,
                core_goal_id=goal.id
            ).first()

            progress_list.append({
                'goal': goal.to_dict(include_rubric=False),
                'progress': progress.to_dict() if progress else {
                    'status': 'locked',
                    'effective_status': 'locked',
                    'is_expired': False
                }
            })

        return progress_list

    def calculate_engagement_stats(self):
        """Calculate engagement statistics for the session."""
        progress_list = self.get_all_progress()

        total = len(progress_list)
        passed = sum(1 for p in progress_list if p['progress']['status'] == 'passed' and not p['progress']['is_expired'])
        engaged = sum(1 for p in progress_list if p['progress']['status'] == 'engaged' and not p['progress']['is_expired'])
        expired = sum(1 for p in progress_list if p['progress']['is_expired'])

        return {
            'total': total,
            'passed': passed,
            'engaged': engaged,
            'expired': expired,
            'valid_count': passed + engaged,
            'engagement_percent': (passed + engaged) / total if total > 0 else 0,
            'can_request_instructor': (passed + engaged) / total >= 0.5 if total > 0 else True
        }
