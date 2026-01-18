"""
Database initialization and seed data for Code Dojo.

Run this script to create the database and populate it with:
- Sample learning module and goals
- Admin and instructor users
- Sample student users

Usage:
    python seed_data.py
    python seed_data.py --reset  # Drop and recreate all tables
"""

import sys
from app import app, db
from models.user import User
from models.module import LearningModule
from models.goal import LearningGoal
from models.anatomy_topic import AnatomyTopic


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


if __name__ == '__main__':
    with app.app_context():
        if len(sys.argv) > 1 and sys.argv[1] == '--reset':
            reset_database()
        elif len(sys.argv) > 1 and sys.argv[1] == '--anatomy':
            seed_anatomy_topics()
        else:
            seed_database()
