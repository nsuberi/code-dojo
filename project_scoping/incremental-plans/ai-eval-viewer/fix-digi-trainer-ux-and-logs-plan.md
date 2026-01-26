# Plan: Fix Digi-Trainer Topic Selection 500 Errors

## Problem Summary

When clicking a topic gem in the Digi-Trainer UI, users get 500 errors. The root cause is that when `focus_goal_id` is provided and matches a goal, `_focus_on_goal()` returns a response dict missing critical fields that the frontend expects.

## Current Logging Status

**No explicit logging is configured.** Flask's development server outputs to the terminal where `./start.sh` runs. To see 500 errors:
- Watch the terminal running `./start.sh`
- Errors and tracebacks appear in stdout/stderr

## Part 1: Add App Logging (for future debugging)

**File:** `app.py` (add after imports, before app creation)

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler('app.log')  # File output
    ]
)
logger = logging.getLogger(__name__)
```

This creates `app.log` in the project root with all debug messages.

---

## Part 2: Fix the 500 Error Root Cause

**Return value mismatch between `_focus_on_goal()` and `start_session()`:**

1. **Normal flow** (`start_session` without focus_goal_id) returns:
   ```python
   return {
       'session_id': self.session.id,      # ← Frontend NEEDS this
       'opening_message': welcome,          # ← Frontend NEEDS this
       'goals': goals,
       'engagement': engagement,
       'can_request_instructor': ...
   }
   ```

2. **Topic click flow** (`_focus_on_goal` called from line 139) returns:
   ```python
   return {
       'response': response,               # ← Wrong key name!
       'current_goal': goal,
       'engagement': ...
   }
   # MISSING: session_id, opening_message, goals
   ```

3. **Frontend expectations** (`review-tab.js:100-110`):
   ```javascript
   if (data.session_id) {  // Never set → voice init fails
       this.digiTrainerSessionId = data.session_id;
   }
   if (data.opening_message) {  // Never set → no message shown
       this.addMessage('assistant', data.opening_message);
   }
   ```

**Result:** When clicking a topic gem:
- No session_id stored → subsequent API calls fail with 500
- No opening_message → user sees nothing or fallback message
- The `response` field exists but frontend doesn't read it

## Solution

Modify `start_session()` to wrap the `_focus_on_goal()` result with the missing fields.

**File:** `services/articulation_harness.py` (lines 130-139)

**Before:**
```python
# If focus_goal_id provided, immediately focus on that specific goal
if focus_goal_id:
    # Convert to int - frontend sends string from dataset attribute
    try:
        focus_goal_id = int(focus_goal_id)
    except (TypeError, ValueError):
        pass  # Keep as-is if conversion fails
    for i, goal in enumerate(goals):
        if goal['id'] == focus_goal_id:
            return self._focus_on_goal(goals, i, introduce=True)
```

**After:**
```python
# If focus_goal_id provided, immediately focus on that specific goal
if focus_goal_id:
    # Convert to int - frontend sends string from dataset attribute
    try:
        focus_goal_id = int(focus_goal_id)
    except (TypeError, ValueError):
        pass  # Keep as-is if conversion fails
    for i, goal in enumerate(goals):
        if goal['id'] == focus_goal_id:
            result = self._focus_on_goal(goals, i, introduce=True)
            # Add fields expected by frontend
            result['session_id'] = self.session.id
            result['opening_message'] = result.get('response')
            result['goals'] = goals
            result['can_request_instructor'] = result['engagement']['can_request_instructor']
            return result
```

## Files to Modify

| File | Change |
|------|--------|
| `app.py` | Add logging configuration (after imports) |
| `services/articulation_harness.py` | Wrap `_focus_on_goal()` result with missing fields (lines 138-139) |

## Verification

1. **Manual UI Test:**
   - Navigate to a submission with the Review tab
   - Click on any topic gem (e.g., "Authentication Decorator Pattern")
   - Verify the initial message says "Let's explore **[Topic Name]**"
   - Verify you can type a response and it processes successfully
   - Check browser console for no 500 errors

2. **Python Test:**
   ```bash
   python3 -c "
   from app import app, db
   from services.articulation_harness import ArticulationHarness
   from models.submission import Submission

   with app.app_context():
       submission = Submission.query.first()
       harness = ArticulationHarness(submission.id, submission.user_id)
       result = harness.start_session(focus_goal_id='1')
       print('session_id:', result.get('session_id'))
       print('opening_message present:', bool(result.get('opening_message')))
   "
   ```

3. **Existing Tests:**
   ```bash
   pytest tests/test_articulation_traces.py -v
   pytest tests/test_sensei_unlock_manual.py -v
   ```

4. **Check Logs (after logging is added):**
   ```bash
   tail -f app.log  # Watch live logs
   # Or check terminal output where ./start.sh is running
   ```
