# Fix: Scheduled Sessions Display & Admin Errors

## Issues to Fix

1. **Admin "View Details" error**: `AttributeError: type object 'AnatomyConversation' has no attribute 'user_id'`
2. **Conversations not loading**: Same root cause - invalid filter
3. **Gems resetting to grey**: Template checks `progress.passed`/`progress.engaged` which don't exist
4. **No scheduled session indicator**: Student doesn't see they already scheduled
5. **My Account page**: Should show upcoming scheduled sessions

## Root Cause Analysis

### Issue 1 & 2: AnatomyConversation has no user_id
In `routes/admin.py:188-190`:
```python
conversations = submission.anatomy_conversations.filter(
    AnatomyConversation.user_id == user.id  # ERROR: user_id doesn't exist!
).order_by(...)
```

`AnatomyConversation` links to users via `submission.user_id`, not directly. The filter is unnecessary since conversations are already scoped to the submission.

### Issue 3: Gems resetting - Wrong attribute checks
In `templates/modules/goal.html:554-560`:
```html
{% if progress and progress.passed %}passed  <!-- WRONG: 'passed' is not an attribute -->
{% elif progress and progress.engaged %}engaged  <!-- WRONG: 'engaged' is not an attribute -->
```

The `GoalProgress` model has `status` as a string field ('locked', 'in_progress', 'engaged', 'passed'), not boolean `passed`/`engaged` attributes. The template checks always fail, showing all gems as locked.

## Implementation Plan

### 1. Fix `routes/admin.py` - Remove invalid filter

**Line 187-190** - Change:
```python
conversations = submission.anatomy_conversations.filter(
    AnatomyConversation.user_id == user.id
).order_by(AnatomyConversation.created_at.desc()).all()
```
To:
```python
conversations = submission.anatomy_conversations.order_by(
    AnatomyConversation.created_at.desc()
).all()
```

### 2. Fix `templates/modules/goal.html` - Correct gem status checks

**Line 554** - Fix gem class assignment:
```html
<!-- Change from: -->
<div class="gem-item {% if progress and progress.passed %}passed{% elif progress and progress.engaged %}engaged{% else %}locked{% endif %}"

<!-- To: -->
<div class="gem-item {% if progress and progress.status == 'passed' %}passed{% elif progress and progress.status == 'engaged' %}engaged{% else %}locked{% endif %}"
```

**Lines 557-560** - Fix gem icon display:
```html
<!-- Change from: -->
{% if progress and progress.passed %}💎
{% elif progress and progress.engaged %}🔵

<!-- To: -->
{% if progress and progress.status == 'passed' %}💎
{% elif progress and progress.status == 'engaged' %}🔵
```

**Line 633-634** - Fix gems_engaged count:
```html
<!-- Change from: -->
{% set gems_engaged = goal_progress | selectattr('engaged', 'equalto', true) | list | length %}

<!-- To: -->
{% set gems_engaged = goal_progress | selectattr('status', 'equalto', 'engaged') | list | length %}
{% set gems_passed = goal_progress | selectattr('status', 'equalto', 'passed') | list | length %}
{% set total_engaged = gems_engaged + gems_passed %}
```

Then check `total_engaged >= 1` instead of `gems_engaged >= 1`.

### 3. Update `routes/modules.py` - Pass scheduled session to template

Add import:
```python
from models.scheduled_session import ScheduledSession
```

In `goal_detail()`, after getting `latest_submission`, add query:
```python
# Get any pending scheduled session for this submission
scheduled_session = None
if latest_submission:
    scheduled_session = ScheduledSession.query.filter(
        ScheduledSession.submission_id == latest_submission.id,
        ScheduledSession.user_id == current_user.id,
        ScheduledSession.session_completed_at.is_(None)
    ).order_by(ScheduledSession.scheduled_at.desc()).first()
```

Pass to template:
```python
scheduled_session=scheduled_session
```

### 4. Update `templates/modules/goal.html` - Show scheduled indicator

**In Sensei Session section (around line 631-665)**, add conditional when session already scheduled:

```html
{% if scheduled_session %}
<div class="sensei-scheduled">
    <svg><!-- calendar icon --></svg>
    <div>
        <p><strong>Session Scheduled</strong></p>
        <p>You have a sensei session scheduled for {{ scheduled_session.scheduled_at.strftime('%B %d, %Y at %H:%M') }}.</p>
        <a href="{{ url_for('scheduling.book', submission_id=latest_submission.id) }}" class="btn btn-secondary">View Booking</a>
    </div>
</div>
{% elif total_engaged >= 1 %}
<!-- existing unlocked content -->
{% else %}
<!-- existing locked content -->
{% endif %}
```

### 5. Update `routes/auth.py` - Add scheduled sessions to account page

Add import:
```python
from models.scheduled_session import ScheduledSession
```

Update `account()`:
```python
scheduled_sessions = ScheduledSession.query.filter(
    ScheduledSession.user_id == current_user.id,
    ScheduledSession.session_completed_at.is_(None)
).order_by(ScheduledSession.scheduled_at.desc()).all()

return render_template('account.html',
                       submissions=submissions,
                       scheduled_sessions=scheduled_sessions)
```

### 6. Update `templates/account.html` - Add scheduled sessions section

After account info section, add:
```html
{% if scheduled_sessions %}
<section class="scheduled-sessions">
    <h2>Upcoming Sensei Sessions</h2>
    <table class="table">
        <thead>
            <tr>
                <th>Challenge</th>
                <th>Scheduled</th>
                <th>Status</th>
                <th>Action</th>
            </tr>
        </thead>
        <tbody>
            {% for session in scheduled_sessions %}
            <tr>
                <td>{{ session.submission.goal.title }}</td>
                <td>{{ session.scheduled_at.strftime('%B %d, %Y at %H:%M') }}</td>
                <td><span class="badge badge-info">Pending</span></td>
                <td>
                    <a href="{{ url_for('modules.goal_detail', module_id=session.submission.goal.module_id, goal_id=session.submission.goal_id) }}#tab-review" class="btn btn-small">View</a>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</section>
{% endif %}
```

## Files to Modify

| File | Change |
|------|--------|
| `routes/admin.py` | Remove invalid user_id filter (line 188-190) |
| `templates/modules/goal.html` | Fix gem status checks (lines 554, 557-560, 633-634) + add scheduled indicator |
| `routes/modules.py` | Query and pass scheduled_session |
| `routes/auth.py` | Query and pass scheduled_sessions |
| `templates/account.html` | Add upcoming sessions section |

## Verification

1. **Admin errors**: Go to `/admin` → Click "View Details" on a scheduled session → Should load without error
2. **Conversations**: Click "Conversations" button → Should display conversations
3. **Gems displaying correctly**: Navigate to review tab → Gems should show proper status (💎 for passed, 🔵 for engaged)
4. **Scheduled indicator**: As student with scheduled session → Review tab shows "Session Scheduled" with date
5. **My Account**: Go to `/auth/account` → Should see "Upcoming Sensei Sessions" section
