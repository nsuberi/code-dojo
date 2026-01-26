# Plan: Implement Topic-Level Threads in Articulation Harness

## Problem Summary

The AI Eval Viewer shows traces but not properly scoped **threads**. Currently:
- One trace per **session** (`articulation_harness_orchestration`)
- One trace per **message** (`articulation_message_process`)

**User requirement:** A thread should represent a **single topic conversation** - from when a user selects a goal until it completes (understanding), fails (lack of understanding), or ends via frustration.

## Current Conversation Flow

```
Session starts
├─ User selects Topic 1 (_focus_on_goal)
│  ├─ Message 1 (articulation_message_process)
│  ├─ Message 2 (articulation_message_process)
│  └─ Topic ends: passed/engaged/frustrated (_goal_completed or _handle_frustration_and_end_topic)
├─ User selects Topic 2 (_focus_on_goal)
│  ├─ Message 3 (articulation_message_process)
│  └─ Topic ends
└─ Session ends (end_session)
```

**Desired thread structure:** Each topic (Topic 1, Topic 2) should be its own thread containing all its messages.

---

## Solution: Add Topic-Level Trace Context

Create a new trace when a topic begins (`_focus_on_goal`) and close it when the topic ends (`_goal_completed`, `_handle_frustration_and_end_topic`).

### Changes Required

#### 1. Add Topic Trace Management to ArticulationHarness

**File:** `services/articulation_harness.py`

Add new instance variables:
```python
def __init__(self, ...):
    ...
    self._topic_trace_context = None  # Trace context for current topic
    self._topic_thread_id = None      # Thread ID for current topic
```

#### 2. Create Topic Trace on Goal Focus

**File:** `services/articulation_harness.py`
**Method:** `_focus_on_goal()` (line 269)

```python
def _focus_on_goal(self, goals, goal_index, introduce=False):
    """Focus the conversation on explaining a specific goal."""
    goal = goals[goal_index]

    # Close any existing topic trace
    if self._topic_trace_context:
        self._topic_trace_context.__exit__(None, None, None)

    # Create new topic thread ID
    self._topic_thread_id = str(uuid.uuid4())

    # Start topic trace
    self._topic_trace_context = trace(
        name="articulation_topic_conversation",
        metadata={
            "topic_thread_id": self._topic_thread_id,
            "session_id": self._thread_id,  # Link to parent session
            "goal_id": goal['id'],
            "goal_title": goal['title'],
            "harness_type": "articulation"
        }
    )
    self._topic_trace_context.__enter__()

    # ... rest of existing code
```

#### 3. Close Topic Trace on Completion

**File:** `services/articulation_harness.py`
**Methods:** `_goal_completed()` (line 484) and `_handle_frustration_and_end_topic()` (line 305)

Add at the end of each method:
```python
def _goal_completed(self, completed_goal, all_goals, status):
    # ... existing code ...

    # Close topic trace with outcome
    self._close_topic_trace(completed_goal, status)

    return {...}

def _close_topic_trace(self, goal, status):
    """Close the current topic trace."""
    if self._topic_trace_context:
        # Add outcome to trace metadata
        self._topic_trace_context.__exit__(None, None, None)
        self._topic_trace_context = None
        self._topic_thread_id = None
```

#### 4. Update Message Traces to Use Topic Thread ID

**File:** `services/articulation_harness.py`
**Method:** `process_message()` (line 172)

Update trace metadata to include topic thread ID:
```python
with trace(
    name="articulation_message_process",
    metadata={
        "topic_thread_id": self._topic_thread_id,  # ADD: Link to topic thread
        "session_id": self._thread_id,
        "harness_type": "articulation",
        "input_mode": input_mode,
        "frustration_detected": is_frustrated
    }
):
```

#### 5. Persist Topic State Across Requests

**File:** `routes/agent_harness.py`
**Lines:** 244-251, 278-285

When reconstructing harness, restore topic state:
```python
harness = ArticulationHarness(...)
harness.session = session
harness._thread_id = session.langsmith_run_id
# Note: _topic_thread_id would need to be stored in AgentSession if persistence is needed
```

**Option A:** Store `current_topic_thread_id` in AgentSession model
**Option B:** Generate new topic thread on each request (lose continuity for HTTP boundary crossings)

#### 6. Update Viewer to Filter by Topic Traces

**File:** `ai-eval-viewer/src/services/langsmith.ts`
**Lines:** 41-47

```typescript
{
  id: 'digi-trainer',
  name: 'Digi-Trainer',
  description: 'Articulation practice for code explanation',
  traceNamePatterns: ['articulation_topic_conversation'],  // Change to topic-level trace
},
```

#### 7. Update Viewer to Fetch Child Spans by Topic Thread ID

**File:** `ai-eval-viewer/src/services/langsmith.ts`
**Method:** `getChildRuns()` (line 239)

Query by `topic_thread_id` metadata instead of `trace_id`:
```typescript
export async function getChildRuns(topicThreadId: string): Promise<LangSmithRun[]> {
  const { runs } = await queryRuns({
    filter: `and(in(metadata_key, ["topic_thread_id"]), eq(metadata_value, "${topicThreadId}"))`,
    limit: 100,
  });
  return runs;
}
```

---

## Database Schema Addition (Optional)

If topic thread persistence across requests is needed:

**File:** `models/agent_session.py`

```python
class AgentSession(db.Model):
    ...
    current_topic_thread_id = db.Column(db.String(100))  # ADD: Current topic's thread ID
```

---

## Files to Modify

| File | Change |
|------|--------|
| `services/articulation_harness.py` | Add topic trace lifecycle (`_topic_trace_context`, `_topic_thread_id`) |
| `services/articulation_harness.py` | Create trace in `_focus_on_goal()` |
| `services/articulation_harness.py` | Close trace in `_goal_completed()` and `_handle_frustration_and_end_topic()` |
| `services/articulation_harness.py` | Update `process_message()` metadata |
| `routes/agent_harness.py` | Restore `_thread_id` and optionally `_topic_thread_id` on reconstruction |
| `models/agent_session.py` | (Optional) Add `current_topic_thread_id` column |
| `ai-eval-viewer/src/services/langsmith.ts` | Change `traceNamePatterns` to `['articulation_topic_conversation']` |
| `ai-eval-viewer/src/services/langsmith.ts` | Update `getChildRuns()` to query by `topic_thread_id` metadata |

---

## Thread Outcome Visibility

Each topic thread will have clear outcome in its trace:

| Outcome | Trigger | Status in Trace |
|---------|---------|-----------------|
| **Understanding** | All rubric items passed | `status: 'passed'`, 💎 gem awarded |
| **Lack of understanding** | Max attempts reached | `status: 'engaged'`, 🔵 needs work |
| **Frustration** | Frustration signals detected | `status: 'engaged'`, `frustration_detected: true` |

---

## Verification Steps

1. Run harness backend: `flask run`
2. Start an articulation session
3. Select a topic and complete it (pass or engage)
4. Select another topic
5. In AI Eval Viewer:
   - Each topic should appear as a separate thread
   - Thread name: `articulation_topic_conversation`
   - Clicking a thread shows message spans nested inside
   - Metadata shows `goal_title`, `status`, and `frustration_detected` where applicable
