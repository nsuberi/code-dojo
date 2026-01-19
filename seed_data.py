"""
Database initialization and seed data for Code Dojo.

Run this script to create the database and populate it with:
- Sample learning module and goals
- Admin and instructor users
- Sample student users

Usage:
    python seed_data.py
    python seed_data.py --reset  # Drop and recreate all tables
    python seed_data.py --rubrics  # Add core learning goals with rubrics
"""

import sys
import json
from app import app, db
from models.user import User
from models.module import LearningModule
from models.goal import LearningGoal
from models.anatomy_topic import AnatomyTopic
from models.core_learning_goal import CoreLearningGoal


# Challenge description for the API Auth challenge
API_AUTH_CHALLENGE = """
## Challenge: Add API Authentication

The Snippet Manager API currently allows **anyone** to create, update, and delete code snippets without any authentication. This is a security vulnerability!

### Your Task

Add authentication to protect write operations (POST, PUT, DELETE) while keeping read operations (GET) public.

### Requirements

1. **Choose an approach** - You can use either:
   - **API Key Authentication** - Using an `X-API-Key` header
   - **HTTP Basic Authentication** - Using `Authorization: Basic` header

2. **Protect write operations**:
   - POST `/api/snippets` (create)
   - PUT `/api/snippets/<id>` (update)
   - DELETE `/api/snippets/<id>` (delete)

3. **Keep read operations public**:
   - GET `/api/snippets` (list all)
   - GET `/api/snippets/<id>` (get one)
   - GET `/api/languages`
   - GET `/api/tags`

4. **Return proper error responses**:
   - 401 Unauthorized when credentials are missing or invalid
   - Include helpful error message

### Getting Started

1. Fork or clone the starter repository
2. Implement your authentication solution
3. Update the tests to verify auth works
4. Submit your solution branch

### Hints

- Look at how Flask decorators work
- Consider using `functools.wraps` for your decorator
- For API keys, `secrets.token_hex(32)` generates secure random keys
- For Basic Auth, werkzeug has password hashing utilities

### Success Criteria

- All existing tests still pass (read operations work without auth)
- New tests verify auth is required for write operations
- Invalid credentials return 401 with helpful message
- Valid credentials allow write operations
"""


def seed_database():
    """Create tables and insert sample data."""
    print("Creating database tables...")
    db.create_all()

    # Check if data already exists
    if LearningModule.query.first():
        print("Database already has data. Use --reset to recreate.")
        return

    print("Creating learning module...")

    # Create the Flask API Auth module
    module = LearningModule(
        title="Flask API Authentication",
        description="Learn how to secure your Flask REST APIs with authentication. You'll implement authentication from scratch and understand the security principles behind it.",
        order=1
    )
    db.session.add(module)
    db.session.flush()  # Get the module ID

    # Create the learning goal
    goal = LearningGoal(
        module_id=module.id,
        title="Add API Key Authentication",
        video_url="https://www.youtube.com/watch?v=o-pMCoVPN_k",
        challenge_md=API_AUTH_CHALLENGE,
        starter_repo="https://github.com/nsuberi/snippet-manager-starter",
        order=1
    )
    db.session.add(goal)
    db.session.flush()  # Get the goal ID

    print("Creating anatomy topics...")

    # Create anatomy topics for the API Auth challenge
    anatomy_topics = [
        AnatomyTopic(
            goal_id=goal.id,
            name="Authentication Decorator",
            description="The decorator pattern you used to protect routes - how it intercepts requests and validates credentials before allowing access.",
            suggested_analogies="A decorator is like a security guard at a building entrance. Before anyone can enter (access the function), the guard checks their ID (validates credentials). If they pass, they're allowed in; if not, they're turned away.",
            order=1
        ),
        AnatomyTopic(
            goal_id=goal.id,
            name="API Key Validation",
            description="How your code checks if the provided API key is valid and matches expected credentials.",
            suggested_analogies="Think of API keys like a special password or VIP pass. Just like a bouncer checks if your name is on the guest list, your code checks if the provided key matches one that's been registered.",
            order=2
        ),
        AnatomyTopic(
            goal_id=goal.id,
            name="HTTP Headers",
            description="How you extract and use the X-API-Key header from incoming requests.",
            suggested_analogies="HTTP headers are like the envelope of a letter - they contain metadata about the message (who it's from, special handling instructions) separate from the actual content inside.",
            order=3
        ),
        AnatomyTopic(
            goal_id=goal.id,
            name="Error Responses",
            description="How your code returns appropriate 401 Unauthorized responses when authentication fails.",
            suggested_analogies="Error responses are like a helpful receptionist who doesn't just say 'no' but explains why you can't proceed and what you might need to do differently.",
            order=4
        ),
        AnatomyTopic(
            goal_id=goal.id,
            name="Route Protection Strategy",
            description="Your approach to deciding which routes need protection (write operations) vs which stay public (read operations).",
            suggested_analogies="This is like a museum where anyone can look at the exhibits (read), but only authorized staff can move or modify them (write). You're deciding what requires a staff badge.",
            order=5
        ),
    ]

    for topic in anatomy_topics:
        db.session.add(topic)

    print("Creating users...")

    # Create admin user
    admin = User.create(
        email="admin@codedojo.com",
        password="admin123",
        role="admin"
    )
    print(f"  Admin: admin@codedojo.com / admin123")

    # Create instructor user
    instructor = User.create(
        email="instructor@codedojo.com",
        password="instructor123",
        role="instructor"
    )
    print(f"  Instructor: instructor@codedojo.com / instructor123")

    # Create sample student users
    student1 = User.create(
        email="alice@example.com",
        password="student123",
        role="student"
    )
    print(f"  Student 1: alice@example.com / student123")

    student2 = User.create(
        email="bob@example.com",
        password="student123",
        role="student"
    )
    print(f"  Student 2: bob@example.com / student123")

    db.session.commit()

    print("\n" + "=" * 60)
    print("SEED DATA CREATED SUCCESSFULLY")
    print("=" * 60)
    print("\nTest Credentials:")
    print("  Admin:      admin@codedojo.com / admin123")
    print("  Instructor: instructor@codedojo.com / instructor123")
    print("  Student 1:  alice@example.com / student123")
    print("  Student 2:  bob@example.com / student123")
    print("\nLearning Content:")
    print(f"  Module: {module.title}")
    print(f"  Goal: {goal.title}")
    print(f"  Starter Repo: {goal.starter_repo}")
    print("=" * 60)


def reset_database():
    """Drop all tables and recreate with seed data."""
    print("Dropping all tables...")
    db.drop_all()
    seed_database()


def seed_anatomy_topics():
    """Add anatomy topics to existing goals (without resetting database)."""
    print("Seeding anatomy topics...")

    # Check if topics already exist
    if AnatomyTopic.query.first():
        print("Anatomy topics already exist. Skipping.")
        return

    # Get the first goal (API Auth challenge)
    goal = LearningGoal.query.first()
    if not goal:
        print("No learning goals found. Run seed_database() first.")
        return

    print(f"Adding anatomy topics to goal: {goal.title}")

    anatomy_topics = [
        AnatomyTopic(
            goal_id=goal.id,
            name="Authentication Decorator",
            description="The decorator pattern you used to protect routes - how it intercepts requests and validates credentials before allowing access.",
            suggested_analogies="A decorator is like a security guard at a building entrance. Before anyone can enter (access the function), the guard checks their ID (validates credentials). If they pass, they're allowed in; if not, they're turned away.",
            order=1
        ),
        AnatomyTopic(
            goal_id=goal.id,
            name="API Key Validation",
            description="How your code checks if the provided API key is valid and matches expected credentials.",
            suggested_analogies="Think of API keys like a special password or VIP pass. Just like a bouncer checks if your name is on the guest list, your code checks if the provided key matches one that's been registered.",
            order=2
        ),
        AnatomyTopic(
            goal_id=goal.id,
            name="HTTP Headers",
            description="How you extract and use the X-API-Key header from incoming requests.",
            suggested_analogies="HTTP headers are like the envelope of a letter - they contain metadata about the message (who it's from, special handling instructions) separate from the actual content inside.",
            order=3
        ),
        AnatomyTopic(
            goal_id=goal.id,
            name="Error Responses",
            description="How your code returns appropriate 401 Unauthorized responses when authentication fails.",
            suggested_analogies="Error responses are like a helpful receptionist who doesn't just say 'no' but explains why you can't proceed and what you might need to do differently.",
            order=4
        ),
        AnatomyTopic(
            goal_id=goal.id,
            name="Route Protection Strategy",
            description="Your approach to deciding which routes need protection (write operations) vs which stay public (read operations).",
            suggested_analogies="This is like a museum where anyone can look at the exhibits (read), but only authorized staff can move or modify them (write). You're deciding what requires a staff badge.",
            order=5
        ),
    ]

    for topic in anatomy_topics:
        db.session.add(topic)

    db.session.commit()
    print(f"Created {len(anatomy_topics)} anatomy topics successfully!")


def seed_core_learning_goals():
    """Add core learning goals with rubrics for the API Auth challenge."""
    print("Seeding core learning goals with rubrics...")

    # Check if already exists
    if CoreLearningGoal.query.first():
        print("Core learning goals already exist. Skipping.")
        return

    # Get the first goal (API Auth challenge)
    goal = LearningGoal.query.first()
    if not goal:
        print("No learning goals found. Run seed_database() first.")
        return

    print(f"Adding core learning goals to: {goal.title}")

    # Define core learning goals with rubrics for Flask API Auth
    core_goals = [
        {
            'title': 'Authentication Decorator Pattern',
            'description': 'Understanding how decorators intercept and validate requests',
            'gem_color': 'blue',
            'certification_days': 90,
            'order_index': 1,
            'rubric': {
                'items': [
                    {
                        'id': 'decorator_purpose',
                        'criterion': 'Understand why decorators are used for authentication',
                        'pass_indicators': [
                            'Explains that decorators wrap functions to add behavior',
                            'Describes how the decorator runs before the route handler',
                            'Uses analogy of security checkpoint or gatekeeper'
                        ],
                        'socratic_hints': [
                            'What happens when a request hits a protected route before your code runs?',
                            'How is this similar to checking IDs at a door?',
                            'Why might wrapping a function be useful instead of checking auth inside each route?'
                        ]
                    },
                    {
                        'id': 'decorator_implementation',
                        'criterion': 'Explain how the decorator is implemented',
                        'pass_indicators': [
                            'Mentions functools.wraps preserving function metadata',
                            'Describes inner function that does the validation',
                            'Explains returning the original function or error response'
                        ],
                        'socratic_hints': [
                            'Walk me through what your decorator code does line by line.',
                            'What does functools.wraps do and why did you use it?',
                            'When does your decorator let the request through vs block it?'
                        ]
                    }
                ]
            }
        },
        {
            'title': 'API Key Extraction and Validation',
            'description': 'How to safely extract and validate API keys from requests',
            'gem_color': 'purple',
            'certification_days': 90,
            'order_index': 2,
            'rubric': {
                'items': [
                    {
                        'id': 'key_extraction',
                        'criterion': 'Understand how API keys are extracted from requests',
                        'pass_indicators': [
                            'Knows API keys come from X-API-Key header',
                            'Explains using request.headers.get()',
                            'Handles case where header is missing'
                        ],
                        'socratic_hints': [
                            'Where does the API key live in an HTTP request?',
                            'What Flask method did you use to get the header value?',
                            'What happens if someone makes a request without the header?'
                        ]
                    },
                    {
                        'id': 'key_validation',
                        'criterion': 'Understand secure key validation',
                        'pass_indicators': [
                            'Compares against stored valid key(s)',
                            'Uses constant-time comparison for security (or understands why)',
                            'Explains what happens on invalid key'
                        ],
                        'socratic_hints': [
                            'How does your code check if a key is valid?',
                            'Why might simple string comparison have security issues?',
                            'Where are your valid keys stored and why there?'
                        ]
                    }
                ]
            }
        },
        {
            'title': 'HTTP Response Codes and Error Handling',
            'description': 'Returning appropriate responses for authentication failures',
            'gem_color': 'green',
            'certification_days': 90,
            'order_index': 3,
            'rubric': {
                'items': [
                    {
                        'id': 'status_codes',
                        'criterion': 'Understand appropriate HTTP status codes',
                        'pass_indicators': [
                            'Uses 401 for authentication failures',
                            'Knows 401 means Unauthorized',
                            'Distinguishes 401 from 403 Forbidden'
                        ],
                        'socratic_hints': [
                            'What status code did you return when auth fails?',
                            'What does 401 tell the client about what went wrong?',
                            'How is 401 different from 403?'
                        ]
                    },
                    {
                        'id': 'error_messages',
                        'criterion': 'Provide helpful error responses',
                        'pass_indicators': [
                            'Returns JSON error message',
                            'Message explains what went wrong',
                            'Avoids leaking sensitive information'
                        ],
                        'socratic_hints': [
                            'What does your error response body look like?',
                            'How would a developer using your API know what to fix?',
                            'Why is it important not to say which part of auth failed?'
                        ]
                    }
                ]
            }
        },
        {
            'title': 'Route Protection Strategy',
            'description': 'Deciding which routes need authentication',
            'gem_color': 'orange',
            'certification_days': 90,
            'order_index': 4,
            'rubric': {
                'items': [
                    {
                        'id': 'read_write_split',
                        'criterion': 'Understand read vs write operation protection',
                        'pass_indicators': [
                            'GET routes remain public (read)',
                            'POST/PUT/DELETE routes require auth (write)',
                            'Explains why this split makes sense'
                        ],
                        'socratic_hints': [
                            'Which HTTP methods did you protect and why?',
                            'Why keep GET public while protecting POST/PUT/DELETE?',
                            'What would happen if GET also required auth?'
                        ]
                    },
                    {
                        'id': 'decorator_application',
                        'criterion': 'Know how to apply decorator to specific routes',
                        'pass_indicators': [
                            'Uses decorator syntax @require_api_key',
                            'Applies to correct routes only',
                            'Order of decorators matters (understands stacking)'
                        ],
                        'socratic_hints': [
                            'How did you mark which routes need authentication?',
                            'Show me a route that needs auth vs one that doesn not.',
                            'If you have multiple decorators, does order matter?'
                        ]
                    }
                ]
            }
        },
        {
            'title': 'Security Considerations',
            'description': 'Understanding security implications of API auth',
            'gem_color': 'red',
            'certification_days': 60,  # Shorter certification for security topics
            'order_index': 5,
            'rubric': {
                'items': [
                    {
                        'id': 'key_generation',
                        'criterion': 'Understand secure key generation',
                        'pass_indicators': [
                            'Uses cryptographically secure random generation',
                            'Keys are long enough (32+ hex characters)',
                            'Does not use predictable patterns'
                        ],
                        'socratic_hints': [
                            'How would you generate a new API key?',
                            'Why use secrets.token_hex vs random strings?',
                            'What makes a key secure vs guessable?'
                        ]
                    },
                    {
                        'id': 'key_storage',
                        'criterion': 'Understand secure key storage',
                        'pass_indicators': [
                            'Keys stored in environment variables',
                            'Not hardcoded in source code',
                            'Understands why .env should not be committed'
                        ],
                        'socratic_hints': [
                            'Where do your API keys live in your codebase?',
                            'Why not just put them directly in the Python file?',
                            'What would happen if keys were committed to GitHub?'
                        ]
                    }
                ]
            }
        }
    ]

    for goal_data in core_goals:
        core_goal = CoreLearningGoal(
            learning_goal_id=goal.id,
            title=goal_data['title'],
            description=goal_data['description'],
            rubric_json=json.dumps(goal_data['rubric']),
            order_index=goal_data['order_index'],
            gem_color=goal_data['gem_color'],
            certification_days=goal_data['certification_days']
        )
        db.session.add(core_goal)

    db.session.commit()
    print(f"Created {len(core_goals)} core learning goals with rubrics!")


if __name__ == '__main__':
    with app.app_context():
        if len(sys.argv) > 1 and sys.argv[1] == '--reset':
            reset_database()
        elif len(sys.argv) > 1 and sys.argv[1] == '--anatomy':
            seed_anatomy_topics()
        elif len(sys.argv) > 1 and sys.argv[1] == '--rubrics':
            seed_core_learning_goals()
        else:
            seed_database()
