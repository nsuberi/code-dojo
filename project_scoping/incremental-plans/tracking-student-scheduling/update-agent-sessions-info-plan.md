# Fix Agent Sessions Display and Add Integration Tests

## Problem
In the instructor scheduled session detail view, the "Agent Sessions" section displays "Unknown" for each session title. They should show the harness type and goal title.

## Root Causes
1. **Template issue**: Line 123 references non-existent `session.session_type`
2. **Data issue**: `core_goal_id` is never set on `AgentSession` even though the column exists

## Solution Overview
1. Fix both harnesses to set `core_goal_id` when a topic is first focused
2. Update the template to display harness type + goal title
3. Add integration test verifying both planning and articulation sessions are saved correctly

---

## Part 1: Fix Harnesses to Set `core_goal_id`

### File: `services/articulation_harness.py`
In `_focus_on_goal()` (around line 374), add setting `core_goal_id` when first topic is focused:

```python
# After line 374: self.session.current_goal_index = goal_index
# Add: Set core_goal_id if not already set (first topic focused)
if self.session.core_goal_id is None:
    self.session.core_goal_id = goal['id']
```

### File: `services/planning_harness.py`
In `_start_guided_planning()` (around line 136) and `_focus_on_goal()` (around line 159):

```python
# In _start_guided_planning(), after line 136:
if self.session.core_goal_id is None:
    self.session.core_goal_id = first_goal['id']

# In _focus_on_goal(), after line 159:
if self.session.core_goal_id is None:
    self.session.core_goal_id = goal['id']
```

---

## Part 2: Template Fix

### File: `templates/admin/scheduled_session_detail.html` (line 123)

```html
<!-- FROM -->
<span class="session-type">{{ session.session_type or 'Unknown' }}</span>

<!-- TO -->
<span class="session-type">
    {{ session.harness_type | title }} - {% if session.core_goal %}{{ session.core_goal.title }}{% else %}{{ session.learning_goal.title }}{% endif %}
</span>
```

This displays:
- "Planning - Authentication Decorator Pattern" (if topic was focused)
- "Planning - Add authentication to Flask API" (if no topic focused, shows challenge title)
- "Articulation - Authentication Decorator Pattern" (when topic was selected)

---

## Part 3: Integration Test

### File: `tests/test_agent_session_display.py` (new file)

Test verifies:
1. Planning harness creates session with `harness_type='planning'`
2. User selects a topic → `core_goal_id` is set
3. PR is submitted (using existing submission in test data)
4. Articulation harness creates session with `harness_type='articulation'`
5. User engages with 2+ topics → first topic's `core_goal_id` is recorded
6. Both sessions appear in scheduled session detail view with correct titles

Test uses existing `articulation_test_data` fixture and the PR URL:
`https://github.com/nsuberi/snippet-manager-starter/pull/1`

```python
@pytest.mark.integration
def test_planning_and_articulation_sessions_display(langsmith_enabled, articulation_test_data, client):
    """Verify both planning and articulation sessions are saved with correct goal titles."""
    with app.app_context():
        data = articulation_test_data
        user = User.query.get(data['user'].id)
        goal = LearningGoal.query.get(data['goal'].id)
        submission = Submission.query.get(data['submission'].id)

        # === PLANNING SESSION ===
        planning_harness = PlanningHarness(
            learning_goal_id=goal.id,
            user_id=user.id
        )
        planning_result = planning_harness.start_session()

        # Select first topic (triggers _start_guided_planning or process_message with "1")
        planning_harness.process_message("guide me through all")
        planning_harness.process_message("I'll use a decorator pattern")
        planning_harness.end_session()

        # Verify planning session saved correctly
        planning_session = AgentSession.query.get(planning_result['session_id'])
        assert planning_session.harness_type == 'planning'
        assert planning_session.core_goal_id is not None  # Should be set now
        assert planning_session.core_goal.title == data['core_goals'][0].title

        # === ARTICULATION SESSION ===
        articulation_harness = ArticulationHarness(
            submission_id=submission.id,
            user_id=user.id
        )
        articulation_result = articulation_harness.start_session()

        # Select and engage with Topic 1
        articulation_harness.process_message("1")
        articulation_harness.process_message(PASSING_RESPONSES['decorator_purpose'])
        articulation_harness.process_message(PASSING_RESPONSES['decorator_implementation'])

        # Select and engage with Topic 2
        articulation_harness.process_message("2")
        articulation_harness.process_message(PASSING_RESPONSES['key_extraction'])
        articulation_harness.process_message(PASSING_RESPONSES['key_validation'])

        articulation_harness.end_session()

        # Verify articulation session saved correctly
        articulation_session = AgentSession.query.get(articulation_result['session_id'])
        assert articulation_session.harness_type == 'articulation'
        assert articulation_session.core_goal_id is not None
        assert articulation_session.core_goal.title == data['core_goals'][0].title  # First topic selected

        # Verify both sessions exist for this user/submission
        all_sessions = AgentSession.query.filter_by(user_id=user.id).all()
        harness_types = {s.harness_type for s in all_sessions}
        assert 'planning' in harness_types
        assert 'articulation' in harness_types
```

---

## Files to Modify
1. `services/articulation_harness.py` - Set `core_goal_id` in `_focus_on_goal()`
2. `services/planning_harness.py` - Set `core_goal_id` in `_start_guided_planning()` and `_focus_on_goal()`
3. `templates/admin/scheduled_session_detail.html` - Update line 123
4. `tests/test_agent_session_display.py` - New integration test file

---

## Verification
1. Run the new integration test:
   ```bash
   pytest tests/test_agent_session_display.py -v -s
   ```
2. Manual verification:
   - Navigate to Admin Dashboard → Scheduled Sessions
   - Click "View Details" on a session with agent sessions
   - Confirm planning sessions show "Planning - [Topic Title]"
   - Confirm articulation sessions show "Articulation - [Topic Title]"
   - Verify titles match those in "Current Goal Progress" table
