# Plan: Enhanced Challenge Rubric System with Multi-Approach Feedback

## Implementation Status: COMPLETE

All sections of this plan have been implemented. Below is a summary of what was completed:

| Section | Status | Files Created/Modified |
|---------|--------|------------------------|
| 1. Challenge Description Update | DONE | `seed_data.py` - Added JWT as third option |
| 2.1 ChallengeRubric Model | DONE | `models/challenge_rubric.py` (NEW) |
| 2.2 Rubric JSON Schema | DONE | Implemented in `seed_data.py` |
| 3.1 Enhanced AIFeedback Model | DONE | `models/ai_feedback.py` - Added 4 new fields |
| 3.2 AgenticReviewService | DONE | `services/agentic_review.py` (NEW) - 8-step pipeline |
| 4. Update generate_ai_feedback | DONE | `services/ai_feedback.py` - Integrated agentic review |
| 5. Five-Tab UI Flow | DONE | `templates/modules/goal.html` - Added Review tab |
| 6. Database Migration | DONE | `models/__init__.py` updated |
| 7. Seed Data Update | DONE | `seed_data.py` - Added rubric seeding |
| 8. Files Modified | DONE | See detailed list below |
| 8a. routes/submissions.py | DONE | Now passes challenge_rubric to generate_ai_feedback |
| 8b. static/js/gems-ui.js | DONE | Updated "instructor" → "Sensei" terminology |
| 10. Goal Title Update | DONE | Changed to "Add authentication to a Flask API" |
| 12. SenseiEvaluation Model | DONE | `models/sensei_evaluation.py` (NEW) |
| 13. LearningGoal Enhancement | DONE | `models/goal.py` - Added recommendation fields |
| 14. Second Learning Goal | DONE | `seed_data.py` - Claude API + LangSmith challenge |
| 14a. Core Learning Goals (2nd) | DONE | `seed_data.py` - 5 Core Learning Goals for Claude API |
| Terminology Update | DONE | "Socratic Sensei" → "Digi-Trainer" throughout |
| Tab Reorder | DONE | Learn → Challenge → Plan → Submit → Review (Challenge moved before Plan) |
| Review Tab Aesthetics | DONE | Restructured to use `.review-harness` matching Plan tab style |

### New Files Created:
- `models/challenge_rubric.py`
- `models/sensei_evaluation.py`
- `services/agentic_review.py`
- `static/js/review-tab.js`

### Files Modified:
- `models/ai_feedback.py`
- `models/goal.py`
- `models/__init__.py`
- `services/ai_feedback.py`
- `routes/modules.py`
- `templates/modules/goal.html`
- `templates/submissions/student_view.html`
- `seed_data.py`

---

## Terminology & Learning Philosophy

| Term | Role | Analogy |
|------|------|---------|
| **Digi-Trainer** | AI coach for articulation practice | Like a wooden dummy in martial arts - build your foundation |
| **Sensei** | Human instructor for premium sessions | Like a master who responds dynamically to you |

### The Learning Journey

```
┌─────────────────────────────────────────────────────────────────────────┐
│  1. CHALLENGE        2. DIGI-TRAINER       3. SENSEI        4. NEXT    │
│  ───────────────    ────────────────      ─────────────    ──────────  │
│  Submit your        Practice your         Premium 1:1      What's your │
│  solution           articulation          session          next step?  │
│                                                                         │
│  Get AI review      "What have you        Sensei evaluates  Suggested  │
│                     learned?"             your journey      challenges │
│                                                                         │
│                     "What are your        Identifies gaps   Tailored   │
│                     questions?"           in understanding  exercises  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Copy & Tone

**Digi-Trainer Section Header**:
> "Before meeting with your Sensei, practice explaining your code. The Digi-Trainer
> helps you build the foundation—like training with a wooden dummy—so when you
> work with your Sensei, you're ready for the real thing."

**Preparing for Sensei**:
> "The Digi-Trainer gets you ready to answer: *What have you learned?* and
> *What are your questions?* This saves both you and your Sensei time, so your
> session focuses on what matters most."

**Sensei Session Section**:
> "Your Sensei is here to help you level up. They'll assess where you are in
> your learning journey, identify concepts you're still working to embody,
> and suggest your next training exercises."

**Post-Sensei Section**:
> "Based on your session, here are recommended next challenges to continue
> building your skills."

## Overview

Enhance the learning challenge system to:
1. Support challenges with multiple valid solutions (API Key, HTTP Basic Auth, JWT)
2. Generate AI feedback that recognizes the chosen approach and discusses alternatives
3. Add a 5-tab UI flow consolidating feedback on the goal page
4. Create an agentic review pipeline for deep code analysis
5. Rename "Socratic Sensei" → "Digi-Trainer" throughout the codebase
6. Add Sensei evaluation model for tracking learning journey insights
7. Add "Next Challenges" recommendation system
8. Create second learning goal (Claude API + LangSmith) to demonstrate multiple challenges

---

## 1. Challenge Description Update

**File**: `seed_data.py` (lines 25-76)

Update `API_AUTH_CHALLENGE` to include JWT as a third option:

```markdown
### Requirements

1. **Choose an approach** - You can use any of these:
   - **API Key Authentication** - Using an `X-API-Key` header
   - **HTTP Basic Authentication** - Using `Authorization: Basic` header
   - **JWT (JSON Web Token)** - Using `Authorization: Bearer` header

### Hints
...
- For JWT, consider using PyJWT library with HS256 signing
- Each approach has different tradeoffs (stateless vs simple, etc.)
```

---

## 2. Multi-Approach Rubric Design

### 2.1 New Model: `ChallengeRubric`

**New file**: `models/challenge_rubric.py`

```python
class ChallengeRubric(db.Model):
    __tablename__ = 'challenge_rubrics'

    id = db.Column(db.Integer, primary_key=True)
    learning_goal_id = db.Column(db.Integer, db.ForeignKey('learning_goals.id'), unique=True)
    title = db.Column(db.String(200), nullable=False)
    rubric_json = db.Column(db.Text, nullable=False)  # Multi-approach schema below
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### 2.2 Rubric JSON Schema (Multi-Approach)

```json
{
  "version": "1.0",
  "valid_approaches": [
    {
      "id": "api_key",
      "name": "API Key Authentication",
      "detection_patterns": ["X-API-Key", "x-api-key", "API_KEY"],
      "tradeoffs": {
        "pros": ["Simple to implement", "Easy to revoke", "No expiration handling needed"],
        "cons": ["Must be stored securely", "No built-in expiration", "Less suitable for user-facing apps"]
      }
    },
    {
      "id": "basic_auth",
      "name": "HTTP Basic Authentication",
      "detection_patterns": ["Authorization: Basic", "base64", "werkzeug.security"],
      "tradeoffs": {
        "pros": ["Standard HTTP mechanism", "Built-in browser support", "Simple for development"],
        "cons": ["Credentials sent with every request", "Must use HTTPS", "No built-in session management"]
      }
    },
    {
      "id": "jwt",
      "name": "JWT Bearer Token",
      "detection_patterns": ["Authorization: Bearer", "PyJWT", "jwt.encode", "jwt.decode"],
      "tradeoffs": {
        "pros": ["Stateless", "Self-contained claims", "Standard for modern APIs", "Built-in expiration"],
        "cons": ["Larger token size", "Cannot revoke without blacklist", "More complex implementation"]
      }
    }
  ],
  "universal_criteria": [
    {
      "id": "protects_write_ops",
      "criterion": "Protects POST, PUT, DELETE endpoints",
      "pass_indicators": ["Decorator applied to write routes", "Returns 401 without valid auth"]
    },
    {
      "id": "allows_read_ops",
      "criterion": "GET endpoints remain public",
      "pass_indicators": ["No auth decorator on GET routes", "GET requests succeed without credentials"]
    },
    {
      "id": "proper_401_response",
      "criterion": "Returns 401 with JSON error body",
      "pass_indicators": ["Status code 401", "JSON response with error message"]
    },
    {
      "id": "uses_decorator_pattern",
      "criterion": "Uses decorator pattern for auth",
      "pass_indicators": ["Defines auth decorator function", "Uses functools.wraps"]
    },
    {
      "id": "secrets_not_hardcoded",
      "criterion": "Secrets loaded from environment",
      "pass_indicators": ["Uses os.getenv or os.environ", "No literal keys in source"]
    }
  ],
  "approach_specific_criteria": {
    "api_key": [
      {"id": "header_extraction", "criterion": "Extracts key from X-API-Key header"},
      {"id": "secure_comparison", "criterion": "Uses constant-time comparison (secrets.compare_digest)"}
    ],
    "basic_auth": [
      {"id": "base64_decode", "criterion": "Properly decodes Base64 credentials"},
      {"id": "password_hash", "criterion": "Compares against hashed password, not plaintext"}
    ],
    "jwt": [
      {"id": "token_decode", "criterion": "Properly decodes and verifies JWT signature"},
      {"id": "expiration_check", "criterion": "Validates token expiration (exp claim)"},
      {"id": "claims_usage", "criterion": "Extracts and uses claims from token payload"}
    ]
  }
}
```

---

## 3. Agentic Review Pipeline

### 3.1 Enhanced `AIFeedback` Model

**File**: `models/ai_feedback.py`

Add fields:
- `detected_approach` (String) - Which approach was detected
- `evaluation_json` (Text) - Structured rubric evaluation
- `alternative_approaches_json` (Text) - Discussion of other valid solutions
- `line_references_json` (Text) - Specific line references for feedback

### 3.2 New Service: `AgenticReviewService`

**New file**: `services/agentic_review.py`

Pipeline steps (each `@traceable` for LangSmith):

1. **`_detect_approach(diff_content)`** → Returns `{approach_id, confidence, evidence_lines}`
2. **`_analyze_architecture(diff_content)`** → Returns component map with line ranges
3. **`_evaluate_universal_criteria(diff_content, rubric)`** → Evaluate approach-agnostic criteria
4. **`_evaluate_approach_criteria(diff_content, approach_id, rubric)`** → Evaluate approach-specific criteria
5. **`_evaluate_tests(diff_content)`** → Test coverage assessment
6. **`_analyze_security(diff_content, approach_id)`** → Security analysis for chosen approach
7. **`_generate_alternatives_discussion(approach_id, rubric)`** → Explain other valid approaches
8. **`_synthesize_feedback(...)`** → Consolidate into final feedback

### 3.3 Feedback Output Structure

The generated feedback will have this structure:

```markdown
# Code Review: API Authentication

## Your Approach: API Key Authentication ✓

You implemented API key authentication using the X-API-Key header pattern.
[Brief positive acknowledgment of what works well]

## What You Did Well
- [Specific praise with line references, e.g., "Line 15-23 in app.py: Clean decorator implementation"]
- ...

## Areas for Improvement
- [Issue with line reference and concrete suggestion]
- [Example of better code if applicable]

## Security Considerations
- [Security-specific feedback for chosen approach]

---

## Other Valid Approaches

### HTTP Basic Authentication
[Brief explanation of how this would work, when you'd choose it]
**Tradeoffs**: [pros/cons relevant to this challenge]

### JWT Bearer Token
[Brief explanation of how this would work, when you'd choose it]
**Tradeoffs**: [pros/cons relevant to this challenge]

---

## Key Learning Points
1. [Concept tied to core learning goal]
2. [Concept tied to core learning goal]
```

---

## 4. Update `generate_ai_feedback` Function

**File**: `services/ai_feedback.py`

```python
def generate_ai_feedback(challenge_description, diff_content, challenge_rubric=None, submission_id=None):
    """Generate AI feedback - uses agentic review when rubric available."""

    if challenge_rubric:
        from services.agentic_review import AgenticReviewService
        service = AgenticReviewService(submission_id)
        return service.run_full_review(
            challenge_md=challenge_description,
            diff_content=diff_content,
            rubric=challenge_rubric.get_rubric()
        )

    # Fallback to simple 4-point feedback for challenges without rubrics
    return _generate_simple_feedback(challenge_description, diff_content)
```

---

## 5. Five-Tab UI Flow

**File**: `templates/modules/goal.html`

### Current Tabs (4):
1. Learn
2. Plan Your Approach
3. Challenge
4. Submit

### New Tab Structure (5):
1. **Learn** - Video tutorial (existing)
2. **Challenge** - Challenge description with 3 approaches listed (existing, update content)
3. **Plan Your Approach** - Socratic planning harness (existing)
4. **Submit** - Repo URL submission (existing)
5. **Review Feedback** - NEW: Consolidate from `student_view.html`

### Review Tab Content (Consolidated from `student_view.html`):

The Review tab brings together all post-submission experiences:

#### Section 1: Submission Status
- Status badge (pending → ai_complete → feedback_requested → reviewed)
- Repo URL and branch info
- Submission timestamp

#### Section 2: AI Feedback
- Detected approach badge ("You used: API Key Authentication")
- Structured feedback with line references
- Collapsible "Other Valid Approaches" comparison table

#### Section 3: Digi-Trainer Gem-Based Review Widget

**Gems Progress Display** (from `gems-ui.js`):
```
MASTERY  💎 🔵 ⚪ ○ ○  (2/5 - engage with 1 more to unlock Sensei)
```
- 💎 = Passed (mastered)
- 🔵 = Engaged (tried, some understanding)
- ⚪ = In progress
- ○ = Locked

**Core Learning Goals Grid**:
Each gem is clickable, showing the topic title and status. Clicking opens the Digi-Trainer chat for that topic.

**Topics from CoreLearningGoals**:
1. Authentication Decorator Pattern
2. API Key Extraction and Validation
3. HTTP Response Codes and Error Handling
4. Route Protection Strategy
5. Security Considerations

**Digi-Trainer Chat Interface** (from anatomy section):
- Sidebar with discussion topics
- Chat container with Digi-Trainer avatar
- Real-time message exchange
- "End Discussion" button → triggers synthesis modal
- Voice input support (existing `voice-input.js`)

#### Section 4: Sensei Session Request

**Terminology**:
- **Digi-Trainer** = AI chat component (for gem-based articulation)
- **Sensei** = Human instructor (for live sessions)

**Unlock Condition**: Student must have:
1. Submitted a solution
2. Received AI review
3. Engaged with the Digi-Trainer (at least one gem interaction)

```
Before unlock:
┌────────────────────────────────────────────────┐
│  🔒 Sensei Session Locked                      │
│  Engage with the Digi-Trainer to unlock        │
└────────────────────────────────────────────────┘

After unlock:
┌────────────────────────────────────────────────┐
│  ✨ You can now request a session with a Sensei│
│  [Schedule a Sensei Session] button            │
└────────────────────────────────────────────────┘
```

#### Section 5: Sensei Feedback (when session completed)
- Session notes from the Sensei
- Pass/Certification badge (if applicable)
- Option to schedule another session

### JavaScript for Review Tab

**New file**: `static/js/review-tab.js`

Integrates:
- `GemsUI` class from `gems-ui.js`
- `ArticulationHarnessUI` from `articulation-harness-ui.js`
- Progress checking API calls
- Tab state management

```javascript
class ReviewTab {
    constructor(goalId, submissionId) {
        this.goalId = goalId;
        this.submissionId = submissionId;
        this.gemsUI = new GemsUI('gems-container', submissionId);
        this.digiTrainerUI = null;
    }

    async init() {
        await this.gemsUI.loadProgress();
        this.gemsUI.onGoalClick = (goalId) => this.startDigiTrainer(goalId);
        this.checkSenseiUnlock();
    }

    async startDigiTrainer(coreGoalId) {
        // Start Digi-Trainer chat for the selected core learning goal
    }

    async checkSenseiUnlock() {
        // Check if student has engaged with Digi-Trainer (at least one gem)
        // If yes, enable "Schedule a Sensei Session" button
    }
}
```

### Route Update
**File**: `routes/modules.py`

Pass `latest_submission` to template:
```python
latest_submission = Submission.query.filter_by(
    user_id=current_user.id, goal_id=goal_id
).order_by(Submission.created_at.desc()).first()
```

---

## 6. Database Migration

Add to `models/__init__.py`:
```python
from models.challenge_rubric import ChallengeRubric
```

Schema changes:
- New table: `challenge_rubrics`
- New columns on `ai_feedbacks`: `detected_approach`, `evaluation_json`, `alternative_approaches_json`, `line_references_json`

---

## 7. Seed Data Update

**File**: `seed_data.py`

1. Update `API_AUTH_CHALLENGE` string to include JWT option
2. Add `seed_challenge_rubric()` function with the multi-approach rubric JSON
3. Call from main seed function

---

## 8. Files to Modify

| File | Changes |
|------|---------|
| `models/challenge_rubric.py` | NEW - ChallengeRubric model |
| `models/ai_feedback.py` | Add `detected_approach`, `evaluation_json`, `alternative_approaches_json`, `line_references_json` fields |
| `models/__init__.py` | Import ChallengeRubric |
| `services/agentic_review.py` | NEW - Multi-step review pipeline with approach detection |
| `services/ai_feedback.py` | Integrate agentic review, return structured result |
| `templates/modules/goal.html` | Add 5th tab with full Review content (gems, Digi-Trainer chat, Sensei session request) |
| `routes/modules.py` | Pass `latest_submission` and `goal_progress` to template |
| `routes/submissions.py` | Update to use challenge rubric when generating feedback |
| `seed_data.py` | Update challenge description (3 approaches), add rubric seed, update goal title |
| `static/js/review-tab.js` | NEW - Orchestrates GemsUI + DigiTrainerUI in Review tab |
| `static/js/gems-ui.js` | Update text from "instructor" to "Sensei" |
| `static/js/articulation-harness-ui.js` | Rename to `digi-trainer-ui.js`, update class names |
| `static/css/styles.css` | Styles for Review tab sections |
| `templates/submissions/student_view.html` | Update "Socratic Sensei" → "Digi-Trainer" text/images |
| `static/assets/` | Add `digi-trainer.png` avatar (or rename existing) |

---

## 9. Verification Plan

1. **Seed the data**: Run `python seed_data.py --reset` to get updated challenge + rubric
2. **Test approach detection**: Submit solutions using each approach, verify correct detection
3. **Verify feedback structure**: Check that feedback includes:
   - Correct approach identification
   - Line number references
   - Alternative approaches discussion
4. **Test 5-tab UI**: Navigate through all tabs, verify Review tab shows submission data
5. **LangSmith tracing**: Verify all agent steps appear in traces

---

## 10. Goal Title Update

**File**: `seed_data.py` (line 103)

Change LearningGoal title from:
```python
title="Add API Key Authentication"
```
To:
```python
title="Add authentication to a Flask API"
```

This makes the goal more general, reflecting that multiple approaches are valid.

---

## 11. Alternative Approaches Comparison Table

The "Other Valid Approaches" section will include a **full comparison table** with code snippets, tradeoffs, and guidance on when to use each approach.

### Feedback Template for Alternatives Section:

```markdown
## Approach Comparison

| Aspect | API Key | HTTP Basic Auth | JWT |
|--------|---------|-----------------|-----|
| **Complexity** | Simple | Simple | Moderate |
| **Stateless** | Yes | Yes | Yes |
| **Expiration** | Manual | None built-in | Built-in (exp claim) |
| **Revocation** | Delete key | Change password | Requires blacklist |
| **Best For** | Server-to-server | Development/simple apps | Modern APIs, SPAs |

### API Key Example
```python
@functools.wraps(f)
def decorated(*args, **kwargs):
    api_key = request.headers.get('X-API-Key')
    if not api_key or not secrets.compare_digest(api_key, VALID_KEY):
        return jsonify({'error': 'Invalid API key'}), 401
    return f(*args, **kwargs)
```

### HTTP Basic Auth Example
```python
@functools.wraps(f)
def decorated(*args, **kwargs):
    auth = request.authorization
    if not auth or not check_password_hash(USERS.get(auth.username), auth.password):
        return jsonify({'error': 'Invalid credentials'}), 401
    return f(*args, **kwargs)
```

### JWT Example
```python
@functools.wraps(f)
def decorated(*args, **kwargs):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    return f(*args, **kwargs)
```

### When to Choose Each

- **API Key**: Best for server-to-server communication, webhooks, third-party integrations
- **HTTP Basic Auth**: Good for internal tools, development, simple admin interfaces
- **JWT**: Ideal for user-facing APIs, mobile apps, SPAs where you need stateless auth with claims
```

---

## 12. Sensei Evaluation Model

**New file**: `models/sensei_evaluation.py`

This model captures the Sensei's assessment after a session with a student.

```python
class SenseiEvaluation(db.Model):
    """Captures a Sensei's evaluation of a student after a session."""

    __tablename__ = 'sensei_evaluations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sensei_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'))
    session_date = db.Column(db.DateTime, default=datetime.utcnow)

    # Sensei's assessment
    journey_stage = db.Column(db.String(50))  # 'beginning', 'developing', 'proficient', 'mastery'
    session_notes = db.Column(db.Text)  # Private notes from the session

    # Concepts the student is still working to embody
    concepts_in_progress_json = db.Column(db.Text)  # ["decorator patterns", "error handling"]

    # Recommended next steps
    recommended_challenges_json = db.Column(db.Text)  # [goal_id, goal_id, ...]
    custom_exercises_json = db.Column(db.Text)  # Free-form suggestions

    # Certification (if applicable)
    certification_granted = db.Column(db.Boolean, default=False)
    certification_level = db.Column(db.String(50))  # 'bronze', 'silver', 'gold'

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

**Key Fields**:
- `journey_stage`: Where the student is overall (beginning → mastery)
- `concepts_in_progress_json`: What the student is still working to embody
- `recommended_challenges_json`: Suggested next learning goals
- `custom_exercises_json`: Tailored practice suggestions

---

## 13. Next Challenges Recommendation

### Model Update: `LearningGoal`

Add fields to support challenge recommendations:

```python
# In models/goal.py
class LearningGoal(db.Model):
    # ... existing fields ...

    # Prerequisite and progression tracking
    prerequisites_json = db.Column(db.Text)  # [goal_id, goal_id, ...]
    difficulty_level = db.Column(db.Integer, default=1)  # 1-5
    category_tags_json = db.Column(db.Text)  # ["auth", "api", "security"]
```

### Recommendation Logic

After a Sensei session, display:

```
┌─────────────────────────────────────────────────────────────┐
│  🎯 Recommended Next Challenges                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Based on your session with Sensei, here are your next      │
│  training exercises:                                         │
│                                                              │
│  ⭐ Claude API Integration (Recommended by Sensei)          │
│     Build a Flask endpoint that calls Claude and traces     │
│     with LangSmith.                                          │
│                                                              │
│  📚 Rate Limiting (Related skill)                           │
│     Add rate limiting to protect your API endpoints.        │
│                                                              │
│  🔒 OAuth2 Implementation (Level up from JWT)               │
│     Implement OAuth2 flows for third-party auth.            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 14. Second Learning Goal: Claude API + LangSmith

> **Implementation Note**: Use the `/concept-to-exercise` skill to generate this challenge.
> The skill will create proper git commits (before/after fix) and structure the exercise.

### Challenge Description

**Title**: "Build an AI-Powered Flask Endpoint with Observability"

```markdown
## Challenge: Build an AI-Powered Flask Endpoint

Create a Flask API endpoint that integrates with the Claude LLM API and
captures all interactions in LangSmith for observability.

### Your Task

Build a `/api/ask` endpoint that:
1. Accepts a question in the request body
2. Sends it to Claude for a response
3. Returns the AI-generated answer
4. Traces the entire interaction in LangSmith

### Requirements

1. **Choose an implementation approach**:
   - **Direct Anthropic SDK** - Using the official `anthropic` Python package
   - **LangChain Integration** - Using LangChain's ChatAnthropic wrapper
   - **Custom HTTP Client** - Using `requests` or `httpx` directly

2. **Implement proper error handling**:
   - Handle API rate limits gracefully
   - Return meaningful error messages
   - Log errors for debugging

3. **Add LangSmith tracing**:
   - Trace all LLM calls
   - Include metadata (model, tokens, latency)
   - Support trace grouping by session

4. **Environment configuration**:
   - API keys from environment variables
   - Configurable model selection
   - Tracing can be enabled/disabled

### Getting Started

1. Fork the starter repository
2. Set up your Anthropic and LangSmith API keys
3. Implement your solution
4. Submit your branch

### Success Criteria

- Endpoint returns Claude's response correctly
- All calls appear in LangSmith dashboard
- Errors are handled gracefully
- No API keys in source code
```

### Multi-Approach Rubric

```json
{
  "version": "1.0",
  "valid_approaches": [
    {
      "id": "anthropic_sdk",
      "name": "Direct Anthropic SDK",
      "detection_patterns": ["from anthropic import", "Anthropic()", "client.messages.create"],
      "tradeoffs": {
        "pros": ["Official SDK", "Type hints", "Minimal dependencies", "Direct control"],
        "cons": ["Manual tracing setup", "No built-in retries", "Less abstraction"]
      }
    },
    {
      "id": "langchain",
      "name": "LangChain Integration",
      "detection_patterns": ["from langchain", "ChatAnthropic", "invoke(", "langchain_anthropic"],
      "tradeoffs": {
        "pros": ["Built-in LangSmith integration", "Automatic tracing", "Rich ecosystem"],
        "cons": ["Heavier dependency", "Abstraction overhead", "Versioning complexity"]
      }
    },
    {
      "id": "http_client",
      "name": "Custom HTTP Client",
      "detection_patterns": ["requests.post", "httpx", "api.anthropic.com", "messages"],
      "tradeoffs": {
        "pros": ["Full control", "Minimal dependencies", "Educational value"],
        "cons": ["Manual everything", "Error-prone", "No SDK benefits"]
      }
    }
  ],
  "universal_criteria": [
    {
      "id": "endpoint_works",
      "criterion": "POST /api/ask returns Claude's response",
      "pass_indicators": ["Returns JSON with 'response' field", "Status 200 on success"]
    },
    {
      "id": "error_handling",
      "criterion": "Handles API errors gracefully",
      "pass_indicators": ["Rate limit handling", "Timeout handling", "Meaningful error messages"]
    },
    {
      "id": "langsmith_tracing",
      "criterion": "Traces appear in LangSmith",
      "pass_indicators": ["@traceable decorator or equivalent", "Trace metadata included"]
    },
    {
      "id": "env_config",
      "criterion": "API keys from environment",
      "pass_indicators": ["os.getenv usage", "No hardcoded keys"]
    }
  ],
  "approach_specific_criteria": {
    "anthropic_sdk": [
      {"id": "sdk_init", "criterion": "Properly initializes Anthropic client"},
      {"id": "manual_trace", "criterion": "Implements manual LangSmith tracing"}
    ],
    "langchain": [
      {"id": "chain_setup", "criterion": "Properly configures LangChain chain"},
      {"id": "auto_trace", "criterion": "Leverages automatic LangSmith integration"}
    ],
    "http_client": [
      {"id": "headers", "criterion": "Sets correct headers (x-api-key, content-type)"},
      {"id": "response_parse", "criterion": "Correctly parses API response structure"}
    ]
  }
}
```

### Core Learning Goals for Claude API Challenge

1. **LLM API Integration** (Blue gem)
   - Understanding API request/response structure
   - Token management and context windows
   - Model selection and parameters

2. **Observability with LangSmith** (Purple gem)
   - Trace instrumentation
   - Metadata capture
   - Debugging with traces

3. **Error Handling for External APIs** (Green gem)
   - Rate limit handling
   - Timeout strategies
   - Retry logic

4. **Environment Configuration** (Orange gem)
   - Secrets management
   - Config patterns
   - Development vs production

---

## 15. Updated Files to Modify

| File | Changes |
|------|---------|
| `models/sensei_evaluation.py` | NEW - Sensei's post-session assessment model |
| `models/goal.py` | Add `prerequisites_json`, `difficulty_level`, `category_tags_json` |
| `routes/sensei.py` | NEW - Sensei session management endpoints |
| `seed_data.py` | Add second learning goal (Claude API + LangSmith) |

---

## 16. Implementation Steps

1. **Create second challenge**: Run `/concept-to-exercise` skill with Claude API + LangSmith concept
2. **Seed both learning goals**: Verify two challenges appear in module
3. **Test multi-approach detection**: Submit different solutions, verify correct approach identified
4. **Test Digi-Trainer flow**: Engage with gems, verify unlock for Sensei session
5. **Test Sensei evaluation**: Create evaluation record, verify next challenges display
6. **End-to-end journey**: Complete Challenge → Digi-Trainer → Sensei → Next Challenges
