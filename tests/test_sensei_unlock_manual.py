"""
Manual test script to verify digi-trainer engagement and sensei unlock flow.

Run with: pytest tests/test_sensei_unlock_manual.py -v -s

This script simulates a student completing articulation on 3+ goals to unlock
instructor feedback scheduling.

Key insight: "Interactions" != "Engagement"
- The 50% engagement threshold is based on COMPLETED GOALS, not individual messages
- Users must SELECT specific topics, then articulate on rubric items
- General chat without selecting topics does NOT count toward engagement
"""

import pytest
import json
from app import app, db
from models.user import User
from models.module import LearningModule
from models.goal import LearningGoal
from models.submission import Submission
from models.core_learning_goal import CoreLearningGoal
from models.goal_progress import GoalProgress
from services.articulation_harness import ArticulationHarness


# Passing responses for each rubric item - these match the pass_indicators in seed_data.py
PASSING_RESPONSES = {
    # Goal 1: Authentication Decorator Pattern
    'decorator_purpose': """
    I implemented a decorator that wraps each protected route function. The decorator
    runs before the actual route handler executes, checking the API key first. If the
    key is invalid or missing, it returns a 401 response before the route code ever
    executes. It's like a security checkpoint that validates credentials before
    allowing access to the protected area.
    """,
    'decorator_implementation': """
    My decorator is defined with an outer function that takes the wrapped function as
    an argument. Inside, I have an inner function that does the actual validation. I
    used functools.wraps to preserve the original function's name and docstring. The
    inner function checks the X-API-Key header - if valid, it calls and returns the
    original function's result. If invalid, it returns a 401 JSON error response.
    """,

    # Goal 2: API Key Extraction and Validation
    'key_extraction': """
    I extract the API key from the X-API-Key header using request.headers.get('X-API-Key').
    This returns None if the header is missing, which I then check for. If there's no
    header at all, I return a 401 with a message saying authentication is required.
    """,
    'key_validation': """
    I compare the extracted key against the valid key stored in an environment variable.
    For security, I use secrets.compare_digest() instead of a simple == comparison to
    prevent timing attacks. If the comparison fails, I return 401 Unauthorized. The
    valid keys are stored in environment variables, never hardcoded in the source code.
    """,

    # Goal 3: HTTP Response Codes and Error Handling
    'status_codes': """
    I return 401 Unauthorized when authentication fails. 401 tells the client that
    credentials are missing or invalid. This is different from 403 Forbidden, which
    means the credentials are valid but the user doesn't have permission for this
    specific resource.
    """,
    'error_messages': """
    My error response is a JSON object with an 'error' key containing a helpful message.
    For example: {"error": "Invalid or missing API key"}. I'm careful not to reveal
    whether it was the wrong key vs missing key to avoid giving attackers clues about
    what they got right.
    """,

    # Goal 4: Route Protection Strategy
    'read_write_split': """
    I protected POST, PUT, and DELETE endpoints with the auth decorator because these
    are write operations that modify data. GET endpoints remain public because they
    only read data. This split makes sense because anyone should be able to view
    snippets, but only authenticated users should be able to create, update, or delete.
    """,
    'decorator_application': """
    I apply the @require_api_key decorator directly above each route that needs
    protection, like @app.route('/api/snippets', methods=['POST']) followed by
    @require_api_key. The order matters - Flask's route decorator should be first
    (outermost), then the auth decorator, so auth is checked before the route runs.
    """,

    # Goal 5: Security Considerations
    'key_generation': """
    I generate API keys using secrets.token_hex(32) which produces 64 hex characters.
    This uses the operating system's cryptographically secure random number generator,
    making the keys impossible to guess or predict. Using random.random() would be
    insecure because it's predictable.
    """,
    'key_storage': """
    I store API keys in environment variables loaded from a .env file. The .env file
    is in .gitignore so it never gets committed to GitHub. This way, if someone sees
    my source code, they still can't access my API because they don't have the keys.
    """,
}


class TestSenseiUnlockFlow:
    """Test the complete flow from articulation to instructor unlock."""

    @pytest.fixture
    def test_data(self, client):
        """Create test data including user, goals, and submission with 5 core learning goals."""
        with app.app_context():
            # Create user
            user = User.create(
                email='unlock_test@test.com',
                password='testpass123',
                role='student'
            )

            # Create module
            module = LearningModule(
                title='Flask API Security',
                description='Learn API authentication',
                order=1
            )
            db.session.add(module)
            db.session.flush()

            # Create goal
            goal = LearningGoal(
                module_id=module.id,
                title='Add authentication to Flask API',
                challenge_md='Implement API authentication',
                order=1
            )
            db.session.add(goal)
            db.session.flush()

            # Create 5 core learning goals (matching seed_data.py structure exactly)
            core_goals_data = [
                {
                    'title': 'Authentication Decorator Pattern',
                    'description': 'Understanding how decorators intercept and validate requests',
                    'gem_color': 'blue',
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
                },
                {
                    'title': 'API Key Extraction and Validation',
                    'description': 'How to safely extract and validate API keys from requests',
                    'gem_color': 'purple',
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
                },
                {
                    'title': 'HTTP Response Codes and Error Handling',
                    'description': 'Returning appropriate responses for authentication failures',
                    'gem_color': 'green',
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
                },
                {
                    'title': 'Route Protection Strategy',
                    'description': 'Deciding which routes need authentication',
                    'gem_color': 'orange',
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
                },
                {
                    'title': 'Security Considerations',
                    'description': 'Understanding security implications of API auth',
                    'gem_color': 'red',
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
                },
            ]

            core_goals = []
            for idx, goal_data in enumerate(core_goals_data):
                rubric = {
                    'items': goal_data['items']
                }

                core_goal = CoreLearningGoal(
                    learning_goal_id=goal.id,
                    title=goal_data['title'],
                    description=goal_data['description'],
                    rubric_json=json.dumps(rubric),
                    order_index=idx,
                    gem_color=goal_data['gem_color'],
                    certification_days=90
                )
                db.session.add(core_goal)
                core_goals.append(core_goal)

            db.session.flush()

            # Create submission
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
                'goal': goal,
                'core_goals': core_goals,
                'submission': submission
            }

    def test_complete_articulation_unlocks_instructor(self, test_data):
        """
        Simulate completing articulation on 3 goals to unlock instructor.

        This is the main test that verifies the unlock mechanism works.
        It tests the REAL issue: you must SELECT topics, not just chat.
        """
        with app.app_context():
            data = test_data

            # Refresh objects in current session
            from models.user import User
            from models.submission import Submission
            user = User.query.get(data['user'].id)
            submission = Submission.query.get(data['submission'].id)

            # Start articulation session
            harness = ArticulationHarness(
                submission_id=submission.id,
                user_id=user.id
            )
            result = harness.start_session()

            print(f"\n{'='*60}")
            print("ARTICULATION SESSION STARTED")
            print(f"{'='*60}")
            print(f"Session ID: {result['session_id']}")
            print(f"Total Goals: {result['engagement']['total']}")
            print(f"Initial can_request_instructor: {result['can_request_instructor']}")

            assert result['engagement']['total'] == 5, f"Expected 5 goals, got {result['engagement']['total']}"
            assert result['can_request_instructor'] == False, "Should not be able to request instructor initially"

            # Complete 3 goals (50% threshold = 3 out of 5)
            goals_to_complete = [0, 1, 2]  # First 3 goals

            for goal_index in goals_to_complete:
                print(f"\n{'='*60}")
                print(f"ARTICULATING ON GOAL {goal_index + 1}")
                print(f"{'='*60}")

                # KEY INSIGHT: Must SELECT the goal by number first!
                # This is what sets current_goal_index
                result = harness.process_message(str(goal_index + 1))
                print(f"Selected: {result.get('current_goal', {}).get('title', 'Unknown')}")

                # Get rubric items for this goal
                current_goal = result.get('current_goal', {})
                rubric_items = current_goal.get('rubric', {}).get('items', [])

                # Articulate on each rubric item
                for item in rubric_items:
                    item_id = item['id']
                    response_text = PASSING_RESPONSES.get(item_id, "I understand this concept well.")

                    print(f"\n  Articulating on: {item_id}")
                    result = harness.process_message(response_text)

                    # Debug: print result keys to understand flow
                    print(f"  [DEBUG] Result keys: {list(result.keys())}")
                    if result.get('error'):
                        print(f"  [DEBUG] Error: {result['error']}")

                    # Check if we moved to next item or completed goal
                    if result.get('gem_unlocked'):
                        print(f"  -> Goal completed with status: {result.get('gem_status')}")
                        break
                    elif 'attempts_remaining' in result:
                        print(f"  -> Attempts remaining: {result['attempts_remaining']}")
                    else:
                        print(f"  -> Progressed to next item")

            # Check final engagement
            engagement = harness.calculate_engagement_stats()

            print(f"\n{'='*60}")
            print("FINAL ENGAGEMENT STATS")
            print(f"{'='*60}")
            print(f"Passed: {engagement['passed']}")
            print(f"Engaged: {engagement['engaged']}")
            print(f"Valid Count: {engagement['valid_count']}")
            print(f"Engagement %: {engagement['engagement_percent']*100:.0f}%")
            print(f"Can Request Instructor: {engagement['can_request_instructor']}")

            # Assert threshold is met
            assert engagement['valid_count'] >= 3, f"Expected 3+ goals completed, got {engagement['valid_count']}"
            assert engagement['can_request_instructor'] == True, "Should be able to request instructor"

            print(f"\n{'='*60}")
            print("SUCCESS: Instructor feedback is now unlocked!")
            print(f"{'='*60}")

    def test_general_chat_does_not_count(self, test_data):
        """
        Verify that general chat WITHOUT selecting topics does NOT count toward engagement.

        This tests the likely root cause of the user's issue.
        """
        with app.app_context():
            data = test_data

            # Refresh objects in current session
            from models.user import User
            from models.submission import Submission
            user = User.query.get(data['user'].id)
            submission = Submission.query.get(data['submission'].id)

            # Start articulation session
            harness = ArticulationHarness(
                submission_id=submission.id,
                user_id=user.id
            )
            result = harness.start_session()

            print(f"\n{'='*60}")
            print("TEST: General chat does NOT count as engagement")
            print(f"{'='*60}")

            initial_engagement = result['engagement']
            print(f"Initial engagement: {initial_engagement['valid_count']}/{initial_engagement['total']}")

            # Send multiple general messages WITHOUT selecting a topic
            general_messages = [
                "Hello, I want to talk about authentication",
                "I implemented a decorator for my routes",
                "The API key is stored in environment variables",
                "I used functools.wraps in my implementation",
                "My error responses return JSON with helpful messages"
            ]

            for i, msg in enumerate(general_messages, 1):
                print(f"\n  Message {i}: {msg[:50]}...")
                result = harness.process_message(msg)
                print(f"  -> Response received (general chat)")

            # Check engagement after general chat
            final_engagement = harness.calculate_engagement_stats()

            print(f"\n{'='*60}")
            print("RESULTS AFTER GENERAL CHAT")
            print(f"{'='*60}")
            print(f"Initial valid_count: {initial_engagement['valid_count']}")
            print(f"Final valid_count: {final_engagement['valid_count']}")
            print(f"Can request instructor: {final_engagement['can_request_instructor']}")

            # Assert that engagement did NOT increase from general chat
            assert final_engagement['valid_count'] == 0, \
                f"General chat should NOT count toward engagement, but got {final_engagement['valid_count']}"
            assert final_engagement['can_request_instructor'] == False, \
                "Should NOT be able to request instructor from general chat alone"

            print(f"\n{'='*60}")
            print("CONFIRMED: General chat does NOT unlock instructor!")
            print("User must SELECT specific topics to make progress.")
            print(f"{'='*60}")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
