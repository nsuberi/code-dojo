# Implementation Plan: Code Dojo Learning Platform

## Overview

A Flask-based learning platform where students can view modules, watch tutorials, submit GitHub solutions, receive AI feedback, and get instructor reviews. Basic HTML/CSS/JS frontend (no framework per constraints).

**Appetite:** 3 days using Shape-up methodology, Claude Code, and Antigravity

**Scope:** Single topic - adding API authentication to a Flask website

---

## Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Database | SQLite | Simple, no setup, fits 3-day scope |
| ORM | SQLAlchemy | Flask standard |
| Auth | Flask-Login + Werkzeug | Built-in session management |
| Templates | Jinja2 | Flask default |
| CSS | Minimal custom | No framework per constraints |
| AI Integration | Anthropic Python SDK | Direct Claude API calls |
| Video Hosting | YouTube embeds | Placeholder: https://www.youtube.com/watch?v=o-pMCoVPN_k |
| GitHub API | Public repos only | Unauthenticated, 60 req/hr limit |
| Diff Strategy | Compare to starter repo | Each challenge has starter repo URL |

---

## Data Models

### N1: User
```python
class User:
    id: int (PK)
    email: str (unique)
    password_hash: str
    role: str  # 'student', 'instructor', 'admin'
    created_at: datetime
```

### N2: LearningModule
```python
class LearningModule:
    id: int (PK)
    title: str
    description: str
    order: int
```

### N3: LearningGoal
```python
class LearningGoal:
    id: int (PK)
    module_id: int (FK -> LearningModule)
    title: str
    video_url: str  # YouTube embed URL
    challenge_md: text
    starter_repo: str  # GitHub repo URL for diff comparison
```

### N4: Submission
```python
class Submission:
    id: int (PK)
    user_id: int (FK -> User)
    goal_id: int (FK -> LearningGoal)
    repo_url: str
    branch: str
    status: str  # 'pending', 'ai_complete', 'feedback_requested', 'reviewed'
    created_at: datetime
```

### N5: AIFeedback
```python
class AIFeedback:
    id: int (PK)
    submission_id: int (FK -> Submission)
    content: text
    created_at: datetime
```

### N6: InstructorFeedback
```python
class InstructorFeedback:
    id: int (PK)
    submission_id: int (FK -> Submission)
    instructor_id: int (FK -> User)
    comment: text
    passed: bool
    created_at: datetime
```

---

## File Structure

```
code-dojo/
├── app.py                      # Flask application entry point
├── config.py                   # Configuration (DB, API keys)
├── requirements.txt            # Python dependencies
├── models/
│   ├── __init__.py
│   ├── user.py                 # N1: User model
│   ├── module.py               # N2: LearningModule model
│   ├── goal.py                 # N3: LearningGoal model
│   ├── submission.py           # N4: Submission model
│   ├── ai_feedback.py          # N5: AIFeedback model
│   └── instructor_feedback.py  # N6: InstructorFeedback model
├── routes/
│   ├── __init__.py
│   ├── auth.py                 # N7, N8, N9: Auth routes
│   ├── modules.py              # N10, N11, N12: Curriculum routes
│   ├── submissions.py          # N13-N17: Submission routes
│   └── admin.py                # N18, N19, N20: Admin/instructor routes
├── services/
│   ├── __init__.py
│   ├── github.py               # N14: fetchGitHubDiff()
│   └── ai_feedback.py          # N15: generateAIFeedback()
├── middleware/
│   ├── __init__.py
│   └── auth.py                 # N21, N22, N23: Auth middleware
├── templates/
│   ├── base.html               # Base template with nav
│   ├── home.html               # PLACE: Home
│   ├── auth/
│   │   ├── signup.html         # PLACE: Account Creation
│   │   ├── login.html          # Login modal/page
│   │   └── reset_password.html # Password reset
│   ├── account.html            # PLACE: User Account Mgmt
│   ├── modules/
│   │   ├── detail.html         # PLACE: Learning Module Detail
│   │   └── goal.html           # PLACE: Learning Goal Detail
│   ├── submissions/
│   │   ├── student_view.html   # PLACE: Submission Review (Student)
│   │   └── instructor_view.html# PLACE: Submission Review (Instructor)
│   └── admin/
│       └── dashboard.html      # PLACE: Admin Control Panel
├── static/
│   ├── css/
│   │   └── styles.css          # Basic styling
│   └── js/
│       └── main.js             # Minimal interactivity
└── seed_data.py                # Seed curriculum content
```

---

## Affordances Reference

### UI Affordances (U)

| ID | Affordance | Place |
|----|------------|-------|
| U1 | Sign up button | Home |
| U2 | Login button | Home |
| U3 | Greeting message | Home |
| U4 | Module list | Home |
| U5 | Email input | Account Creation |
| U6 | Password input | Account Creation |
| U7 | Create account button | Account Creation |
| U8 | Reset password link | User Account Mgmt |
| U9 | Submissions history | User Account Mgmt |
| U10 | Start goal button | Learning Module Detail |
| U11 | Video player | Learning Goal Detail |
| U12 | Challenge description | Learning Goal Detail |
| U13 | GitHub repo input | Learning Goal Detail |
| U14 | Branch input | Learning Goal Detail |
| U15 | Submit button | Learning Goal Detail |
| U16 | Processing indicator | Submission Review (Student) |
| U17 | AI feedback display | Submission Review (Student) |
| U18 | Request feedback button | Submission Review (Student) |
| U19 | Instructor feedback display | Submission Review (Student) |
| U20 | Pass/fail badge | Submission Review (Student) |
| U21 | Student list | Admin Control Panel |
| U22 | Submissions table | Admin Control Panel |
| U23 | Code diff viewer | Submission Review (Instructor) |
| U24 | Comment textarea | Submission Review (Instructor) |
| U25 | Pass/fail toggle | Submission Review (Instructor) |
| U26 | Save review button | Submission Review (Instructor) |

### Code Affordances (N)

| ID | Affordance | Type |
|----|------------|------|
| N1 | User | Model |
| N2 | LearningModule | Model |
| N3 | LearningGoal | Model |
| N4 | Submission | Model |
| N5 | AIFeedback | Model |
| N6 | InstructorFeedback | Model |
| N7 | createUser() | Function |
| N8 | authenticateUser() | Function |
| N9 | resetPassword() | Function |
| N10 | getModules() | Function |
| N11 | getGoalsByModule() | Function |
| N12 | getGoalDetail() | Function |
| N13 | createSubmission() | Function |
| N14 | fetchGitHubDiff() | Function |
| N15 | generateAIFeedback() | Function |
| N16 | requestInstructorFeedback() | Function |
| N17 | getSubmissionsByUser() | Function |
| N18 | getAllStudents() | Function |
| N19 | getAllSubmissions() | Function |
| N20 | saveInstructorFeedback() | Function |
| N21 | requireAuth | Middleware |
| N22 | requireAdmin | Middleware |
| N23 | requireInstructor | Middleware |

---

## Implementation Phases

### Phase 1: Foundation + Authentication

**Files to create:**
- `app.py` - Flask app initialization
- `config.py` - Configuration
- `requirements.txt` - Dependencies
- `models/__init__.py`, `models/user.py` - User model
- `routes/__init__.py`, `routes/auth.py` - Auth routes
- `middleware/__init__.py`, `middleware/auth.py` - Auth decorators
- `templates/base.html` - Base template
- `templates/home.html` - Home page
- `templates/auth/signup.html` - Registration
- `templates/auth/login.html` - Login
- `static/css/styles.css` - Basic styles

**Functions to implement:**
- N7 `createUser()` - Validate email uniqueness, hash password, insert user
- N8 `authenticateUser()` - Check credentials, create session
- N21 `requireAuth` - Decorator to protect routes

**Acceptance criteria:**
- [ ] User can register with email/password
- [ ] Duplicate email rejected with error message
- [ ] User can log in with valid credentials
- [ ] Session persists across requests
- [ ] Logged-in user sees greeting with email
- [ ] Protected routes redirect to login when not authenticated

---

### Phase 2: Curriculum Browsing

**Files to create:**
- `models/module.py` - LearningModule model
- `models/goal.py` - LearningGoal model
- `routes/modules.py` - Curriculum routes
- `templates/modules/detail.html` - Module detail page
- `templates/modules/goal.html` - Goal detail page
- `seed_data.py` - Seed Flask API auth curriculum

**Functions to implement:**
- N10 `getModules()` - Return all modules ordered
- N11 `getGoalsByModule(module_id)` - Return goals for module
- N12 `getGoalDetail(goal_id)` - Return goal with video/challenge

**Seed data:**
- One module: "Flask API Authentication"
- One goal: "Add API Key Authentication"
- Video URL: `https://www.youtube.com/watch?v=o-pMCoVPN_k`
- Challenge markdown describing the task
- Starter repo URL (to be provided)

**Acceptance criteria:**
- [ ] Home page shows list of modules
- [ ] Clicking module shows its learning goals
- [ ] Goal detail page shows YouTube video embed
- [ ] Goal detail page shows challenge description in markdown
- [ ] Submission form visible with repo URL and branch inputs

---

### Phase 3: Submission Flow

**Files to create:**
- `models/submission.py` - Submission model
- `models/ai_feedback.py` - AIFeedback model
- `routes/submissions.py` - Submission routes
- `services/__init__.py`
- `services/github.py` - GitHub API integration
- `services/ai_feedback.py` - Claude API integration
- `templates/submissions/student_view.html` - Student submission view
- `templates/account.html` - User account page

**Functions to implement:**
- N13 `createSubmission(user_id, goal_id, repo_url, branch)` - Create submission record
- N14 `fetchGitHubDiff(starter_repo, student_repo, branch)` - Get diff via GitHub API
- N15 `generateAIFeedback(submission_id, diff, challenge)` - Send to Claude, store result
- N16 `requestInstructorFeedback(submission_id)` - Update status
- N17 `getSubmissionsByUser(user_id)` - Return user's submissions

**GitHub API integration:**
```
GET https://api.github.com/repos/{owner}/{repo}/compare/{base}...{head}
```
Compare starter repo default branch to student's repo/branch.

**Claude API integration:**
```python
prompt = f"""Review this code submission for the following challenge:

{challenge_description}

Here is the diff showing what the student changed from the starter code:

{diff_content}

Provide feedback on:
1. Correctness - Does it solve the challenge?
2. Code quality - Is it well-structured?
3. Security - Any vulnerabilities introduced?
"""
```

**Acceptance criteria:**
- [ ] Student can submit GitHub repo URL and branch
- [ ] System fetches diff from GitHub API
- [ ] Processing indicator shown while AI generates feedback
- [ ] AI feedback displayed after processing
- [ ] Student can request instructor feedback
- [ ] Student can view their submission history on account page

---

### Phase 4: Instructor Review

**Files to create:**
- `models/instructor_feedback.py` - InstructorFeedback model
- `routes/admin.py` - Admin/instructor routes
- `templates/submissions/instructor_view.html` - Instructor review page

**Functions to implement:**
- N20 `saveInstructorFeedback(submission_id, instructor_id, comment, passed)` - Store review
- N23 `requireInstructor` - Decorator for instructor-only routes

**Acceptance criteria:**
- [ ] Instructor can view submission with code diff
- [ ] Instructor can see AI feedback for context
- [ ] Instructor can add text comment
- [ ] Instructor can set pass/fail
- [ ] Student sees instructor feedback on their submission view

---

### Phase 5: Admin Dashboard

**Files to create:**
- `templates/admin/dashboard.html` - Admin dashboard

**Functions to implement:**
- N18 `getAllStudents()` - Return all non-admin users
- N19 `getAllSubmissions()` - Return all submissions with status info
- N22 `requireAdmin` - Decorator for admin-only routes

**Acceptance criteria:**
- [ ] Admin can view list of all student accounts
- [ ] Admin can view all submissions with status (pending, reviewed, etc.)
- [ ] Admin can see which submissions have feedback requested
- [ ] Admin can click through to instructor review view

---

## Wiring Diagram Summary

```
┌─ Home ─────────────────────────────────────────────────┐
│  U1 "Sign up" ─→ Account Creation                      │
│  U2 "Login" ─→ N8 authenticateUser()                   │
│  N10 getModules() ─→ U4 module list                    │
└────────────────────────────────────────────────────────┘
         │
         ▼
┌─ Learning Module Detail ───────────────────────────────┐
│  N11 getGoalsByModule() ─→ goal list                   │
│  Click goal ─→ Learning Goal Detail                    │
└────────────────────────────────────────────────────────┘
         │
         ▼
┌─ Learning Goal Detail ─────────────────────────────────┐
│  N12 getGoalDetail() ─→ U11 video + U12 challenge      │
│  U15 "Submit" ─→ N13 createSubmission()                │
│                    └─→ Submission Review (Student)     │
└────────────────────────────────────────────────────────┘
         │
         ▼
┌─ Submission Review (Student) ──────────────────────────┐
│  N14 fetchGitHubDiff() ─→ N15 generateAIFeedback()     │
│                              └─→ U17 AI feedback       │
│  U18 "Request feedback" ─→ N16 requestInstructorFeedback()
│  N6 InstructorFeedback ─→ U19 feedback + U20 badge     │
└────────────────────────────────────────────────────────┘
         │
         ▼
┌─ Submission Review (Instructor) ───────────────────────┐
│  N14 fetchGitHubDiff() ─→ U23 code diff viewer         │
│  U26 "Save review" ─→ N20 saveInstructorFeedback()     │
└────────────────────────────────────────────────────────┘
```

---

## Dependencies (requirements.txt)

```
flask>=3.0.0
flask-sqlalchemy>=3.1.0
flask-login>=0.6.0
werkzeug>=3.0.0
anthropic>=0.18.0
requests>=2.31.0
python-dotenv>=1.0.0
markdown>=3.5.0
```

---

## Environment Variables

```
FLASK_SECRET_KEY=<random-secret>
ANTHROPIC_API_KEY=<your-api-key>
DATABASE_URL=sqlite:///code_dojo.db
```

---

## Notes & Technical Debt

Per the project pitch, we acknowledge but do not solve:
- Database migrations (using SQLite with create_all for demo)
- Production deployment hardening
- Rate limiting on GitHub API (60 req/hr unauthenticated)
- Email delivery for password reset (stub for demo)
