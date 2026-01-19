"""Integration tests for agent harness."""

import pytest
import json
from app import app, db
from models.user import User
from models.module import LearningModule
from models.goal import LearningGoal
from models.submission import Submission
from models.core_learning_goal import CoreLearningGoal
from models.goal_progress import GoalProgress
from models.agent_session import AgentSession


@pytest.fixture
def client():
    """Create a test client."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()


def test_core_learning_goal_rubric(client):
    """Test that rubric JSON is properly parsed."""
    with app.app_context():
        # Create module and goal
        module = LearningModule(title='Test', description='Test', order=1)
        db.session.add(module)
        db.session.flush()

        goal = LearningGoal(
            module_id=module.id,
            title='Test Goal',
            challenge_md='Test',
            order=1
        )
        db.session.add(goal)
        db.session.flush()

        rubric = {
            'items': [
                {
                    'id': 'test_item_1',
                    'criterion': 'Test criterion 1',
                    'pass_indicators': ['Indicator 1', 'Indicator 2'],
                    'socratic_hints': ['Hint 1', 'Hint 2']
                }
            ]
        }

        core_goal = CoreLearningGoal(
            learning_goal_id=goal.id,
            title='Test Core Goal',
            description='Test description',
            rubric_json=json.dumps(rubric),
            order_index=1,
            gem_color='blue',
            certification_days=90
        )
        db.session.add(core_goal)
        db.session.commit()

        # Retrieve and test - query by ID to avoid conflicts with seeded data
        retrieved = CoreLearningGoal.query.get(core_goal.id)
        assert retrieved is not None

        parsed_rubric = retrieved.get_rubric()
        assert 'items' in parsed_rubric
        assert len(parsed_rubric['items']) == 1
        assert parsed_rubric['items'][0]['id'] == 'test_item_1'


def test_goal_progress_creation(client):
    """Test that goal progress records are created correctly."""
    with app.app_context():
        # Create user
        user = User.create(email='test@example.com', password='testpass', role='student')

        # Create module and goal
        module = LearningModule(title='Test', description='Test', order=1)
        db.session.add(module)
        db.session.flush()

        goal = LearningGoal(
            module_id=module.id,
            title='Test Goal',
            challenge_md='Test',
            order=1
        )
        db.session.add(goal)
        db.session.flush()

        core_goal = CoreLearningGoal(
            learning_goal_id=goal.id,
            title='Test Core Goal',
            description='Test',
            rubric_json='{"items":[]}',
            order_index=1
        )
        db.session.add(core_goal)
        db.session.commit()

        # Create progress
        progress = GoalProgress(
            user_id=user.id,
            learning_goal_id=goal.id,
            core_goal_id=core_goal.id,
            status='in_progress'
        )
        db.session.add(progress)
        db.session.commit()

        # Verify
        retrieved = GoalProgress.query.filter_by(
            user_id=user.id,
            core_goal_id=core_goal.id
        ).first()

        assert retrieved is not None
        assert retrieved.status == 'in_progress'
        assert not retrieved.is_expired()


def test_goal_progress_expiration(client):
    """Test that goal progress expiration works."""
    from datetime import datetime, timedelta

    with app.app_context():
        # Setup
        user = User.create(email='expiry@test.com', password='testpass', role='student')

        module = LearningModule(title='Test', description='Test', order=1)
        db.session.add(module)
        db.session.flush()

        goal = LearningGoal(module_id=module.id, title='Test', challenge_md='Test', order=1)
        db.session.add(goal)
        db.session.flush()

        core_goal = CoreLearningGoal(
            learning_goal_id=goal.id,
            title='Test',
            description='Test',
            rubric_json='{"items":[]}',
            order_index=1,
            certification_days=90
        )
        db.session.add(core_goal)
        db.session.commit()

        # Create progress
        progress = GoalProgress(
            user_id=user.id,
            learning_goal_id=goal.id,
            core_goal_id=core_goal.id,
            status='passed'
        )
        db.session.add(progress)
        db.session.commit()

        # Set expiration in the past
        progress.expires_at = datetime.utcnow() - timedelta(days=1)
        db.session.commit()

        assert progress.is_expired()
        assert progress.get_effective_status() == 'expired'
        assert not progress.can_unlock_instructor()


def test_goal_progress_rubric_results(client):
    """Test rubric results tracking."""
    with app.app_context():
        # Setup
        user = User.create(email='rubric@test.com', password='testpass', role='student')

        module = LearningModule(title='Test', description='Test', order=1)
        db.session.add(module)
        db.session.flush()

        goal = LearningGoal(module_id=module.id, title='Test', challenge_md='Test', order=1)
        db.session.add(goal)
        db.session.flush()

        core_goal = CoreLearningGoal(
            learning_goal_id=goal.id,
            title='Test',
            description='Test',
            rubric_json='{"items":[{"id":"test_item_1"}]}',
            order_index=1
        )
        db.session.add(core_goal)
        db.session.commit()

        # Create progress
        progress = GoalProgress(
            user_id=user.id,
            learning_goal_id=goal.id,
            core_goal_id=core_goal.id,
            status='in_progress'
        )
        db.session.add(progress)
        db.session.commit()

        # Mark an item as passed
        progress.mark_item_passed('test_item_1', 'Student response', 'Good understanding')
        db.session.commit()

        results = progress.get_rubric_results()
        assert results['pass_count'] == 1
        assert len(results['items']) == 1
        assert results['items'][0]['status'] == 'passed'


def test_agent_session_creation(client):
    """Test agent session creation."""
    import uuid

    with app.app_context():
        # Setup
        user = User.create(email='session@test.com', password='testpass', role='student')

        module = LearningModule(title='Test', description='Test', order=1)
        db.session.add(module)
        db.session.flush()

        goal = LearningGoal(module_id=module.id, title='Test', challenge_md='Test', order=1)
        db.session.add(goal)
        db.session.commit()

        # Create session
        session = AgentSession(
            id=str(uuid.uuid4()),
            user_id=user.id,
            learning_goal_id=goal.id,
            harness_type='articulation',
            context='post_submission',
            status='active',
            total_goals=3
        )
        db.session.add(session)
        db.session.commit()

        retrieved = AgentSession.query.get(session.id)
        assert retrieved is not None
        assert retrieved.harness_type == 'articulation'
        assert retrieved.calculate_engagement_percent() == 0


def test_agent_session_engagement_calculation(client):
    """Test engagement percentage calculation."""
    import uuid

    with app.app_context():
        # Setup
        user = User.create(email='engage@test.com', password='testpass', role='student')

        module = LearningModule(title='Test', description='Test', order=1)
        db.session.add(module)
        db.session.flush()

        goal = LearningGoal(module_id=module.id, title='Test', challenge_md='Test', order=1)
        db.session.add(goal)
        db.session.commit()

        session = AgentSession(
            id=str(uuid.uuid4()),
            user_id=user.id,
            learning_goal_id=goal.id,
            harness_type='articulation',
            context='post_submission',
            status='active',
            total_goals=4,
            goals_passed=1,
            goals_engaged=1
        )
        db.session.add(session)
        db.session.commit()

        # 2/4 = 50%
        assert session.calculate_engagement_percent() == 0.5
        assert session.can_request_instructor()


def test_instructor_unlock_threshold(client):
    """Test instructor feedback gating logic."""
    from routes.submissions import check_instructor_unlock_threshold

    with app.app_context():
        # Create test data
        module = LearningModule(title='Test', description='Test', order=1)
        db.session.add(module)
        db.session.flush()

        goal = LearningGoal(
            module_id=module.id,
            title='Test Goal',
            challenge_md='Test',
            order=1
        )
        db.session.add(goal)
        db.session.flush()

        # Create 4 core goals
        for i in range(4):
            core_goal = CoreLearningGoal(
                learning_goal_id=goal.id,
                title=f'Core Goal {i+1}',
                description='Test',
                rubric_json='{"items":[]}',
                order_index=i
            )
            db.session.add(core_goal)

        user = User.create(email='threshold@test.com', password='test123', role='student')
        db.session.commit()

        # Initially, threshold not met (0/4)
        can_unlock, stats = check_instructor_unlock_threshold(user.id, goal.id)
        assert not can_unlock
        assert stats['valid'] == 0
        assert stats['total'] == 4

        # Add progress for 2 goals (50%)
        core_goals = CoreLearningGoal.query.filter_by(learning_goal_id=goal.id).all()
        for i, cg in enumerate(core_goals[:2]):
            progress = GoalProgress(
                user_id=user.id,
                learning_goal_id=goal.id,
                core_goal_id=cg.id,
                status='passed' if i == 0 else 'engaged'
            )
            db.session.add(progress)
        db.session.commit()

        # Now threshold should be met (2/4 = 50%)
        can_unlock, stats = check_instructor_unlock_threshold(user.id, goal.id)
        assert can_unlock
        assert stats['valid'] == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
