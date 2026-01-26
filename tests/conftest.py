"""
Shared pytest fixtures for Code Dojo tests.

Includes fixtures for:
- LangSmith tracing enablement
- Rate limit delay between tests
- Test data creation for articulation harness tests
"""

import pytest
import os
import time
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
    """Create a test client with in-memory database."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()


@pytest.fixture
def langsmith_enabled():
    """Enable LangSmith tracing for this test (uses separate test project).

    Traces will appear in the 'code-dojo-tests' project to isolate
    test traces from production traces.
    """
    # Store original values
    original_tracing = os.environ.get("LANGCHAIN_TRACING_V2")
    original_project = os.environ.get("LANGCHAIN_PROJECT")
    original_background = os.environ.get("LANGCHAIN_TRACING_BACKGROUND")

    # Enable tracing for tests
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = os.getenv('LANGSMITH_API_KEY', os.getenv('LANGCHAIN_API_KEY', ''))
    os.environ["LANGCHAIN_PROJECT"] = "code-dojo-tests"  # Separate from production
    os.environ["LANGCHAIN_TRACING_BACKGROUND"] = "true"  # Async to avoid blocking

    yield

    # Restore original values
    if original_tracing is not None:
        os.environ["LANGCHAIN_TRACING_V2"] = original_tracing
    elif "LANGCHAIN_TRACING_V2" in os.environ:
        del os.environ["LANGCHAIN_TRACING_V2"]

    if original_project is not None:
        os.environ["LANGCHAIN_PROJECT"] = original_project
    elif "LANGCHAIN_PROJECT" in os.environ:
        del os.environ["LANGCHAIN_PROJECT"]

    if original_background is not None:
        os.environ["LANGCHAIN_TRACING_BACKGROUND"] = original_background
    elif "LANGCHAIN_TRACING_BACKGROUND" in os.environ:
        del os.environ["LANGCHAIN_TRACING_BACKGROUND"]


@pytest.fixture(autouse=True)
def rate_limit_delay():
    """Add delay between tests to avoid LangSmith rate limits.

    This fixture runs automatically after each test.
    """
    yield
    time.sleep(1)  # 1 second delay after each test


@pytest.fixture
def articulation_test_data(client):
    """Create test data for articulation harness tests.

    Creates:
    - A test user
    - A learning module (Flask API Security)
    - A learning goal (Flask API Authentication)
    - Core learning goals with detailed rubric items
    - A submission with PR context

    Yields a dict with references to all created objects.
    """
    with app.app_context():
        # Create user
        user = User.create(
            email='articulation_test@test.com',
            password='testpass123',
            role='student'
        )

        # Create module
        module = LearningModule(
            title='Flask API Security',
            description='Learn API authentication patterns in Flask',
            order=1
        )
        db.session.add(module)
        db.session.flush()

        # Create goal with detailed challenge
        goal = LearningGoal(
            module_id=module.id,
            title='Flask API Authentication',
            challenge_md='''# Implement Secure API Authentication

Your task is to implement secure API authentication for a Flask snippet manager.

## Requirements
1. Use Flask-Login for session management
2. Implement password hashing
3. Create @login_required decorator protection
4. Write tests for authentication flows
''',
            order=1
        )
        db.session.add(goal)
        db.session.flush()

        # Create detailed rubric for core learning goals
        auth_decorator_rubric = {
            "items": [
                {
                    "id": "auth-decorator-usage",
                    "criterion": "Uses @login_required decorator for protected routes",
                    "pass_indicators": [
                        "mentions @login_required decorator",
                        "explains how it protects routes",
                        "understands authentication check mechanism"
                    ],
                    "socratic_hints": [
                        "How do you prevent unauthorized access to certain routes?",
                        "What happens when someone tries to access a protected route without logging in?",
                        "Where does the decorator redirect unauthenticated users?"
                    ]
                }
            ]
        }

        password_hashing_rubric = {
            "items": [
                {
                    "id": "password-hashing",
                    "criterion": "Implements password hashing with salt",
                    "pass_indicators": [
                        "mentions hashing function (pbkdf2, bcrypt, argon2)",
                        "explains purpose of salt",
                        "understands why plaintext storage is dangerous"
                    ],
                    "socratic_hints": [
                        "How do you store passwords securely?",
                        "What prevents attackers from using rainbow tables?",
                        "Why don't we just store the password directly?"
                    ]
                }
            ]
        }

        session_management_rubric = {
            "items": [
                {
                    "id": "session-management",
                    "criterion": "Manages user sessions correctly",
                    "pass_indicators": [
                        "explains login_user function",
                        "understands session lifecycle",
                        "knows how logout works"
                    ],
                    "socratic_hints": [
                        "How does Flask-Login track who is logged in?",
                        "What happens when a user calls login_user()?",
                        "How do you properly end a user's session?"
                    ]
                }
            ]
        }

        test_coverage_rubric = {
            "items": [
                {
                    "id": "test-coverage",
                    "criterion": "Tests authentication flows",
                    "pass_indicators": [
                        "tests protected endpoints",
                        "verifies 401 for unauthenticated requests",
                        "uses test client properly"
                    ],
                    "socratic_hints": [
                        "How do you test that authentication is working?",
                        "What should happen when an unauthenticated user accesses a protected route?",
                        "How do you simulate a logged-in user in tests?"
                    ]
                }
            ]
        }

        # Create core learning goals
        core_goals = []

        core_goal_1 = CoreLearningGoal(
            learning_goal_id=goal.id,
            title='Route Protection with Decorators',
            description='Understanding how to protect Flask routes using @login_required',
            rubric_json=json.dumps(auth_decorator_rubric),
            order_index=0,
            gem_color='blue',
            certification_days=90
        )
        db.session.add(core_goal_1)
        core_goals.append(core_goal_1)

        core_goal_2 = CoreLearningGoal(
            learning_goal_id=goal.id,
            title='Password Security',
            description='Implementing secure password storage with hashing and salting',
            rubric_json=json.dumps(password_hashing_rubric),
            order_index=1,
            gem_color='green',
            certification_days=90
        )
        db.session.add(core_goal_2)
        core_goals.append(core_goal_2)

        core_goal_3 = CoreLearningGoal(
            learning_goal_id=goal.id,
            title='Session Management',
            description='Managing user sessions with Flask-Login',
            rubric_json=json.dumps(session_management_rubric),
            order_index=2,
            gem_color='purple',
            certification_days=90
        )
        db.session.add(core_goal_3)
        core_goals.append(core_goal_3)

        core_goal_4 = CoreLearningGoal(
            learning_goal_id=goal.id,
            title='Authentication Testing',
            description='Writing tests for authentication flows',
            rubric_json=json.dumps(test_coverage_rubric),
            order_index=3,
            gem_color='yellow',
            certification_days=90
        )
        db.session.add(core_goal_4)
        core_goals.append(core_goal_4)

        db.session.flush()

        # Create submission (represents PR submission)
        submission = Submission(
            user_id=user.id,
            goal_id=goal.id,
            pr_url='https://github.com/nsuberi/snippet-manager-starter/pull/1',
            pr_number=1,
            pr_title='Implement authentication',
            pr_state='open',
            status='submitted'
        )
        db.session.add(submission)
        db.session.commit()

        yield {
            'user': user,
            'module': module,
            'goal': goal,
            'core_goals': core_goals,
            'submission': submission
        }

        # Cleanup is handled by the db.drop_all() in the client fixture
