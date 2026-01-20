# Implementation Plan: LangChain/LangGraph/LangSmith with Agent Harness and Gems System

## Implementation Status

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1: Database Schema & Models | ✅ COMPLETED | Created core_learning_goal.py, goal_progress.py, agent_session.py, challenge_plan.py, voice_input_metrics.py |
| Phase 2: LangSmith Infrastructure | ✅ COMPLETED | Added dependencies, configured config.py, updated socratic_chat.py with @traceable |
| Phase 3: Agent Harness Service | ✅ COMPLETED | Created socratic_harness_base.py, planning_harness.py, articulation_harness.py, whisper_transcription.py |
| Phase 4: API Routes | ✅ COMPLETED | Created routes/agent_harness.py with all endpoints, registered blueprint in app.py |
| Phase 5: Frontend | ✅ COMPLETED | Created gems-ui.js, voice-input.js, checkmarks-ui.js, plan-editor.js, articulation-harness-ui.js, agent-harness.css |
| Phase 6: Instructor Feedback Gating | ✅ COMPLETED | Updated routes/submissions.py with 50% engagement threshold |
| Phase 7: Rubric Creation | ✅ COMPLETED | Added seed_core_learning_goals() to seed_data.py with 5 core goals for Flask API Auth |
| Integration Tests | ✅ COMPLETED | 7/7 tests passing in tests/test_agent_harness.py |

**Last Updated**: 2026-01-18

---

## Executive Summary

Implement a systematic learning journey system for Code Dojo that guides students through core learning goals using LangChain/LangGraph agents, tracks their understanding with rubric-based evaluation, visualizes progress with gems around a Sensei avatar, and uses engagement-based gating for instructor feedback.

**Key Differentiation**: Pre-challenge and post-challenge experiences serve fundamentally different pedagogical goals with distinct UIs, progress indicators, and interaction modes.

---

## Pedagogical Framework

### Core Skill Development

| Phase | Core Skill | Primary Output | Interaction Mode | Progress Indicator |
|-------|------------|----------------|------------------|-------------------|
| Pre-Challenge | Creating & executing plans with AI agents | A plan artifact for agentic coding tools | Text-based planning | ✓ Checkmarks (coverage) |
| Post-Challenge | Articulating what you've done | Verbal explanation practice | Voice-first dialogue | 💎 Gems (mastery) |

### Pre-Challenge: Plan Creation
The fundamental skill being developed is working effectively with AI agents to create and execute plans. Students learn to:
- Break down challenges into actionable steps
- Anticipate technical considerations
- Create artifacts that guide their coding session
- Iterate on plans as understanding deepens

### Post-Challenge: Verbal Articulation
The fundamental skill being developed is the ability to clearly explain technical work. Students learn to:
- Articulate their implementation decisions verbally
- Explain code to others (preparation for reviews, interviews)
- Reflect on their learning through spoken explanation
- Build confidence in technical communication

---

## Critical Distinction: Checkmarks vs Gems

**Pre-Challenge: Checkmarks for Plan Coverage**
- Shows whether learning goals are *addressed* in the plan
- Binary: covered ✓ or not covered ○
- Evaluates the plan artifact, not student mastery
- "Your plan addresses 3/4 key concepts"

**Post-Challenge: Gems for Demonstrated Mastery**
- Shows whether student can *articulate* understanding
- Requires submitting code AND talking through it
- Rubric-based evaluation of verbal explanation
- Gems unlock through demonstrated articulation

---

## Key Design Decisions

### 1. Architecture: Layered Orchestration Model
- **Socratic Sensei (Teaching Layer)**: Existing chat service with Anthropic SDK - handles all conversations with students using Socratic method
- **Agent Harness (Orchestration Layer)**: LangGraph state machine that coordinates learning flow, calls Socratic chat for each rubric item, evaluates responses
- **LangSmith tracing**: Captures entire flow from orchestration to conversation
- **Single unified personality**: Students interact with one Socratic Sensei throughout, agent works behind the scenes

### 2. Agentic Harness Architecture: Shared Core, Different Flows

**Shared Components:**
- Socratic Sensei personality and prompt templates
- Core learning goals / rubric definitions
- LangSmith tracing infrastructure
- Base conversation management

**Separate Orchestration Flows:**

| Aspect | Pre-Challenge (PlanningHarness) | Post-Challenge (ArticulationHarness) |
|--------|--------------------------------|-------------------------------------|
| Entry state | `planning_intro` | `articulation_intro` |
| Input handling | Text only | Voice-first + text fallback |
| Evaluation target | Plan document coverage | Verbal rubric responses |
| Progress tracking | Checkmarks on plan | Gems on student profile |
| Output artifact | Exportable plan markdown | Rubric evaluation results |
| Gating | None (optional) | 50% gems to unlock instructor |

**Implementation Approach:**
```python
# Shared base class
class SocraticHarnessBase:
    """Common functionality for both harnesses."""
    def __init__(self, learning_goal_id, user_id):
        self.learning_goals = CoreLearningGoal.query.filter_by(...)
        self.socratic_chat = SocraticChatService()

    def get_rubric_items(self): ...
    def send_socratic_message(self, context): ...

# Pre-challenge: Plan-focused harness
class PlanningHarness(SocraticHarnessBase):
    """Guides student to create an implementation plan."""

    def evaluate_plan_coverage(self, plan_text) -> dict:
        """Check which learning goals are addressed in plan."""
        # Returns: {"goal_1": True, "goal_2": False, ...}

    def generate_plan_from_conversation(self) -> str:
        """Extract structured plan from dialogue."""

# Post-challenge: Articulation-focused harness
class ArticulationHarness(SocraticHarnessBase):
    """Evaluates student's verbal articulation of concepts."""

    def process_voice_input(self, audio_data) -> str:
        """Transcribe via Whisper API."""

    def evaluate_articulation(self, transcript, rubric_item) -> bool:
        """Binary pass/fail on verbal explanation."""

    def update_gem_status(self, goal_id, passed: bool): ...
```

### 3. How Agent Harness and Socratic Chat Work Together
```
┌─────────────────────────────────────────────────────┐
│         Student sees: Single Socratic Sensei         │
└─────────────────────────────────────────────────────┘
                         ↕
┌─────────────────────────────────────────────────────┐
│  Agent Harness (LangGraph Orchestration)            │
│  - Selects next rubric item                         │
│  - Prepares rubric context (criterion, hints)       │
│  - Calls Socratic chat with rubric topic            │
│  - Receives student response                        │
│  - Evaluates against pass indicators                │
│  - Decides: passed / next hint / mark engaged       │
│  - Manages flow (gems, progress, unlocks)           │
└─────────────────────────────────────────────────────┘
                         ↕
┌─────────────────────────────────────────────────────┐
│  Socratic Chat Service (Teaching)                   │
│  - Same warm Socratic Sensei personality            │
│  - Asks questions based on rubric hints             │
│  - Guides student to understanding                  │
│  - Returns conversation + realizations              │
└─────────────────────────────────────────────────────┘
                         ↕
┌─────────────────────────────────────────────────────┐
│  Claude API (with LangSmith tracing)                │
└─────────────────────────────────────────────────────┘
```

### 4. Learning Goals Structure
- **CoreLearningGoal replaces AnatomyTopic** for rubric-based learning
- Each core learning goal = anatomy topic with structured rubric
- Admin configures core learning goals (title, description, rubric)
- Existing anatomy topic buttons become entry points to rubric-evaluated learning
- Each goal has a **rubric** with binary pass/fail criteria

### 5. Evaluation System: Rubric-Based, Not Confidence Scores
- **Binary pass/fail** per rubric item (not 0-100% confidence)
- **3 attempts per rubric item** using progressive Socratic hinting
- After 3 attempts: Mark as "engaged" and move to next item
- Failed items still count as engagement toward instructor unlock
- **Engagement threshold**: Must attempt ≥50% of learning goals to unlock instructor feedback
- **Override mechanism** available if student shows frustration

---

## Entry Points & User Interface

### Pre-Challenge Context: "Plan Mode"

**Visual Identity:**
- Header: "Plan Your Approach"
- Icon: 📋 or blueprint/schematic icon
- Color accent: Blue/teal (planning, thinking)
- Sensei prompt style: Collaborative planning partner

**Copy/Framing:**
```
"Let's build your implementation plan together."
"What's your initial approach to this challenge?"
"Before you code, let's think through the key steps."
```

**Features:**
- Page shows challenge description + video
- Section: "Plan Your Approach"
- Text-based planning dialogue with Socratic Sensei
- Plan preview panel builds in real-time alongside chat
- **Fully editable**: Student can modify the generated plan before exporting
- Rich text editor for plan refinement
- Copy-to-clipboard for easy paste into coding tools (Claude, Cursor)
- **Checkmarks** show which learning goals are addressed in plan (NOT gems)
- **Optional**: Students can skip directly to "Start Coding"

**Plan Document Output:**
```markdown
# Implementation Plan: [Challenge Title]

## Understanding
- Key concepts explored: [list from Socratic session]
- Core requirements: [derived from challenge description]

## Approach
- [Step 1]: ...
- [Step 2]: ...
- [Step 3]: ...

## Key Considerations
- [Technical consideration from Socratic dialogue]
- [Edge case discussed]

## Questions to Explore While Coding
- [Open question that emerged]
```

**Layout:**
```
┌──────────────────────────────────────────────────────────────┐
│  📋 Plan Your Approach                                        │
├────────────────────────────────┬─────────────────────────────┤
│                                │  YOUR PLAN                   │
│   Socratic Sensei Chat         │  ─────────────               │
│                                │  ## Understanding            │
│   "What's your initial         │  - [builds as you talk]     │
│    approach to this?"          │                              │
│                                │  ## Approach                 │
│   [Text input]                 │  - Step 1: ...              │
│                                │  - Step 2: ...              │
│                                │                              │
│                                │  ─────────────               │
│                                │  COVERAGE (2/4)              │
│                                │  ✓ Authentication            │
│                                │  ✓ Sessions                  │
│                                │  ○ Passwords                 │
│                                │  ○ Authorization             │
│                                │                              │
│                                │  [Edit Plan] [Export →]     │
└────────────────────────────────┴─────────────────────────────┘
```

### Post-Challenge Context: "Talk Through Mode"

**Visual Identity:**
- Header: "Talk Through Your Solution"
- Icon: 🎤 or conversation/presentation icon
- Color accent: Purple/warm (communication, presentation)
- Sensei prompt style: Interviewer/reviewer persona

**Copy/Framing:**
```
"Walk me through what you built."
"Explain your approach as if I'm a colleague reviewing your code."
"How would you describe this to a teammate?"
"This is practice for code reviews and technical interviews."
```

**Features:**
- Page shows submitted code diff + AI feedback
- Section: "Talk Through Your Solution"
- **Voice input is PRIMARY** - Whisper API for transcription
- Text input available as explicit fallback ("Prefer to type instead?")
- Code diff visible for reference while explaining
- **Gems display** showing mastery progress (NOT checkmarks)
- **50% engagement required** before requesting instructor feedback
- Instructor feedback unlock gated by gems

**Voice Input Implementation:**
- Use **Whisper API** (OpenAI) for consistent, high-quality transcription
- Cost: ~$0.006/minute - budget for typical 2-5 min explanations
- Record audio client-side, send to backend for Whisper processing
- Show transcription after recording completes
- Student can review/edit transcription before sending
- Support for pause/resume recording

**UI Flow:**
```
┌─────────────────────────────────────────────────────────┐
│  Socratic Sensei wants to hear about your solution      │
│                                                         │
│  [🎤 Talk Through Your Code]  ← Primary, prominent      │
│                                                         │
│  Prefer to type? [Switch to text input]  ← Secondary    │
└─────────────────────────────────────────────────────────┘
```

**Layout:**
```
┌──────────────────────────────────────────────────────────────┐
│  🎤 Talk Through Your Solution                                │
│  Practice explaining your code like you would to a colleague  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  MASTERY   💎 ○ ○ ○   (1/4 - unlock 2 for instructor)        │
│                                                              │
│        ┌─────────────────────────────────────┐               │
│        │  🎤  Tap to explain your solution   │               │
│        │      [Recording interface]          │               │
│        └─────────────────────────────────────┘               │
│                                                              │
│        Prefer to type? [Switch to text]                      │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  CONCEPTS TO EXPLAIN            │  Sensei Chat               │
│  💎 Authentication (mastered)   │                            │
│  ○ Sessions                     │  "Walk me through how      │
│  ○ Passwords                    │   you handled sessions..." │
│  ○ Authorization                │                            │
│                                 │                            │
│  [Your code diff for reference] │                            │
└─────────────────────────────────┴────────────────────────────┘
```

### Side-by-Side Comparison

| Aspect | Pre-Challenge | Post-Challenge |
|--------|----------------|-----------------|
| Header | "Plan Your Approach" | "Talk Through Your Solution" |
| Icon | 📋 Blueprint | 🎤 Microphone |
| Color | Blue/Teal | Purple/Warm |
| Input | Text (planning) | Voice-first (speaking) |
| Sidebar | Plan building in real-time | Code diff + concepts to explain |
| **Progress** | **✓ Checkmarks** (plan coverage) | **💎 Gems** (demonstrated mastery) |
| Sensei tone | "Let's think through..." | "Walk me through..." |
| Framing | "Before you code" | "Like explaining to a colleague" |
| Output | Exportable plan artifact | Gem unlocks + verbal practice |
| Gating | None (optional) | 50% gems to unlock instructor |
| CTA | "Export Plan & Start Coding" | "Continue to Instructor Feedback" |

### Professional Context Messaging (Post-Challenge)
- "Explaining code verbally is essential for code reviews"
- "Technical interviews often ask you to walk through your solutions"
- "Practice articulating your decisions to build confidence"
- "Your recording won't be shared - this is for your practice"

---

## Metrics to Track

### Voice Input Analytics
- `voice_input_offered`: Count of times voice prompt shown
- `voice_input_accepted`: Count of times student used voice
- `voice_input_declined`: Count of times student chose text fallback
- `voice_input_skip_rate`: Ratio of declined/offered (key metric)
- `voice_duration_seconds`: How long students speak
- `voice_vs_text_word_count`: Compare verbosity between modes

### Plan Export Analytics
- `plan_exported_at`: When student exported
- `plan_iterations`: How many times they refined it
- `coverage_json`: Which learning goals addressed

---

## Gems System (Global Progress with Re-Certification)

**Unlock with Time-Based Expiration:**
- Gems are tied to **user + learning_goal**, not individual submissions
- Once you demonstrate understanding, it's unlocked for a **certification period**
- After expiration, must re-demonstrate to renew (re-certification)
- Pre-coding learning persists to post-submission context (within certification period)
- Database: `goal_progress` tracks by `(user_id, core_goal_id)` with `expires_at` timestamp

**Certification Period:**
- Admin-configurable per CoreLearningGoal (default: 90 days)
- Examples: Fundamentals might be 30 days, advanced concepts 90 days
- Set in admin panel: "This concept requires re-certification every X days"

**Gem States:**
- **Gray (locked)**: Not yet explored OR expired certification
- **Blue (pulsing)**: Currently exploring
- **Blue (solid)**: Passed - current certification (not expired)
- **Purple (solid)**: Engaged but struggled - current certification (not expired)
- **Yellow/Orange (faded)**: Expired certification - needs renewal

**Re-Certification Flow:**
- When gem expires, status changes to `expired`
- Student sees yellow/orange gem on button
- Clicking starts conversation: "Your understanding of X needs renewal. Let's revisit..."
- Goes through rubric evaluation again
- Can renew as `passed` or `engaged`
- New `expires_at` timestamp set

**Engagement Calculation:**
- Only **non-expired** gems count toward 50% instructor unlock threshold
- If 2/4 gems are blue but 1 is expired, only counts as 1/4 (25%)
- Encourages keeping certifications current

**Why Re-Certification?**
- Ensures knowledge retention over time
- Supports spaced repetition learning
- Keeps skills current as students progress
- Prevents "certified once, forgot later" problem

---

## Implementation Phases

### Phase 1: Database Schema & Models

#### New Tables

**`core_learning_goals`**
```sql
CREATE TABLE core_learning_goals (
    id INTEGER PRIMARY KEY,
    learning_goal_id INTEGER REFERENCES learning_goals(id),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    rubric_json TEXT NOT NULL,  -- JSON array of rubric items
    order_index INTEGER DEFAULT 0,
    gem_color VARCHAR(20) DEFAULT 'blue',
    certification_days INTEGER DEFAULT 90,  -- How many days until expiration
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Re-Certification Period Field:**
- `certification_days`: Number of days the certification is valid
- Admin-configurable per concept
- Default: 90 days
- Can be set to NULL for "never expires" (permanent certification)

**Rubric JSON Format:**
```json
{
  "items": [
    {
      "id": "auth_basic_concept",
      "criterion": "Can explain what authentication means in the context of APIs",
      "pass_indicators": [
        "Explains authentication verifies user identity",
        "Distinguishes authentication from authorization",
        "Relates it to their API implementation"
      ],
      "socratic_hints": [
        "What problem does authentication solve in your API?",
        "Think about when you log into a website - what's happening?",
        "In your code, what happens before you can access protected data?"
      ]
    }
  ]
}
```

**`goal_progress`** (Global, per-user with expiration)
```sql
CREATE TABLE goal_progress (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    learning_goal_id INTEGER REFERENCES learning_goals(id),
    core_goal_id INTEGER REFERENCES core_learning_goals(id),
    status VARCHAR(20) DEFAULT 'locked',  -- locked, in_progress, engaged, passed, expired
    attempts INTEGER DEFAULT 0,
    rubric_results_json TEXT,  -- JSON with per-item results
    last_explored_submission_id INTEGER REFERENCES submissions(id),
    unlocked_at TIMESTAMP,
    expires_at TIMESTAMP,  -- When certification expires
    certification_count INTEGER DEFAULT 0,  -- How many times re-certified
    completed_at TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(user_id, core_goal_id)
);
```

**Rubric Results JSON Format:**
```json
{
  "items": [
    {
      "id": "auth_basic_concept",
      "status": "passed",
      "attempts": 2,
      "student_response": "Authentication checks who you are...",
      "evaluation": "Student demonstrated understanding by relating to login flow"
    }
  ],
  "overall_status": "passed",
  "pass_count": 3,
  "fail_count": 1,
  "total_items": 4
}
```

**`challenge_plans`** (NEW - for pre-challenge plan artifacts)
```sql
CREATE TABLE challenge_plans (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    learning_goal_id INTEGER REFERENCES learning_goals(id),
    plan_content TEXT,
    coverage_json TEXT,  -- {"goal_1": true, "goal_2": false, ...}
    plan_exported_at TIMESTAMP,
    plan_iterations INTEGER DEFAULT 0,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**`agent_sessions`** (Tracks specific conversation sessions)
```sql
CREATE TABLE agent_sessions (
    id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    learning_goal_id INTEGER REFERENCES learning_goals(id),
    core_goal_id INTEGER REFERENCES core_learning_goals(id),
    submission_id INTEGER REFERENCES submissions(id),  -- NULL if pre-coding
    harness_type VARCHAR(20),  -- 'planning' or 'articulation'
    context VARCHAR(20),  -- 'pre_coding' or 'post_submission'
    status VARCHAR(20) DEFAULT 'active',
    guide_me_mode BOOLEAN DEFAULT FALSE,
    langsmith_run_id VARCHAR(100),
    created_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

**`agent_messages`**
```sql
CREATE TABLE agent_messages (
    id INTEGER PRIMARY KEY,
    session_id VARCHAR(36) REFERENCES agent_sessions(id),
    role VARCHAR(20),  -- user, assistant, system
    content TEXT,
    input_mode VARCHAR(10),  -- 'voice' | 'text'
    voice_duration_seconds INTEGER,
    original_transcription TEXT,  -- Raw transcription before edits
    metadata_json TEXT,  -- rubric item ID, attempt number, etc.
    created_at TIMESTAMP
);
```

**`voice_input_metrics`** (NEW - for analytics)
```sql
CREATE TABLE voice_input_metrics (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    session_id VARCHAR(36) REFERENCES agent_sessions(id),
    offered_at TIMESTAMP,
    response VARCHAR(20),  -- 'accepted' | 'declined'
    voice_duration_seconds INTEGER,
    created_at TIMESTAMP
);
```

#### New Model Files

**`models/core_learning_goal.py`**
- CoreLearningGoal model with rubric JSON field
- Methods: `get_rubric()`, `get_rubric_item(item_id)`

**`models/goal_progress.py`**
- GoalProgress model tracking rubric-based evaluation
- Methods: `get_rubric_results()`, `increment_attempts()`, `mark_item_passed()`, `can_unlock_instructor()`

**`models/agent_session.py`**
- AgentSession and AgentMessage models
- Methods: `calculate_engagement_percent()`, `can_request_instructor()`

**`models/challenge_plan.py`**
- ChallengePlan model for pre-challenge plan artifacts
- Methods: `get_coverage()`, `update_coverage()`, `export_markdown()`

### Phase 2: LangSmith Infrastructure

#### Install Dependencies
```txt
langchain>=0.1.0
langchain-anthropic>=0.1.0
langgraph>=0.0.20
langsmith>=0.0.77
openai>=1.0.0  # For Whisper API
```

#### Environment Configuration (`config.py`)
```python
LANGCHAIN_TRACING_V2 = os.getenv('LANGCHAIN_TRACING_V2', 'true')
LANGCHAIN_API_KEY = os.getenv('LANGCHAIN_API_KEY', '')
LANGCHAIN_PROJECT = os.getenv('LANGCHAIN_PROJECT', 'code-dojo')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')  # For Whisper
```

#### Enhance Socratic Chat for Rubric Context

**`services/socratic_chat.py` - MODIFY**

Add support for rubric-specific conversations while keeping existing free-form anatomy topics:

```python
from langsmith import traceable

def get_socratic_system_prompt(topic_name, topic_description, analogies, diff_content, challenge_context, rubric_context=None):
    """Build the system prompt for Socratic dialogue.

    Args:
        rubric_context: Optional dict with:
            - criterion: The learning criterion to explore
            - pass_indicators: What demonstrates understanding
            - current_hint_index: Which Socratic hint to emphasize (0-2)
            - hints: List of progressive Socratic questions
    """
    # Existing prompt logic...

    # Add rubric section if provided
    rubric_section = ""
    if rubric_context:
        current_hint = rubric_context['hints'][rubric_context['current_hint_index']]
        rubric_section = f"""
## Focused Learning Objective
Your goal in this conversation is to guide the student to understand:
**{rubric_context['criterion']}**

They demonstrate understanding when they can:
{format_pass_indicators(rubric_context['pass_indicators'])}

Start with this Socratic question:
{current_hint}

If they struggle, build up progressively from simpler concepts.
"""

    return f"""You are the Socratic Sensei...

{rubric_section}

{existing_prompt_content}
"""

@traceable(name="socratic_chat_start", metadata={"feature": "socratic_sensei"})
def start_conversation(submission, topic_id=None, topic_name=None, topic_description=None,
                       analogies=None, diff_content=None, rubric_context=None):
    """Start conversation - now accepts optional rubric_context for agent-driven sessions."""
    # Existing implementation, now passes rubric_context to prompt builder
    system_prompt = get_socratic_system_prompt(
        topic_name, topic_description, analogies, diff_content, challenge_context, rubric_context
    )
    # ... rest of existing logic

@traceable(name="socratic_chat_message")
def send_message(conversation_id, user_message, diff_content=None, rubric_context=None):
    """Send message - now accepts optional rubric_context for progressive hints."""
    # Existing implementation, updated to use rubric_context if provided
```

**Key Changes:**
- Add optional `rubric_context` parameter to existing functions
- Keep all existing behavior when `rubric_context=None` (free-form anatomy topics)
- When rubric context provided, inject focused learning objective and hint into system prompt
- No changes to Socratic personality or teaching style

### Phase 3: Agent Harness Service (LangGraph)

#### File: `services/agent_harness.py` (NEW)

**Architecture: Orchestration that calls Socratic Chat**

The agent harness is a state machine that manages rubric progression and calls the existing `socratic_chat` service for all student interactions.

**1. State Definition**
```python
class AgentState(TypedDict):
    session_id: str
    submission_id: int
    learning_goals: List[dict]  # CoreLearningGoal data
    current_goal_index: int
    current_rubric_item_index: int
    current_attempts: int  # For current rubric item
    active_conversation_id: str  # Current socratic_chat conversation
    agent_phase: str  # intro, probing, evaluating, negotiating, synthesizing
    can_unlock_instructor: bool
    frustration_detected: bool
```

**2. Graph Nodes**

```python
def initialize_session(state: AgentState) -> AgentState:
    """Load goals, offer student choice of starting point."""
    submission = Submission.query.get(state['submission_id'])

    # Load all core learning goals for this exercise
    goals = CoreLearningGoal.query.filter_by(
        learning_goal_id=submission.goal_id
    ).order_by(CoreLearningGoal.order_index).all()

    state['learning_goals'] = [g.to_dict() for g in goals]
    state['guide_me_mode'] = False  # Default: student chooses
    state['current_goal_index'] = None  # No goal selected yet
    state['current_rubric_item_index'] = 0
    state['current_attempts'] = 0

    # Create welcome message offering choice
    welcome = f"""Hello! I'm your Socratic Sensei. I can help you explore {len(goals)} key learning concepts from this challenge:

{format_goal_menu(goals)}

How would you like to proceed?
1. Let me choose a topic to start with
2. Suggest a good starting point for me
3. Guide me through all of them in order"""

    state['last_assistant_message'] = welcome

    return state

def handle_student_choice(state: AgentState, user_message: str) -> AgentState:
    """Process student's topic selection or mode preference."""
    if "guide me" in user_message.lower() or "all of them" in user_message.lower():
        state['guide_me_mode'] = True
        state['current_goal_index'] = 0
        state['agent_phase'] = 'start_conversation'

    elif "suggest" in user_message.lower():
        recommended_index = recommend_next_goal(state)
        state['current_goal_index'] = recommended_index
        state['agent_phase'] = 'start_conversation'

    else:
        selected_index = parse_topic_selection(user_message, state['learning_goals'])
        if selected_index is not None:
            state['current_goal_index'] = selected_index
            state['agent_phase'] = 'start_conversation'
        else:
            state['agent_phase'] = 'clarify_choice'

    return state

def check_topic_switch(state: AgentState, user_message: str) -> bool:
    """Detect if student wants to switch topics mid-conversation."""
    switch_signals = [
        "switch to",
        "let's talk about",
        "instead",
        "different topic",
        "what about"
    ]

    for signal in switch_signals:
        if signal in user_message.lower():
            new_index = parse_topic_selection(user_message, state['learning_goals'])
            if new_index is not None:
                if state.get('active_conversation_id'):
                    end_conversation(state['active_conversation_id'])

                state['current_goal_index'] = new_index
                state['current_rubric_item_index'] = 0
                state['current_attempts'] = 0
                return True

    return False

def start_rubric_conversation(state: AgentState) -> AgentState:
    """Start a Socratic conversation focused on current rubric item."""
    current_goal = state['learning_goals'][state['current_goal_index']]
    rubric_items = current_goal['rubric']['items']
    current_item = rubric_items[state['current_rubric_item_index']]

    rubric_context = {
        'criterion': current_item['criterion'],
        'pass_indicators': current_item['pass_indicators'],
        'hints': current_item['socratic_hints'],
        'current_hint_index': min(state['current_attempts'], 2)
    }

    submission = Submission.query.get(state['submission_id'])
    diff_content = fetch_diff_for_submission(submission)

    conversation, opening_response = start_conversation(
        submission=submission,
        topic_name=current_item['criterion'],
        topic_description=f"Let's explore: {current_goal['title']}",
        diff_content=diff_content,
        rubric_context=rubric_context
    )

    state['active_conversation_id'] = conversation.id

    return state

def process_student_message(state: AgentState, user_message: str) -> AgentState:
    """Send student message to Socratic chat and get response."""

    if check_topic_switch(state, user_message):
        state['agent_phase'] = 'start_conversation'
        return state

    if "guide me" in user_message.lower() or "what next" in user_message.lower():
        state['guide_me_mode'] = True

    submission = Submission.query.get(state['submission_id'])
    diff_content = fetch_diff_for_submission(submission)

    current_goal = state['learning_goals'][state['current_goal_index']]
    rubric_items = current_goal['rubric']['items']
    current_item = rubric_items[state['current_rubric_item_index']]

    state['current_attempts'] += 1

    rubric_context = {
        'criterion': current_item['criterion'],
        'pass_indicators': current_item['pass_indicators'],
        'hints': current_item['socratic_hints'],
        'current_hint_index': min(state['current_attempts'], 2)
    }

    success, assistant_response = send_message(
        conversation_id=state['active_conversation_id'],
        user_message=user_message,
        diff_content=diff_content,
        rubric_context=rubric_context
    )

    state['last_student_message'] = user_message
    state['last_assistant_response'] = assistant_response

    return state

def evaluate_understanding(state: AgentState) -> AgentState:
    """Evaluate student's understanding against rubric pass indicators."""
    current_goal = state['learning_goals'][state['current_goal_index']]
    rubric_items = current_goal['rubric']['items']
    current_item = rubric_items[state['current_rubric_item_index']]

    passed = evaluate_rubric_item(
        student_response=state['last_student_message'],
        rubric_item=current_item
    )

    update_rubric_item_status(
        state['session_id'],
        current_goal['id'],
        current_item['id'],
        'passed' if passed else 'in_progress',
        state['current_attempts'],
        state['last_student_message']
    )

    if passed:
        state['current_rubric_item_index'] += 1
        state['current_attempts'] = 0
        state['agent_phase'] = 'next_item'
        update_gem_state(state['session_id'], current_goal['id'])

    elif state['current_attempts'] >= 3:
        update_rubric_item_status(
            state['session_id'],
            current_goal['id'],
            current_item['id'],
            'engaged',
            state['current_attempts'],
            state['last_student_message']
        )
        state['current_rubric_item_index'] += 1
        state['current_attempts'] = 0
        state['agent_phase'] = 'next_item'
    else:
        state['agent_phase'] = 'continue_probing'

    return state

def check_goal_completion(state: AgentState) -> AgentState:
    """Check if all rubric items for current goal are done."""
    current_goal = state['learning_goals'][state['current_goal_index']]
    rubric_items = current_goal['rubric']['items']

    if state['current_rubric_item_index'] >= len(rubric_items):
        end_conversation(state['active_conversation_id'])
        state['active_conversation_id'] = None
        update_goal_gem_status(state['session_id'], current_goal['id'])
        check_negotiation_threshold(state)

        if state['guide_me_mode']:
            next_index = recommend_next_goal(state)
            if next_index is not None:
                state['current_goal_index'] = next_index
                state['current_rubric_item_index'] = 0
                state['current_attempts'] = 0
                state['agent_phase'] = 'start_conversation'
            else:
                state['agent_phase'] = 'synthesize'
        else:
            state['agent_phase'] = 'offer_choice'
            remaining = get_remaining_goals(state)
            if remaining:
                message = f"""Great work on {current_goal['title']}!

What would you like to explore next?
{format_goal_menu(remaining)}

Or say "guide me" and I'll suggest the best next topic."""
                state['last_assistant_message'] = message
            else:
                state['agent_phase'] = 'synthesize'

    return state
```

**3. Evaluation Logic** (Separate Claude call, not part of Socratic chat)
```python
@traceable(name="evaluate_rubric_item")
def evaluate_rubric_item(student_response, rubric_item):
    """Binary pass/fail evaluation using Claude.

    This is SEPARATE from the Socratic conversation.
    This is the agent's internal evaluation logic.
    """
    prompt = f"""Evaluate if student demonstrates understanding of this criterion:

CRITERION: {rubric_item['criterion']}

PASS INDICATORS (must show at least 2 of these):
{format_indicators(rubric_item['pass_indicators'])}

STUDENT RESPONSE:
{student_response}

Evaluate objectively. Return JSON: {{"passed": true/false, "evaluation": "brief explanation"}}
"""

    client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )

    import json
    result = json.loads(response.content[0].text)
    return result['passed']
```

**4. Frustration Detection**
```python
def detect_frustration(state):
    """Detect user frustration from message patterns."""
    recent_messages = state['messages'][-5:]

    frustration_signals = [
        "I don't understand",
        "can we move on",
        "this is confusing",
        "skip this",
    ]

    for msg in recent_messages:
        if any(signal in msg.lower() for signal in frustration_signals):
            state['frustration_detected'] = True
            break
```

**5. Negotiation Logic**
```python
def offer_negotiation(state):
    """At 50% completion, offer instructor unlock."""
    session = AgentSession.query.get(state['session_id'])
    engagement_percent = (session.goals_engaged + session.goals_passed) / session.total_goals

    if engagement_percent >= 0.5 and not state['can_unlock_instructor']:
        state['can_unlock_instructor'] = True

        message = """Great progress! You've explored half the learning goals.

You can now request instructor feedback if you'd like, or we can continue exploring the remaining concepts together. What would you prefer?"""

        state['messages'].append(AIMessage(content=message))
```

**6. Graph Structure**
```python
workflow = StateGraph(AgentState)

workflow.add_node("initialize", initialize_session)
workflow.add_node("start_rubric_conversation", start_rubric_conversation)
workflow.add_node("wait_for_response", wait_for_student_response)
workflow.add_node("process_message", process_student_message)
workflow.add_node("evaluate", evaluate_understanding)
workflow.add_node("check_goal_completion", check_goal_completion)
workflow.add_node("check_session_completion", check_session_completion)
workflow.add_node("synthesize", synthesize_learning)

workflow.set_entry_point("initialize")
workflow.add_edge("initialize", "start_rubric_conversation")
workflow.add_edge("start_rubric_conversation", "wait_for_response")

workflow.add_edge("wait_for_response", "process_message")
workflow.add_edge("process_message", "evaluate")

workflow.add_conditional_edges(
    "evaluate",
    route_after_evaluation,
    {
        "continue_probing": "wait_for_response",
        "next_item": "check_goal_completion",
    }
)

workflow.add_conditional_edges(
    "check_goal_completion",
    route_goal_completion,
    {
        "next_rubric_item": "start_rubric_conversation",
        "next_goal": "start_rubric_conversation",
        "done": "synthesize"
    }
)

workflow.add_edge("synthesize", END)
```

### Phase 4: API Routes

#### File: `routes/agent_harness.py` (NEW)

**Endpoints:**

```python
POST /submissions/<id>/agent/start
- Create new agent session
- Return session_id, opening messages

POST /submissions/<id>/agent/message
- Send user message
- Process through graph
- Return AI responses, updated progress, gem states

GET /submissions/<id>/agent/progress
- Get all goal progress and gem states
- Return JSON for gems visualization

POST /submissions/<id>/agent/skip
- Override to instructor (requires reason)
- Mark session as overridden
- Allow instructor feedback request

GET /submissions/<id>/agent/can-request-instructor
- Check if student can request instructor feedback
- Return true if: engagement ≥50% OR override used

# Pre-challenge specific
POST /goals/<id>/plan/start
- Create new planning session
- Return session_id, opening messages

POST /goals/<id>/plan/message
- Send user message for planning
- Return AI responses, updated plan coverage

GET /goals/<id>/plan/export
- Export plan as markdown
- Track export analytics

# Voice input specific
POST /agent/voice/transcribe
- Accept audio blob
- Call Whisper API
- Return transcription
```

### Phase 5: Frontend - Gems Visualization

#### File: `static/js/gems-system.js` (NEW)

**Key Features:**
- Orbital gem layout around Sensei avatar
- 4 gem states: locked (gray), in_progress (pulsing blue), engaged (blue), passed (glowing blue)
- Particle effects on state changes
- Tooltips showing goal title + status
- Real-time updates from agent session

**CSS Classes:**
```css
.gem.locked { opacity: 0.3; filter: grayscale(100%); }
.gem.in_progress { animation: pulse 2s infinite; }
.gem.passed { opacity: 1; box-shadow: 0 0 20px blue; animation: glow-blue 2s infinite; }
.gem.engaged { opacity: 1; box-shadow: 0 0 20px purple; animation: glow-purple 2s infinite; }
.gem.expired {
  opacity: 0.6;
  background: linear-gradient(135deg, #f39c12 0%, #f1c40f 100%);
  box-shadow: 0 0 12px rgba(243, 156, 18, 0.4);
  animation: fade-pulse 2s infinite;
}
```

**Expired Gem Display:**
- Button shows "⟳ Renew" badge
- Tooltip: "Expired 5 days ago - click to renew certification"
- Clicking starts re-certification conversation

#### File: `templates/submissions/student_view.html` (MODIFY)

Update existing anatomy section for post-challenge voice-first UI:
```html
<div class="anatomy-section" id="anatomy-section" data-submission-id="{{ submission.id }}">
  <h2>🎤 Talk Through Your Solution</h2>
  <p class="section-description">
    Practice explaining your code like you would to a colleague.
    Engage with at least 50% to unlock instructor feedback.
  </p>

  <div class="anatomy-topics">
    <div class="mastery-indicator">
      MASTERY <span id="gems-display">💎 ○ ○ ○</span>
      (<span id="gem-count">0</span>/4 - unlock 2 for instructor)
    </div>

    <div class="topics-grid" id="topics-grid">
      <!-- Topic buttons populated by JS from API -->
    </div>

    <div class="progress-summary">
      <span id="goals-passed" class="stat-blue">0 mastered</span> ·
      <span id="goals-expired" class="stat-orange">0 expired</span> ·
      <span id="goals-remaining">4 not started</span>
    </div>
  </div>

  <div class="instructor-feedback-section">
    <button id="request-feedback-btn" class="btn btn-secondary" disabled
            title="Explore 50% of concepts to unlock">
      Request Instructor Feedback
    </button>
  </div>
</div>

<style>
.topics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
  margin: 20px 0;
}

.topic-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

.topic-btn:hover {
  border-color: #9b59b6;
  box-shadow: 0 2px 8px rgba(155, 89, 182, 0.2);
}

.topic-btn[data-status="passed"] {
  border-color: #667eea;
  background: #f0f4ff;
}

.topic-btn[data-status="engaged"] {
  border-color: #9b59b6;
  background: #f8f4ff;
}

.gem-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  flex-shrink: 0;
}

.gem-locked { background: #ccc; }
.gem-in-progress { background: #9b59b6; animation: pulse 1.5s infinite; }
.gem-passed { background: #667eea; box-shadow: 0 0 12px rgba(102, 126, 234, 0.5); }
.gem-engaged { background: #9b59b6; box-shadow: 0 0 12px rgba(155, 89, 182, 0.5); }

.stat-blue { color: #667eea; font-weight: 600; }
.stat-purple { color: #9b59b6; font-weight: 600; }
</style>
```

#### File: `templates/goals/goal_detail.html` (MODIFY)

Add pre-challenge planning section with checkmarks:
```html
<div class="challenge-page">
  <h1>{{ goal.title }}</h1>

  {% if goal.video_url %}
  <div class="video-section">
    <iframe src="{{ goal.video_url }}" ...></iframe>
  </div>
  {% endif %}

  <div class="challenge-description">
    {{ goal.challenge_md | markdown }}
  </div>

  <!-- Pre-Coding Learning - Plan Mode -->
  <div class="prepare-section" style="border-left: 4px solid #667eea; padding-left: 20px;">
    <h2>📋 Plan Your Approach</h2>
    <p>Build your implementation plan before you start coding (optional).</p>

    <div class="plan-interface">
      <div class="topics-coverage" id="topics-coverage">
        <h4>COVERAGE (<span id="coverage-count">0</span>/4)</h4>
        <!-- Checkmarks populated by JS -->
      </div>

      <button class="btn btn-primary" onclick="startPlanningSession()">
        Start Planning with Sensei →
      </button>
    </div>
  </div>

  <div class="action-section">
    <a href="{{ url_for('submissions.new_submission', goal_id=goal.id) }}"
       class="btn btn-primary btn-large">
      Start Coding →
    </a>
  </div>
</div>
```

### Phase 6: Instructor Feedback Gating & Re-Certification

#### File: `routes/submissions.py` (MODIFY)

**Update instructor feedback request endpoint with expiration check:**
```python
@submissions_bp.route('/<int:submission_id>/request-feedback', methods=['POST'])
@login_required
def request_instructor_feedback(submission_id):
    submission = Submission.query.get_or_404(submission_id)

    can_request, details = can_request_instructor_feedback(current_user.id, submission.goal_id)

    if not can_request:
        return jsonify({
            'error': 'Please complete the guided learning journey first',
            'required_engagement': 0.5,
            'current_engagement': details['current_engagement'],
            'valid_gems': details['valid_count'],
            'expired_gems': details['expired_count'],
            'total_gems': details['total_count'],
            'message': 'Explore at least 50% of concepts (with current certification) to unlock instructor feedback'
        }), 403

    submission.status = 'feedback_requested'
    db.session.commit()

    return jsonify({'success': True})

def can_request_instructor_feedback(user_id, learning_goal_id):
    """Check if student has met engagement threshold with non-expired gems."""
    from datetime import datetime

    core_goals = CoreLearningGoal.query.filter_by(learning_goal_id=learning_goal_id).all()
    total_count = len(core_goals)

    if total_count == 0:
        return True, {}

    progress_records = GoalProgress.query.filter_by(
        user_id=user_id,
        learning_goal_id=learning_goal_id
    ).all()

    progress_map = {p.core_goal_id: p for p in progress_records}

    valid_count = 0
    expired_count = 0

    for core_goal in core_goals:
        progress = progress_map.get(core_goal.id)

        if not progress or progress.status == 'locked':
            continue

        if progress.expires_at and progress.expires_at < datetime.utcnow():
            expired_count += 1
        elif progress.status in ['passed', 'engaged']:
            valid_count += 1

    current_engagement = valid_count / total_count

    can_request = current_engagement >= 0.5

    details = {
        'current_engagement': current_engagement,
        'valid_count': valid_count,
        'expired_count': expired_count,
        'total_count': total_count
    }

    return can_request, details
```

### Phase 7: Rubric Creation for Flask API Auth

#### File: `seed_data.py` (MODIFY)

Add initial rubrics for API Authentication learning goal:

```python
def create_core_learning_goals():
    """Create core learning goals with rubrics."""

    api_auth_goal = LearningGoal.query.filter_by(title="API Authentication Challenge").first()

    if not api_auth_goal:
        return

    # Core Learning Goal 1: Authentication Basics
    goal1 = CoreLearningGoal(
        learning_goal_id=api_auth_goal.id,
        title="Authentication Fundamentals",
        description="Understand what authentication is and why it's needed in APIs",
        certification_days=30,  # Fundamental concept - monthly renewal
        rubric_json=json.dumps({
            "items": [
                {
                    "id": "auth_definition",
                    "criterion": "Can explain what authentication means in the context of APIs",
                    "pass_indicators": [
                        "Explains that authentication verifies user identity",
                        "Distinguishes authentication from authorization",
                        "Can relate to real-world examples (login, passwords)"
                    ],
                    "socratic_hints": [
                        "What problem does authentication solve in your API?",
                        "Think about when you log into a website - what's the server checking?",
                        "In your code, how does the API know who is making the request?"
                    ]
                },
                {
                    "id": "auth_necessity",
                    "criterion": "Can explain why APIs need authentication",
                    "pass_indicators": [
                        "Identifies security risks without authentication",
                        "Explains concept of protected resources",
                        "Connects to their implementation"
                    ],
                    "socratic_hints": [
                        "What could go wrong if anyone could access any user's data?",
                        "Look at your API endpoints - which ones should be public vs private?",
                        "What happens in your code when someone accesses a protected route?"
                    ]
                }
            ]
        }),
        order_index=1,
        gem_color='blue'
    )

    # Core Learning Goal 2: Session Management
    goal2 = CoreLearningGoal(
        learning_goal_id=api_auth_goal.id,
        title="Session Management",
        description="Understand how sessions maintain authentication state",
        certification_days=90,  # Standard - quarterly renewal
        rubric_json=json.dumps({
            "items": [
                {
                    "id": "session_concept",
                    "criterion": "Can explain what a session is and how it works",
                    "pass_indicators": [
                        "Explains sessions maintain state between requests",
                        "Understands session IDs and cookies",
                        "Can trace session flow in their code"
                    ],
                    "socratic_hints": [
                        "HTTP is stateless - how does the server remember you logged in?",
                        "Look at your code - what happens after successful login?",
                        "Where is the session information stored?"
                    ]
                },
                {
                    "id": "session_security",
                    "criterion": "Understands session security considerations",
                    "pass_indicators": [
                        "Knows sessions should be secure/httponly",
                        "Understands session expiration",
                        "Can identify session hijacking risks"
                    ],
                    "socratic_hints": [
                        "What could go wrong if someone stole your session cookie?",
                        "Why do websites log you out after a while?",
                        "In your code, how are sessions protected?"
                    ]
                }
            ]
        }),
        order_index=2,
        gem_color='blue'
    )

    # Core Learning Goal 3: Password Security
    goal3 = CoreLearningGoal(
        learning_goal_id=api_auth_goal.id,
        title="Password Security",
        description="Understand secure password handling",
        certification_days=60,  # Security-critical - bi-monthly renewal
        rubric_json=json.dumps({
            "items": [
                {
                    "id": "password_hashing",
                    "criterion": "Can explain why passwords must be hashed",
                    "pass_indicators": [
                        "Explains hashing is one-way transformation",
                        "Understands passwords should never be stored in plaintext",
                        "Can find hashing in their code"
                    ],
                    "socratic_hints": [
                        "Why can't you just store passwords as-is in the database?",
                        "If a database gets stolen, what protects the passwords?",
                        "Look at your registration code - what happens to the password before it's saved?"
                    ]
                },
                {
                    "id": "password_verification",
                    "criterion": "Understands how password verification works with hashes",
                    "pass_indicators": [
                        "Explains you hash the login attempt and compare hashes",
                        "Understands you can't reverse a hash",
                        "Can trace verification in their login code"
                    ],
                    "socratic_hints": [
                        "If passwords are hashed, how does the login check if it's correct?",
                        "Can you un-hash a password to check it? Why or why not?",
                        "In your login route, how is the password checked?"
                    ]
                }
            ]
        }),
        order_index=3,
        gem_color='blue'
    )

    # Core Learning Goal 4: Authorization
    goal4 = CoreLearningGoal(
        learning_goal_id=api_auth_goal.id,
        title="Authorization & Access Control",
        description="Understand the difference between authentication and authorization",
        certification_days=90,  # Standard - quarterly renewal
        rubric_json=json.dumps({
            "items": [
                {
                    "id": "authn_vs_authz",
                    "criterion": "Can distinguish authentication from authorization",
                    "pass_indicators": [
                        "Explains authentication is 'who are you'",
                        "Explains authorization is 'what can you do'",
                        "Can give examples of each"
                    ],
                    "socratic_hints": [
                        "Once you're logged in, does that mean you can do everything?",
                        "Think about a banking app - what's the difference between proving you're you vs being allowed to transfer money?",
                        "In your code, where do you check who someone is vs what they can access?"
                    ]
                },
                {
                    "id": "protected_routes",
                    "criterion": "Understands how to protect routes/resources",
                    "pass_indicators": [
                        "Can explain decorators like @login_required",
                        "Understands middleware checks",
                        "Can identify protected vs public endpoints in their code"
                    ],
                    "socratic_hints": [
                        "What happens if you try to access /profile without logging in?",
                        "Look at the @login_required decorator - what do you think it does?",
                        "Which of your API endpoints should anyone be able to access?"
                    ]
                }
            ]
        }),
        order_index=4,
        gem_color='blue'
    )

    db.session.add_all([goal1, goal2, goal3, goal4])
    db.session.commit()
```

---

## Files to Create/Modify

### New Files - Services
- `services/socratic_harness_base.py` - Shared base class for both harnesses
- `services/planning_harness.py` - Pre-challenge plan creation harness
- `services/articulation_harness.py` - Post-challenge voice-first harness
- `services/whisper_transcription.py` - Whisper API integration

### New Files - Frontend
- `static/js/voice-input.js` - Voice recording and Whisper transcription
- `static/js/plan-generator.js` - Plan artifact generation from conversation
- `static/js/plan-editor.js` - Rich text editor for plan refinement
- `static/js/checkmarks-ui.js` - Plan coverage checkmarks (pre-challenge)
- `static/js/gems-ui.js` - Mastery gems display (post-challenge)
- `templates/components/voice_input_modal.html` - Voice input UI
- `templates/components/plan_editor.html` - Editable plan panel

### New Files - Models
- `models/core_learning_goal.py` - Rubric-based learning goals
- `models/goal_progress.py` - Tracks rubric evaluation and attempts
- `models/agent_session.py` - Agent session state
- `models/challenge_plan.py` - Plan artifacts

### Modified Files
- `services/socratic_chat.py` - Add @traceable decorators + rubric_context parameter
- `routes/agent_harness.py` - Separate endpoints for planning vs articulation
- `routes/submissions.py` - Add engagement gating for instructor feedback
- `templates/submissions/student_view.html` - Voice-first UI with gems
- `templates/goals/goal_detail.html` - Plan building UI with checkmarks
- `static/js/agent-harness-ui.js` - Mode-specific UI rendering
- `app.py` - Register agent_harness blueprint
- `config.py` - Add LangSmith config + Whisper API config
- `requirements.txt` - Add LangChain dependencies + openai (for Whisper)
- `seed_data.py` - Add rubric creation

### Database Migration
- Create `challenge_plans` table
- Create `voice_input_metrics` table
- Add `input_mode`, `voice_duration_seconds`, `original_transcription` to `agent_messages`
- Add `harness_type` to `agent_sessions`

---

## Implementation Order

1. **Database & Models** (Phase 1)
   - Create new tables
   - Create new models
   - Run migration

2. **LangSmith Setup** (Phase 2)
   - Add dependencies
   - Configure environment
   - Add tracing to existing services

3. **Agent Harness Backend** (Phase 3)
   - Implement shared base class
   - Build PlanningHarness
   - Build ArticulationHarness
   - Implement rubric evaluation

4. **API Routes** (Phase 4)
   - Create agent_harness.py routes
   - Add planning endpoints
   - Add voice transcription endpoint
   - Modify submissions.py for gating

5. **Frontend** (Phase 5)
   - Build checkmarks UI (pre-challenge)
   - Build gems visualization (post-challenge)
   - Build voice input modal
   - Build plan editor
   - Update templates

6. **Rubrics & Seed Data** (Phase 6)
   - Create Flask API Auth rubrics
   - Update seed data

7. **Testing & Iteration**
   - Test full planning flow
   - Test full articulation flow
   - Verify voice transcription
   - Test engagement gating
   - **Run LangSmith integration tests locally**:
     ```bash
     export LANGCHAIN_TRACING_V2=true
     export LANGCHAIN_API_KEY=your_key
     export LANGCHAIN_PROJECT=code-dojo-local-test
     pytest tests/integration/test_langsmith_tracing.py -v
     ```
   - Verify traces appear in LangSmith dashboard with correct hierarchy

---

## Verification

1. **Pre-Challenge Planning Harness**
   - Start planning session on challenge page
   - Verify Socratic dialogue focuses on planning approach
   - Check checkmarks update as concepts are covered in plan
   - Edit generated plan in rich text editor
   - Export plan and verify format works in coding tools (Claude, Cursor)
   - Verify `challenge_plans` record created with coverage_json

2. **Post-Challenge Articulation Harness**
   - Submit code, enter articulation dialogue
   - Verify voice prompt appears first and prominently
   - Test voice recording with Whisper transcription
   - Verify student can review/edit transcription
   - Test fallback to text input
   - Verify gems unlock on successful articulation
   - Confirm 50% gems required for instructor feedback

3. **UI Differentiation**
   - Pre-challenge shows blue/teal theme with blueprint icon
   - Pre-challenge shows checkmarks (not gems)
   - Post-challenge shows purple/warm theme with mic icon
   - Post-challenge shows gems (not checkmarks)
   - Each mode has distinct Sensei tone

4. **Analytics**
   - Voice skip rate metrics populate correctly
   - Plan export and iteration tracking works
   - Coverage vs mastery metrics separate

5. **LangSmith Tracing (Local Integration Tests - Fully Automated)**
   - Run integration tests locally: `pytest tests/integration/test_langsmith_tracing.py -v`
   - All verification is done programmatically via LangSmith API (no manual dashboard checking required)
   - Tests verify:
     - planning_harness_orchestration traces appear with child conversation traces
     - articulation_harness_orchestration traces include whisper_transcribe spans
     - evaluate_rubric_item traces capture pass/fail results in outputs
     - Trace hierarchy matches expected structure
     - Metadata tagging: `harness_type`, `input_mode`, `user_id`, `goal_id`
     - Trace content downloaded and validated via API assertions

---

## Success Criteria

- [x] Pre-challenge plan building works with checkmarks for coverage *(Backend API implemented, frontend JS ready)*
- [x] Plan is fully editable and exportable for agentic coding tools *(PlanEditor.js + API endpoints)*
- [x] Post-challenge voice input works as primary method (Whisper API) *(whisper_transcription.py service)*
- [x] Text fallback works when student declines voice *(VoiceInput.js with fallback)*
- [x] Voice skip rate metrics are tracked *(voice_input_metrics table + service)*
- [x] Agent guides through rubric items with Socratic questions *(ArticulationHarness + rubric_context)*
- [x] Rubric evaluation works correctly (binary pass/fail) *(evaluate_rubric_item function)*
- [x] 3-attempt limit enforced per rubric item *(GoalProgress.mark_item_passed)*
- [x] Gems show correct states (locked, in-progress, passed, engaged, expired) *(GemsUI.js)*
- [x] Expiration dates calculated correctly based on certification_days *(GoalProgress.set_expiration)*
- [x] Expired gems show yellow/orange with "⟳ Renew" badge *(CSS + GemsUI)*
- [x] Re-certification flow works (updates expires_at, certification_count) *(GoalProgress model)*
- [x] Only non-expired gems count toward 50% instructor unlock *(check_instructor_unlock_threshold)*
- [x] Admin can configure certification periods per concept *(CoreLearningGoal.certification_days)*
- [x] Pre-coding learning persists to post-submission (within expiration) *(goal_progress table)*
- [ ] Topic switching works mid-conversation *(Partial - needs UI testing)*
- [x] UI clearly differentiates pre-challenge (blue/checkmarks) from post-challenge (purple/gems/voice) *(CSS variables + separate JS components)*
- [x] LangSmith captures all AI interactions *(@traceable decorators on all AI calls)*
- [x] Gems visualization updates in real-time *(GemsUI.updateFromAPI)*

---

## LangSmith Integration Testing

### Overview
Verify that all orchestration and conversation events are properly traced to LangSmith using the LangSmith API. Tests should be rate-limit aware and comprehensive enough to validate the full agent flow.

### Test Configuration

```python
# tests/conftest.py
import os
import pytest
from langsmith import Client
import time

@pytest.fixture(scope="session")
def langsmith_client():
    """LangSmith client for verification tests."""
    return Client(api_key=os.getenv('LANGSMITH_API_KEY'))

@pytest.fixture(scope="session")
def test_project_name():
    """Unique project name for test isolation."""
    return f"code-dojo-test-{int(time.time())}"

@pytest.fixture(autouse=True)
def rate_limit_buffer():
    """Pause between tests to respect API rate limits."""
    yield
    time.sleep(0.5)  # 500ms buffer between tests
```

### Integration Test: Full Agent Orchestration Flow

```python
# tests/integration/test_langsmith_tracing.py
import pytest
from datetime import datetime, timedelta

class TestLangSmithTracing:
    """Verify LangSmith captures all agent harness traces."""

    def test_planning_harness_traces_complete_flow(
        self, langsmith_client, test_project_name, test_user, test_goal
    ):
        """Verify planning harness generates expected trace hierarchy."""
        from services.planning_harness import PlanningHarness

        harness = PlanningHarness(
            learning_goal_id=test_goal.id,
            user_id=test_user.id,
            langsmith_project=test_project_name
        )

        # Execute one complete rubric item flow
        harness.start_session()
        harness.process_message("I'll start by setting up authentication routes")
        harness.process_message("The API should verify credentials against the database")

        time.sleep(2)  # Allow traces to propagate

        # Verify trace structure via LangSmith API
        runs = list(langsmith_client.list_runs(
            project_name=test_project_name,
            start_time=datetime.utcnow() - timedelta(minutes=5),
            limit=20
        ))

        # Verify parent orchestration run exists
        orchestration_runs = [r for r in runs if r.name == "planning_harness_orchestration"]
        assert len(orchestration_runs) >= 1, "Missing orchestration parent trace"

        # Verify child conversation runs
        conversation_runs = [r for r in runs if r.name == "socratic_chat_message"]
        assert len(conversation_runs) >= 2, "Missing conversation traces"

        # Verify evaluation runs
        eval_runs = [r for r in runs if r.name == "evaluate_plan_coverage"]
        assert len(eval_runs) >= 1, "Missing plan coverage evaluation trace"

    def test_articulation_harness_traces_voice_input(
        self, langsmith_client, test_project_name, test_user, test_submission
    ):
        """Verify articulation harness traces voice transcription."""
        from services.articulation_harness import ArticulationHarness

        harness = ArticulationHarness(
            submission_id=test_submission.id,
            user_id=test_user.id,
            langsmith_project=test_project_name
        )

        harness.start_session()
        harness.process_voice_input(audio_data=b"fake_audio", input_mode="voice")

        time.sleep(2)

        runs = list(langsmith_client.list_runs(
            project_name=test_project_name,
            start_time=datetime.utcnow() - timedelta(minutes=5),
            limit=20
        ))

        # Verify whisper transcription is traced
        whisper_runs = [r for r in runs if r.name == "whisper_transcribe"]
        assert len(whisper_runs) >= 1, "Missing Whisper transcription trace"

    def test_rubric_evaluation_traces_binary_result(
        self, langsmith_client, test_project_name
    ):
        """Verify rubric evaluation traces capture pass/fail result."""
        from services.agent_harness import evaluate_rubric_item

        rubric_item = {
            "criterion": "Can explain authentication",
            "pass_indicators": ["Verifies identity", "Distinguishes from authorization"]
        }

        evaluate_rubric_item(
            student_response="Authentication verifies who you are",
            rubric_item=rubric_item,
            langsmith_project=test_project_name
        )

        time.sleep(2)

        runs = list(langsmith_client.list_runs(
            project_name=test_project_name,
            filter='name == "evaluate_rubric_item"',
            limit=5
        ))

        assert len(runs) >= 1, "Missing evaluation trace"
        assert "passed" in str(runs[0].outputs), "Missing pass/fail in output"


class TestTraceContentVerification:
    """Download and validate trace content via LangSmith API - no manual dashboard needed."""

    def test_trace_hierarchy_parent_child_relationships(
        self, langsmith_client, test_project_name, test_user, test_goal
    ):
        """Verify trace parent-child relationships are correct."""
        from services.planning_harness import PlanningHarness

        harness = PlanningHarness(
            learning_goal_id=test_goal.id,
            user_id=test_user.id,
            langsmith_project=test_project_name
        )
        harness.start_session()
        harness.process_message("Testing hierarchy")

        time.sleep(2)

        runs = list(langsmith_client.list_runs(
            project_name=test_project_name,
            start_time=datetime.utcnow() - timedelta(minutes=5),
            limit=20
        ))

        # Find orchestration parent
        orchestration = next((r for r in runs if r.name == "planning_harness_orchestration"), None)
        assert orchestration is not None, "Missing orchestration run"

        # Verify child runs reference parent
        child_runs = [r for r in runs if r.parent_run_id == orchestration.id]
        assert len(child_runs) >= 1, f"No child runs found under orchestration {orchestration.id}"

        # Verify child run names
        child_names = {r.name for r in child_runs}
        assert "socratic_chat_start" in child_names or "socratic_chat_message" in child_names

    def test_trace_inputs_outputs_captured(
        self, langsmith_client, test_project_name, test_user, test_goal
    ):
        """Verify trace inputs and outputs contain expected data."""
        from services.planning_harness import PlanningHarness

        test_message = "I'll implement password hashing with bcrypt"

        harness = PlanningHarness(
            learning_goal_id=test_goal.id,
            user_id=test_user.id,
            langsmith_project=test_project_name
        )
        harness.start_session()
        harness.process_message(test_message)

        time.sleep(2)

        runs = list(langsmith_client.list_runs(
            project_name=test_project_name,
            filter='name == "socratic_chat_message"',
            limit=5
        ))

        assert len(runs) >= 1, "Missing conversation trace"
        run = runs[0]

        # Verify inputs contain student message
        assert run.inputs is not None, "Run inputs not captured"
        assert test_message in str(run.inputs), "Student message not in trace inputs"

        # Verify outputs contain assistant response
        assert run.outputs is not None, "Run outputs not captured"
        assert len(str(run.outputs)) > 0, "Empty assistant response in outputs"

    def test_metadata_tagging_complete(
        self, langsmith_client, test_project_name, test_user, test_goal
    ):
        """Verify metadata tags are present for filtering and analytics."""
        from services.planning_harness import PlanningHarness

        harness = PlanningHarness(
            learning_goal_id=test_goal.id,
            user_id=test_user.id,
            langsmith_project=test_project_name
        )
        harness.start_session()

        time.sleep(2)

        runs = list(langsmith_client.list_runs(
            project_name=test_project_name,
            filter='name == "planning_harness_orchestration"',
            limit=5
        ))

        assert len(runs) >= 1
        run = runs[0]

        # Verify required metadata
        metadata = run.extra.get("metadata", {})
        assert metadata.get("harness_type") == "planning", "Missing harness_type metadata"
        assert metadata.get("user_id") == test_user.id, "Missing user_id metadata"
        assert metadata.get("goal_id") == test_goal.id, "Missing goal_id metadata"

    def test_full_conversation_flow_traced(
        self, langsmith_client, test_project_name, test_user, test_goal
    ):
        """Verify complete multi-turn conversation is captured."""
        from services.planning_harness import PlanningHarness

        harness = PlanningHarness(
            learning_goal_id=test_goal.id,
            user_id=test_user.id,
            langsmith_project=test_project_name
        )

        # Multi-turn conversation
        harness.start_session()
        harness.process_message("First, I need to understand authentication basics")
        harness.process_message("So authentication verifies the user's identity")
        harness.process_message("And that's different from authorization which checks permissions")

        time.sleep(3)

        runs = list(langsmith_client.list_runs(
            project_name=test_project_name,
            filter='name == "socratic_chat_message"',
            limit=10
        ))

        # Verify all 3 message turns were traced
        assert len(runs) >= 3, f"Expected 3+ conversation traces, got {len(runs)}"

        # Verify traces are ordered (most recent first in list)
        for run in runs:
            assert run.inputs is not None
            assert run.outputs is not None
```

### Rate Limit Handling

```python
# tests/conftest.py
import functools

def rate_limited(max_per_minute=20):
    """Decorator to enforce rate limits on LangSmith API calls."""
    min_interval = 60.0 / max_per_minute
    last_call = [0.0]

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_call[0]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            last_call[0] = time.time()
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

### Expected Trace Hierarchy

```
planning_harness_orchestration (parent)
├── socratic_chat_start
│   └── claude_api_call
├── socratic_chat_message
│   └── claude_api_call
├── evaluate_plan_coverage
│   └── claude_api_call
└── socratic_chat_message
    └── claude_api_call

articulation_harness_orchestration (parent)
├── whisper_transcribe
│   └── openai_api_call
├── socratic_chat_message
│   └── claude_api_call
└── evaluate_rubric_item
    └── claude_api_call
```

### CI Configuration

```yaml
# .github/workflows/test.yml (excerpt)
integration-tests:
  env:
    LANGCHAIN_TRACING_V2: "true"
    LANGCHAIN_API_KEY: ${{ secrets.LANGSMITH_API_KEY }}
    LANGCHAIN_PROJECT: "code-dojo-ci-${{ github.run_id }}"
  steps:
    - run: pytest tests/integration/test_langsmith_tracing.py -v -x
```

---

## Future Enhancements

1. **Context-Aware Suggestions** - When student submits code with new patterns, suggest revisiting concepts in new context: "Your new code uses JWT tokens - want to revisit authentication in this context?"
2. **Adaptive Rubrics** - LLM generates rubrics from challenge descriptions
3. **Sentiment Analysis** - More sophisticated frustration detection
4. **Orbital Gem Visualization** - Visual gems ring around Sensei avatar (currently just gem icons on buttons)
5. **Instructor Analytics** - Dashboard showing student engagement patterns across cohorts
6. **A/B Testing** - Experiment with different rubric stringency levels
7. **Multi-modal Evidence** - Accept code snippets as demonstration of understanding
8. **Spaced Repetition Reminders** - Optional nudges to revisit concepts after time
9. **AI-Detected Anatomy Topics** - Keep AI pattern detection for supplementary discussion topics beyond core rubrics
