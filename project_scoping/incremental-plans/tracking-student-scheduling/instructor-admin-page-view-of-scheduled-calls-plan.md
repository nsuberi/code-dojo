# Feature: Show Scheduled Sessions on Admin Dashboard

## Overview
When a student schedules a sensei session, track it in the database and display it to instructors on the admin dashboard, including the student's digi-trainer interactions.

## Implementation

### 1. Create Model: `models/scheduled_session.py`

```python
"""Scheduled session model for tracking student scheduling requests."""

from datetime import datetime
from models import db


class ScheduledSession(db.Model):
    """Tracks when students initiate scheduling with an instructor."""

    __tablename__ = 'scheduled_sessions'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    eligibility_reason = db.Column(db.String(50))  # 'needs_work_feedback' or 'digi_trainer_engagement'
    goals_passed = db.Column(db.Integer, default=0)
    goals_engaged = db.Column(db.Integer, default=0)
    total_goals = db.Column(db.Integer, default=0)
    scheduled_at = db.Column(db.DateTime, default=datetime.utcnow)
    session_completed_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)

    submission = db.relationship('Submission', backref=db.backref('scheduled_sessions', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('scheduled_sessions', lazy='dynamic'))

    def engagement_percent(self):
        if self.total_goals == 0:
            return 0
        return round((self.goals_engaged + self.goals_passed) / self.total_goals * 100)
```

### 2. Register Model: `models/__init__.py`

Add import after line 26:
```python
from models.scheduled_session import ScheduledSession
```

### 3. Create Migration: `migrations/add_scheduled_sessions.py`

SQL to execute:
```sql
CREATE TABLE scheduled_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    eligibility_reason VARCHAR(50),
    goals_passed INTEGER DEFAULT 0,
    goals_engaged INTEGER DEFAULT 0,
    total_goals INTEGER DEFAULT 0,
    scheduled_at DATETIME NOT NULL,
    session_completed_at DATETIME,
    notes TEXT,
    FOREIGN KEY (submission_id) REFERENCES submissions (id),
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE INDEX idx_scheduled_sessions_submission ON scheduled_sessions (submission_id);
CREATE INDEX idx_scheduled_sessions_user ON scheduled_sessions (user_id);
```

### 4. Update `routes/scheduling.py`

In the `book()` function, after eligibility check passes and before rendering:
- Determine eligibility_reason ('needs_work_feedback' or 'digi_trainer_engagement')
- Calculate goals_passed, goals_engaged, total_goals from GoalProgress
- Check if already scheduled recently (within 1 hour) to avoid duplicates
- Create ScheduledSession record if not duplicate

### 5. Update `routes/admin.py`

**Add to dashboard():**
- Import ScheduledSession and GoalProgress
- Query uncompleted scheduled sessions
- Pass `scheduled_sessions` to template

**Add new route `view_scheduled_session(session_id)`:**
- Show full details including goal progress, agent sessions, and conversations
- Use `@require_instructor` decorator

**Add new route `complete_scheduled_session(session_id)` [POST]:**
- Mark session_completed_at = now
- Save optional notes
- Redirect to dashboard

### 6. Update `templates/admin/dashboard.html`

After stats cards (line 22), add:
- New stat card showing scheduled sessions count
- New "Scheduled Sessions" section with table:
  - Student email
  - Challenge name
  - Eligibility reason (badge)
  - Digi-trainer progress (X passed, Y engaged / Z total)
  - Scheduled date
  - Actions: View Details, View Conversations

### 7. Create `templates/admin/scheduled_session_detail.html`

Detail view showing:
- Session info (scheduled_at, eligibility_reason, submission link)
- Engagement stats at time of scheduling
- Current goal progress table
- Agent sessions with message previews
- Link to anatomy conversations
- Form to mark session as completed with notes

## Files to Modify/Create

| File | Action |
|------|--------|
| `models/scheduled_session.py` | Create |
| `models/__init__.py` | Add import |
| `migrations/add_scheduled_sessions.py` | Create |
| `routes/scheduling.py` | Add record creation |
| `routes/admin.py` | Add queries + 2 new routes |
| `templates/admin/dashboard.html` | Add section |
| `templates/admin/scheduled_session_detail.html` | Create |

## Implementation Sequence

1. Create `models/scheduled_session.py`
2. Update `models/__init__.py` with import
3. Create `migrations/add_scheduled_sessions.py`
4. **Run migration**: `python migrations/add_scheduled_sessions.py`
5. Update `routes/scheduling.py` to create records
6. Update `routes/admin.py` with queries and new routes
7. Update `templates/admin/dashboard.html` with scheduled sessions section
8. Create `templates/admin/scheduled_session_detail.html`

## Verification

1. Restart app
2. As student: Navigate to eligible submission → Click "Schedule a Sensei Session"
3. As admin: Go to /admin → See new "Scheduled Sessions" section
4. Click "View Details" → See student's digi-trainer engagement
5. Mark session as completed → Verify it disappears from pending list
