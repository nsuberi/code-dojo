# Plan: Investigate Digi-Trainer Engagement Issue and Create Test Script

## Problem Summary

The user is having more than 3 interactions with the digi-trainer but engagement isn't registering, preventing the unlock of sensei scheduling.

## Root Cause Analysis

### Key Finding: "Interactions" ≠ "Engagement"

The 50% engagement threshold is based on **completed goals**, NOT individual messages/interactions.

**How Engagement Actually Works:**

1. **Start Session** → AgentSession created with `total_goals` count (5 goals for API Auth challenge)
2. **Select a Topic** → User must explicitly select a goal by number or name
3. **Articulate on Rubric Items** → Each goal has 2 rubric items requiring articulation
4. **Evaluation** → Claude evaluates each response against pass indicators
5. **Goal Completion** → After all rubric items processed, goal marked as "passed" or "engaged"
6. **Threshold Check** → `(goals_passed + goals_engaged) / total_goals >= 0.5`

**The Likely Issue:**
- User is chatting generally without selecting specific topics
- Messages without `current_goal_index` set go to general chat, NOT rubric evaluation
- Look at `process_message()` in `articulation_harness.py:266-271`:
  ```python
  elif (selected_index := parse_topic_selection(user_message, goals)) is not None:
      result = self._focus_on_goal(goals, selected_index, introduce=True)
  elif self.session.current_goal_index is not None:
      result = self._evaluate_articulation(user_message, goals)  # ONLY HERE gets evaluated
  else:
      result = self._generate_articulation_response(...)  # Generic chat - no progress!
  ```

### Core Learning Goals for API Auth Challenge

From `seed_data.py`, there are **5 core learning goals** with **2 rubric items each**:

| Goal | Title | Rubric Items |
|------|-------|--------------|
| 1 | Authentication Decorator Pattern | decorator_purpose, decorator_implementation |
| 2 | API Key Extraction and Validation | key_extraction, key_validation |
| 3 | HTTP Response Codes and Error Handling | status_codes, error_messages |
| 4 | Route Protection Strategy | read_write_split, decorator_application |
| 5 | Security Considerations | key_generation, key_storage |

**To unlock instructor: Need 3 out of 5 goals (50%) marked as "passed" or "engaged"**

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `tests/test_sensei_unlock_manual.py` | Create | Manual test script to verify sensei unlock flow |

## Test Script Design

The test script will:
1. Create test data (user, submission, goals)
2. Start an articulation session
3. Select 3 specific goals by number
4. Provide articulation responses that should PASS the rubric evaluation
5. Verify `can_request_instructor` becomes `True`

### Messages to Pass Rubric Items

**Goal 1: Authentication Decorator Pattern**

Rubric Item: `decorator_purpose`
- Criterion: "Understand why decorators are used for authentication"
- Pass Indicators:
  - Explains that decorators wrap functions to add behavior
  - Describes how the decorator runs before the route handler
  - Uses analogy of security checkpoint or gatekeeper

**Example Passing Response:**
```
I implemented a decorator that wraps each protected route function. The decorator
runs before the actual route handler, checking the API key first. If the key is
invalid or missing, it returns a 401 response before the route code ever executes.
It's like a security checkpoint that validates credentials before allowing access
to the protected area.
```

Rubric Item: `decorator_implementation`
- Criterion: "Explain how the decorator is implemented"
- Pass Indicators:
  - Mentions functools.wraps preserving function metadata
  - Describes inner function that does the validation
  - Explains returning the original function or error response

**Example Passing Response:**
```
My decorator is defined with an outer function that takes the wrapped function as
an argument. Inside, I have an inner function that does the actual validation. I
used functools.wraps to preserve the original function's name and docstring. The
inner function checks the X-API-Key header - if valid, it calls and returns the
original function's result. If invalid, it returns a 401 JSON error response.
```

**Goal 2: API Key Extraction and Validation**

Rubric Item: `key_extraction`
**Example Passing Response:**
```
I extract the API key from the X-API-Key header using request.headers.get('X-API-Key').
This returns None if the header is missing, which I then check for. If there's no
header at all, I return a 401 with a message saying authentication is required.
```

Rubric Item: `key_validation`
**Example Passing Response:**
```
I compare the extracted key against the valid key stored in an environment variable.
For security, I use secrets.compare_digest() instead of a simple == comparison to
prevent timing attacks. If the comparison fails, I return 401 Unauthorized. The
valid keys are stored in environment variables, never hardcoded in the source code.
```

**Goal 3: HTTP Response Codes and Error Handling**

Rubric Item: `status_codes`
**Example Passing Response:**
```
I return 401 Unauthorized when authentication fails. 401 tells the client that
credentials are missing or invalid. This is different from 403 Forbidden, which
means the credentials are valid but the user doesn't have permission for this
specific resource.
```

Rubric Item: `error_messages`
**Example Passing Response:**
```
My error response is a JSON object with an 'error' key containing a helpful message.
For example: {"error": "Invalid or missing API key"}. I'm careful not to reveal
whether it was the wrong key vs missing key to avoid giving attackers clues about
what they got right.
```

## Implementation Steps

### Step 1: Create Manual Test Script

Create `tests/test_sensei_unlock_manual.py` with:
- Fixture to create test data
- Function to simulate articulation session
- Specific passing responses for each rubric item
- Assertions to verify engagement threshold met

### Step 2: Add CLI Option for Quick Testing

Add a `--test-unlock` option to run the test interactively:
```bash
python -m pytest tests/test_sensei_unlock_manual.py -v -s
```

## Test Script Code

```python
"""
Manual test script to verify digi-trainer engagement and sensei unlock flow.

Run with: pytest tests/test_sensei_unlock_manual.py -v -s

This script simulates a student completing articulation on 3+ goals to unlock
instructor feedback scheduling.
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


# Passing responses for each rubric item
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
        """Create test data including user, goals, and submission."""
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

            # Create 5 core learning goals (matching seed_data.py structure)
            core_goals_data = [
                ('Authentication Decorator Pattern', ['decorator_purpose', 'decorator_implementation']),
                ('API Key Extraction and Validation', ['key_extraction', 'key_validation']),
                ('HTTP Response Codes and Error Handling', ['status_codes', 'error_messages']),
                ('Route Protection Strategy', ['read_write_split', 'decorator_application']),
                ('Security Considerations', ['key_generation', 'key_storage']),
            ]

            core_goals = []
            for idx, (title, item_ids) in enumerate(core_goals_data):
                rubric = {
                    'items': [
                        {
                            'id': item_id,
                            'criterion': f'Test criterion for {item_id}',
                            'pass_indicators': [
                                'Explains the concept clearly',
                                'Uses appropriate terminology',
                                'Demonstrates understanding'
                            ],
                            'socratic_hints': ['Tell me more...']
                        }
                        for item_id in item_ids
                    ]
                }

                core_goal = CoreLearningGoal(
                    learning_goal_id=goal.id,
                    title=title,
                    description=f'Understanding {title.lower()}',
                    rubric_json=json.dumps(rubric),
                    order_index=idx,
                    gem_color='blue',
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
        """
        with app.app_context():
            data = test_data

            # Start articulation session
            harness = ArticulationHarness(
                submission_id=data['submission'].id,
                user_id=data['user'].id
            )
            result = harness.start_session()

            print(f"\n{'='*60}")
            print("ARTICULATION SESSION STARTED")
            print(f"{'='*60}")
            print(f"Session ID: {result['session_id']}")
            print(f"Total Goals: {result['engagement']['total']}")
            print(f"Initial can_request_instructor: {result['can_request_instructor']}")

            assert result['engagement']['total'] == 5
            assert result['can_request_instructor'] == False

            # Complete 3 goals (50% threshold)
            goals_to_complete = [0, 1, 2]  # First 3 goals

            for goal_index in goals_to_complete:
                print(f"\n{'='*60}")
                print(f"ARTICULATING ON GOAL {goal_index + 1}")
                print(f"{'='*60}")

                # Select the goal by number
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


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
```

## Configuration

- **API Mode**: Use real Claude API for rubric evaluation (requires `ANTHROPIC_API_KEY` env var)
- This proves the crafted responses actually pass the evaluation, not just mock success

## Verification Steps

After implementing:

1. **Run the test script:**
   ```bash
   cd /Users/nathansuberi/Documents/GitHub/code-dojo
   source venv/bin/activate
   pytest tests/test_sensei_unlock_manual.py -v -s
   ```

2. **Check the output shows:**
   - 3 goals completed
   - `can_request_instructor: True`
   - "SUCCESS: Instructor feedback is now unlocked!"

3. **Manual UI verification:**
   - Start a new articulation session
   - Select topic "1" (or click the gem)
   - Provide the sample passing responses
   - Verify the gem changes from ○ to 💎 or 🔵
   - After 3 goals, verify unlock message appears

## Key Insights for User

1. **You must SELECT a specific topic** - just chatting won't register engagement
2. **Each topic requires articulation** on 2 rubric items
3. **Need 3 out of 5 goals** completed to unlock instructor
4. **"Completed" means** either passed (all items correct) or engaged (attempted with 3 tries)
