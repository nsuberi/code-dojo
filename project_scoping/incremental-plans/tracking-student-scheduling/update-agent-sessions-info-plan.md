# Fix Agent Sessions "Unknown" Title in Scheduled Session Detail View

## Problem
In the instructor scheduled session detail view, the "Agent Sessions" section displays "Unknown" for each session title instead of showing meaningful information about the session.

## Root Cause
The template at line 123 references a non-existent attribute:
```html
<span class="session-type">{{ session.session_type or 'Unknown' }}</span>
```

The `AgentSession` model has no `session_type` attribute. It does have:
- `harness_type` column → 'planning' or 'articulation'
- `core_goal` relationship → links to `CoreLearningGoal` which has a `title`

## Solution
Display both the harness type and the goal title:
- For planning sessions: "Planning"
- For articulation sessions: "Articulation - [Goal Title]"

## File to Modify
- `templates/admin/scheduled_session_detail.html` (line 123)

## Change
```html
<!-- FROM -->
<span class="session-type">{{ session.session_type or 'Unknown' }}</span>

<!-- TO -->
<span class="session-type">
    {{ session.harness_type | title }}{% if session.core_goal %} - {{ session.core_goal.title }}{% endif %}
</span>
```

This will display:
- "Planning" for planning harness sessions (typically no core_goal)
- "Articulation - Understanding recursion" for articulation sessions with a goal

## Verification
1. Navigate to Admin Dashboard → Scheduled Sessions
2. Click "View Details" on a scheduled session that has Agent Sessions
3. Confirm planning sessions show "Planning"
4. Confirm articulation sessions show "Articulation - [Goal Title]"
5. Verify goal titles match those in the "Current Goal Progress" table
