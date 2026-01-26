"""
Integration test for agent session display in scheduled session detail view.

Verifies that:
1. Planning and articulation harnesses correctly set harness_type
2. core_goal_id is set when first topic is focused
3. Both session types appear correctly in the scheduled session detail view

Run with: pytest tests/test_agent_session_display.py -v -s
"""

import pytest
from app import app, db
from models.user import User
from models.goal import LearningGoal
from models.submission import Submission
from models.agent_session import AgentSession
from services.articulation_harness import ArticulationHarness
from services.planning_harness import PlanningHarness


# Passing responses for rubric items (from test_sensei_unlock_manual.py)
PASSING_RESPONSES = {
    # Goal 1: Route Protection with Decorators
    'auth-decorator-usage': """
    I implemented a decorator that wraps each protected route function. The decorator
    runs before the actual route handler executes, checking the API key first. If the
    key is invalid or missing, it returns a 401 response before the route code ever
    executes. It's like a security checkpoint that validates credentials before
    allowing access to the protected area.
    """,
}


class TestAgentSessionDisplay:
    """Test that planning and articulation sessions are saved with correct goal titles."""

    @pytest.mark.integration
    def test_planning_session_sets_core_goal_id(self, langsmith_enabled, articulation_test_data, client):
        """Verify planning session sets core_goal_id when topic is focused."""
        with app.app_context():
            data = articulation_test_data
            user = User.query.get(data['user'].id)
            goal = LearningGoal.query.get(data['goal'].id)

            # Start planning session
            planning_harness = PlanningHarness(
                learning_goal_id=goal.id,
                user_id=user.id
            )
            planning_result = planning_harness.start_session()

            print(f"\n{'='*60}")
            print("PLANNING SESSION STARTED")
            print(f"{'='*60}")
            print(f"Session ID: {planning_result['session_id']}")

            # Verify initial state - core_goal_id should be None
            planning_session = AgentSession.query.get(planning_result['session_id'])
            assert planning_session.harness_type == 'planning'
            assert planning_session.core_goal_id is None, "core_goal_id should be None before topic selection"

            # Select first topic via "guide me" mode (triggers _start_guided_planning)
            result = planning_harness.process_message("guide me through all")
            print(f"After 'guide me': current_goal_index = {planning_harness.session.current_goal_index}")

            # Refresh session from DB
            db.session.refresh(planning_session)

            # Verify core_goal_id is now set
            assert planning_session.core_goal_id is not None, "core_goal_id should be set after topic selection"
            assert planning_session.core_goal.title == data['core_goals'][0].title

            print(f"core_goal_id set to: {planning_session.core_goal_id}")
            print(f"core_goal title: {planning_session.core_goal.title}")

            # End session
            planning_harness.end_session()

            print(f"\n{'='*60}")
            print("SUCCESS: Planning session correctly sets core_goal_id")
            print(f"{'='*60}")

    @pytest.mark.integration
    def test_articulation_session_sets_core_goal_id(self, langsmith_enabled, articulation_test_data, client):
        """Verify articulation session sets core_goal_id when topic is focused."""
        with app.app_context():
            data = articulation_test_data
            user = User.query.get(data['user'].id)
            submission = Submission.query.get(data['submission'].id)

            # Start articulation session
            articulation_harness = ArticulationHarness(
                submission_id=submission.id,
                user_id=user.id
            )
            articulation_result = articulation_harness.start_session()

            print(f"\n{'='*60}")
            print("ARTICULATION SESSION STARTED")
            print(f"{'='*60}")
            print(f"Session ID: {articulation_result['session_id']}")

            # Verify initial state - core_goal_id should be None
            articulation_session = AgentSession.query.get(articulation_result['session_id'])
            assert articulation_session.harness_type == 'articulation'
            assert articulation_session.core_goal_id is None, "core_goal_id should be None before topic selection"

            # Select Topic 1 by sending "1"
            result = articulation_harness.process_message("1")
            print(f"After selecting topic 1: current_goal = {result.get('current_goal', {}).get('title')}")

            # Refresh session from DB
            db.session.refresh(articulation_session)

            # Verify core_goal_id is now set
            assert articulation_session.core_goal_id is not None, "core_goal_id should be set after topic selection"
            assert articulation_session.core_goal.title == data['core_goals'][0].title

            print(f"core_goal_id set to: {articulation_session.core_goal_id}")
            print(f"core_goal title: {articulation_session.core_goal.title}")

            # End session
            articulation_harness.end_session()

            print(f"\n{'='*60}")
            print("SUCCESS: Articulation session correctly sets core_goal_id")
            print(f"{'='*60}")

    @pytest.mark.integration
    def test_planning_and_articulation_sessions_display(self, langsmith_enabled, articulation_test_data, client):
        """Verify both planning and articulation sessions are saved with correct goal titles."""
        with app.app_context():
            data = articulation_test_data
            user = User.query.get(data['user'].id)
            goal = LearningGoal.query.get(data['goal'].id)
            submission = Submission.query.get(data['submission'].id)

            print(f"\n{'='*60}")
            print("TESTING BOTH SESSION TYPES")
            print(f"{'='*60}")

            # === PLANNING SESSION ===
            planning_harness = PlanningHarness(
                learning_goal_id=goal.id,
                user_id=user.id
            )
            planning_result = planning_harness.start_session()

            # Select first topic (triggers _start_guided_planning)
            planning_harness.process_message("guide me through all")
            planning_harness.process_message("I'll use a decorator pattern")
            planning_harness.end_session()

            # Verify planning session saved correctly
            planning_session = AgentSession.query.get(planning_result['session_id'])
            assert planning_session.harness_type == 'planning'
            assert planning_session.core_goal_id is not None, "Planning session should have core_goal_id set"
            assert planning_session.core_goal.title == data['core_goals'][0].title

            print(f"Planning session: {planning_session.harness_type} - {planning_session.core_goal.title}")

            # === ARTICULATION SESSION ===
            articulation_harness = ArticulationHarness(
                submission_id=submission.id,
                user_id=user.id
            )
            articulation_result = articulation_harness.start_session()

            # Select and engage with Topic 1
            articulation_harness.process_message("1")
            articulation_harness.process_message(PASSING_RESPONSES['auth-decorator-usage'])

            articulation_harness.end_session()

            # Verify articulation session saved correctly
            articulation_session = AgentSession.query.get(articulation_result['session_id'])
            assert articulation_session.harness_type == 'articulation'
            assert articulation_session.core_goal_id is not None, "Articulation session should have core_goal_id set"
            assert articulation_session.core_goal.title == data['core_goals'][0].title  # First topic selected

            print(f"Articulation session: {articulation_session.harness_type} - {articulation_session.core_goal.title}")

            # Verify both sessions exist for this user
            all_sessions = AgentSession.query.filter_by(user_id=user.id).all()
            harness_types = {s.harness_type for s in all_sessions}
            assert 'planning' in harness_types, "Should have a planning session"
            assert 'articulation' in harness_types, "Should have an articulation session"

            print(f"\n{'='*60}")
            print("SUCCESS: Both sessions correctly display with goal titles")
            print(f"  - Planning: {planning_session.harness_type} - {planning_session.core_goal.title}")
            print(f"  - Articulation: {articulation_session.harness_type} - {articulation_session.core_goal.title}")
            print(f"{'='*60}")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
