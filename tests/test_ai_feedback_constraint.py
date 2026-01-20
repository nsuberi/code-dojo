"""Test for AIFeedback unique constraint fix."""

import pytest
from models import db
from models.submission import Submission
from models.ai_feedback import AIFeedback
from models.goal import LearningGoal
from models.module import Module
from models.user import User
from routes.submissions import get_or_create_ai_feedback


def test_get_or_create_ai_feedback_creates_new(app, client):
    """Test that get_or_create_ai_feedback creates a new record when none exists."""
    with app.app_context():
        # Create test user
        user = User(username='testuser', email='test@example.com')
        user.set_password('password')
        db.session.add(user)

        # Create test module and goal
        module = Module(title='Test Module', description='Test')
        db.session.add(module)
        db.session.flush()

        goal = LearningGoal(
            module_id=module.id,
            title='Test Goal',
            challenge_md='Test challenge',
            starter_repo='test/repo'
        )
        db.session.add(goal)
        db.session.flush()

        # Create test submission
        submission = Submission(
            user_id=user.id,
            goal_id=goal.id,
            pr_url='https://github.com/test/repo/pull/1',
            pr_number=1,
            pr_title='Test PR',
            pr_state='open',
            status='pending'
        )
        db.session.add(submission)
        db.session.commit()

        # Test: get_or_create should create new
        ai_feedback, created = get_or_create_ai_feedback(submission.id)

        assert created is True
        assert ai_feedback.submission_id == submission.id

        # Save to database
        db.session.add(ai_feedback)
        db.session.commit()

        # Verify only one exists
        count = AIFeedback.query.filter_by(submission_id=submission.id).count()
        assert count == 1


def test_get_or_create_ai_feedback_returns_existing(app, client):
    """Test that get_or_create_ai_feedback returns existing record."""
    with app.app_context():
        # Create test user
        user = User(username='testuser2', email='test2@example.com')
        user.set_password('password')
        db.session.add(user)

        # Create test module and goal
        module = Module(title='Test Module 2', description='Test')
        db.session.add(module)
        db.session.flush()

        goal = LearningGoal(
            module_id=module.id,
            title='Test Goal 2',
            challenge_md='Test challenge',
            starter_repo='test/repo2'
        )
        db.session.add(goal)
        db.session.flush()

        # Create test submission
        submission = Submission(
            user_id=user.id,
            goal_id=goal.id,
            pr_url='https://github.com/test/repo/pull/2',
            pr_number=2,
            pr_title='Test PR 2',
            pr_state='open',
            status='pending'
        )
        db.session.add(submission)
        db.session.commit()

        # Create initial AIFeedback
        initial_feedback = AIFeedback(
            submission_id=submission.id,
            content='Initial feedback'
        )
        db.session.add(initial_feedback)
        db.session.commit()
        initial_id = initial_feedback.id

        # Test: get_or_create should return existing
        ai_feedback, created = get_or_create_ai_feedback(submission.id)

        assert created is False
        assert ai_feedback.submission_id == submission.id
        assert ai_feedback.id == initial_id
        assert ai_feedback.content == 'Initial feedback'

        # Verify still only one exists
        count = AIFeedback.query.filter_by(submission_id=submission.id).count()
        assert count == 1


def test_no_duplicate_on_multiple_calls(app, client):
    """Test that multiple calls don't create duplicates."""
    with app.app_context():
        # Create test user
        user = User(username='testuser3', email='test3@example.com')
        user.set_password('password')
        db.session.add(user)

        # Create test module and goal
        module = Module(title='Test Module 3', description='Test')
        db.session.add(module)
        db.session.flush()

        goal = LearningGoal(
            module_id=module.id,
            title='Test Goal 3',
            challenge_md='Test challenge',
            starter_repo='test/repo3'
        )
        db.session.add(goal)
        db.session.flush()

        # Create test submission
        submission = Submission(
            user_id=user.id,
            goal_id=goal.id,
            pr_url='https://github.com/test/repo/pull/3',
            pr_number=3,
            pr_title='Test PR 3',
            pr_state='open',
            status='pending'
        )
        db.session.add(submission)
        db.session.commit()

        # First call - creates new
        ai_feedback1, created1 = get_or_create_ai_feedback(submission.id)
        assert created1 is True
        db.session.add(ai_feedback1)
        db.session.commit()

        # Second call - returns existing
        ai_feedback2, created2 = get_or_create_ai_feedback(submission.id)
        assert created2 is False
        assert ai_feedback2.id == ai_feedback1.id

        # Third call - still returns same
        ai_feedback3, created3 = get_or_create_ai_feedback(submission.id)
        assert created3 is False
        assert ai_feedback3.id == ai_feedback1.id

        # Verify only one exists
        count = AIFeedback.query.filter_by(submission_id=submission.id).count()
        assert count == 1
