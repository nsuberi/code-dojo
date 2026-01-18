"""
Demo script to create sample submissions in Code Dojo.

This script demonstrates:
1. Alice submitting the API Key authentication solution
2. Bob submitting the HTTP Basic Auth solution
3. AI feedback being generated for both
4. Instructor reviewing both submissions
"""

from app import app, db
from models.user import User
from models.goal import LearningGoal
from models.submission import Submission
from models.ai_feedback import AIFeedback
from models.instructor_feedback import InstructorFeedback


def create_demo_submissions():
    """Create sample submissions for demonstration."""
    print("Creating demo submissions...")

    # Get users and goal
    alice = User.query.filter_by(email="alice@example.com").first()
    bob = User.query.filter_by(email="bob@example.com").first()
    instructor = User.query.filter_by(email="instructor@codedojo.com").first()
    goal = LearningGoal.query.first()

    if not all([alice, bob, instructor, goal]):
        print("Error: Required users or goal not found. Run seed_data.py first.")
        return

    # Clear existing submissions
    Submission.query.delete()
    AIFeedback.query.delete()
    InstructorFeedback.query.delete()
    db.session.commit()

    # Alice's submission - API Key Authentication
    print("\n1. Creating Alice's submission (API Key solution)...")
    alice_submission = Submission(
        user_id=alice.id,
        goal_id=goal.id,
        repo_url="https://github.com/nsuberi/snippet-manager-starter",
        branch="with-api-auth",
        status="ai_complete"
    )
    db.session.add(alice_submission)
    db.session.flush()

    # AI Feedback for Alice
    alice_ai_feedback = AIFeedback(
        submission_id=alice_submission.id,
        content="""## AI Feedback for API Key Authentication Solution

### Correctness (Excellent)

Your implementation correctly protects write operations with API key authentication:

- ✅ Added `ApiKey` model with secure key generation using `secrets.token_hex(32)`
- ✅ Created `require_api_key` decorator that validates the `X-API-Key` header
- ✅ Applied decorator to POST, PUT, DELETE endpoints
- ✅ GET endpoints remain public as required

### Code Quality (Good)

**Strengths:**
- Clean decorator pattern using `functools.wraps`
- Good separation of concerns between model and route logic
- Clear error messages in 401 responses

**Areas for improvement:**
- Consider adding rate limiting to prevent brute force attacks
- The `generate_key()` method could use a class method pattern

### Security (Good)

- ✅ 256-bit entropy for key generation is excellent
- ✅ Keys are stored in database (though not hashed - see suggestion below)
- ✅ Proper 401 responses with helpful messages

**Suggestion:** Consider hashing API keys before storage, similar to passwords. This way if the database is compromised, the actual keys aren't exposed.

### Summary

Great work! Your API key implementation is solid and follows best practices. The code is clean, well-organized, and properly secures the write endpoints while keeping read operations public.

**Recommendation:** Ready for instructor review!
"""
    )
    db.session.add(alice_ai_feedback)

    # Bob's submission - Basic Auth
    print("2. Creating Bob's submission (Basic Auth solution)...")
    bob_submission = Submission(
        user_id=bob.id,
        goal_id=goal.id,
        repo_url="https://github.com/nsuberi/snippet-manager-starter",
        branch="with-basic-auth",
        status="reviewed"
    )
    db.session.add(bob_submission)
    db.session.flush()

    # AI Feedback for Bob
    bob_ai_feedback = AIFeedback(
        submission_id=bob_submission.id,
        content="""## AI Feedback for HTTP Basic Authentication Solution

### Correctness (Excellent)

Your implementation correctly protects write operations with HTTP Basic Auth:

- ✅ Added `User` model with secure password hashing using `werkzeug.security`
- ✅ Created `require_basic_auth` decorator that parses Authorization header
- ✅ Applied decorator to POST, PUT, DELETE endpoints
- ✅ GET endpoints remain public as required
- ✅ Proper `WWW-Authenticate` header in 401 responses

### Code Quality (Excellent)

**Strengths:**
- Clean decorator pattern with proper use of `functools.wraps`
- Password hashing using industry-standard werkzeug utilities
- Comprehensive User model with `authenticate()` class method
- Good error handling for malformed headers

**Minor suggestions:**
- Consider adding `last_login_at` timestamp tracking
- Could add account lockout after failed attempts

### Security (Excellent)

- ✅ Passwords stored as hashes (never plaintext!)
- ✅ Uses werkzeug's battle-tested hashing
- ✅ Proper Base64 decoding with error handling
- ✅ `WWW-Authenticate` header follows HTTP spec
- ✅ User `is_active` flag allows account deactivation

**Note:** HTTP Basic Auth sends credentials with every request, so HTTPS is essential in production.

### Summary

Excellent implementation! Your HTTP Basic Auth solution demonstrates strong understanding of security principles. The password hashing is done correctly, error handling is comprehensive, and the code follows Python best practices.

**Recommendation:** This is production-ready code. Excellent work!
"""
    )
    db.session.add(bob_ai_feedback)

    # Instructor feedback for Bob (marking as reviewed and passed)
    bob_instructor_feedback = InstructorFeedback(
        submission_id=bob_submission.id,
        instructor_id=instructor.id,
        comment="""Great work, Bob!

Your HTTP Basic Authentication implementation shows strong understanding of:
- Security best practices (password hashing, never storing plaintext)
- Python decorators and the `functools.wraps` pattern
- HTTP authentication standards

A few things I particularly liked:
1. The `authenticate()` static method on User - clean API design
2. Proper `WWW-Authenticate` header in responses
3. Good handling of malformed Authorization headers

One suggestion for your learning: Try implementing both API Key and Basic Auth solutions and compare them. Understanding when to use each is valuable.

Keep up the excellent work!""",
        passed=True
    )
    db.session.add(bob_instructor_feedback)

    # Request instructor feedback for Alice
    alice_submission.status = "feedback_requested"

    db.session.commit()

    print("\n" + "=" * 60)
    print("DEMO SUBMISSIONS CREATED")
    print("=" * 60)
    print("\nAlice's Submission:")
    print(f"  Status: {alice_submission.status}")
    print(f"  Branch: {alice_submission.branch} (API Key solution)")
    print(f"  AI Feedback: Generated")
    print(f"  Instructor Feedback: Awaiting review")
    print("\nBob's Submission:")
    print(f"  Status: {bob_submission.status}")
    print(f"  Branch: {bob_submission.branch} (Basic Auth solution)")
    print(f"  AI Feedback: Generated")
    print(f"  Instructor Feedback: Reviewed - PASSED")
    print("=" * 60)


if __name__ == '__main__':
    with app.app_context():
        create_demo_submissions()
