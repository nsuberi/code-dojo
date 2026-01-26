# Fix: Multiple Admin & Scheduling Display Issues

## Issues to Fix

1. **URL Endpoint Error**: `BuildError: Could not build url for endpoint 'scheduling.book_session'`
2. **Goal Title Not Showing**: In "Current Goal Progress" table, goal title is blank
3. **Conversations Button Not Working**: No information displays when clicking "Conversations"

---

## Issue 1: Wrong URL Endpoint

**Error**: `BuildError: Could not build url for endpoint 'scheduling.book_session' with values ['goal_id']`

**Root Cause**: Template uses wrong endpoint name and parameter:
- Uses: `url_for('scheduling.book_session', goal_id=goal.id)`
- Should be: `url_for('scheduling.book', submission_id=latest_submission.id)`

**File**: `templates/modules/goal.html`

**Fix Lines 648 and 663-664**:
```html
<!-- Line 648 - Change: -->
<a href="{{ url_for('scheduling.book_session', goal_id=goal.id) }}" class="btn btn-secondary">View Booking</a>
<!-- To: -->
<a href="{{ url_for('scheduling.book', submission_id=latest_submission.id) }}" class="btn btn-secondary">View Booking</a>

<!-- Lines 663-664 - Change: -->
<a href="{{ url_for('scheduling.book_session', goal_id=goal.id) }}" class="btn btn-primary">Schedule a Sensei Session</a>
<!-- To: -->
<a href="{{ url_for('scheduling.book', submission_id=latest_submission.id) }}" class="btn btn-primary">Schedule a Sensei Session</a>
```

---

## Issue 2: Goal Title Not Showing

**Root Cause**: Template uses wrong attribute name:
- Uses: `progress.core_goal.name`
- Should be: `progress.core_goal.title`

The `CoreLearningGoal` model has `title` attribute (not `name`).

**File**: `templates/admin/scheduled_session_detail.html`

**Fix Line 97**:
```html
<!-- Change: -->
<td>{{ progress.core_goal.name if progress.core_goal else 'Unknown' }}</td>
<!-- To: -->
<td>{{ progress.core_goal.title if progress.core_goal else 'Unknown' }}</td>
```

---

## Issue 3: Conversations Button Shows No Data - DATA IN WRONG PLACE

**Root Cause**: Two separate conversation systems exist:

1. **`AnatomyConversation`** - Old Socratic chat system via `/submissions/<id>/anatomy/chat` routes
2. **`AgentSession`** - New articulation harness via `/api/agent/.../articulation/...` routes (used by Review tab gems)

The Review tab's Digi-Trainer uses `AgentSession` (see `review-tab.js:92`). So when students engage with gems to unlock scheduling, their data goes into `AgentSession` - but the "Conversations" button only queries `AnatomyConversation`.

**Evidence**: The `scheduled_session_detail.html` already has an "Agent Sessions" section (lines 116-142) that shows `AgentSession` data. This is where the Digi-Trainer conversations are.

**Fix**: Remove the "Conversations" button since "View Details" already shows all conversation data (both Agent Sessions and Anatomy Conversations).

**File**: `templates/admin/dashboard.html`

**Remove Lines 67-68**:
```html
<a href="{{ url_for('admin.submission_conversations', submission_id=session.submission.id) }}"
   class="btn btn-small">Conversations</a>
```

---

## Files to Modify

| File | Change |
|------|--------|
| `templates/modules/goal.html` | Fix URL endpoint from `scheduling.book_session` to `scheduling.book` with `submission_id` (lines 648, 663-664) |
| `templates/admin/scheduled_session_detail.html` | Fix `core_goal.name` to `core_goal.title` (line 97) |
| `templates/admin/dashboard.html` | Remove redundant "Conversations" button (lines 67-68) |

---

## Verification

1. **URL endpoint**: Navigate to goal page with submission → Review tab → Click "Schedule a Sensei Session" → Should load without error
2. **Goal title**: Go to `/admin` → Click "View Details" on scheduled session → "Current Goal Progress" table should show goal titles
3. **Conversations**: View Details page should show "Agent Sessions" section with Digi-Trainer conversation data
