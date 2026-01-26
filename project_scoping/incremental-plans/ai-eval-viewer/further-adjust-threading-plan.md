# Plan: Fix LangSmith Tracing to Group Traces as Threads

## LangSmith Docs on Threads

Read here for detailed instrutions on implementing threads: 


https://docs.langchain.com/langsmith/threads

## Problem

The AI Eval Viewer shows individual traces instead of grouped threads because each `@traceable` decorated function in the articulation harness creates an independent top-level trace. The traces don't share a common `trace_id` or have `parent_run_id` relationships.

**Current behavior:**
- `start_session()` → independent trace #1
- `process_message()` → independent trace #2
- `evaluate_rubric_item()` → independent trace #3
- Each appears as a separate "thread" in the viewer

**Expected behavior:**
- One parent trace for the entire session (`articulation_harness_orchestration`)
- Child traces nested underneath sharing the same `trace_id`
- Hierarchical span tree visible in AI Eval Viewer

## Solution: Use LangSmith Context Manager for Parent-Child Tracing

LangSmith's `trace()` context manager automatically propagates trace context. Child `@traceable` calls inherit the parent's `trace_id` and set `parent_run_id`.

## Files to Modify

| File | Changes |
|------|---------|
| `services/articulation_harness.py` | Add parent trace context management |
| `models/agent_session.py` | Already has `langsmith_run_id` field (line 22) - will populate it |
| `tests/test_articulation_traces.py` | Add test for trace grouping verification |

## Implementation Steps

### Step 1: Modify ArticulationHarness to Create Parent Trace

**File:** `services/articulation_harness.py`

```python
# Add import
from langsmith import trace

class ArticulationHarness(SocraticHarnessBase):
    def __init__(self, submission_id, user_id, langsmith_project=None):
        # ... existing init ...
        self._session_trace_context = None  # Store the trace context manager

    def start_session(self, focus_goal_id=None):
        # Remove @traceable decorator - we create the trace manually

        # Create parent trace context
        self._session_trace_context = trace(
            name="articulation_harness_orchestration",
            metadata={
                "harness_type": "articulation",
                "user_id": self.user_id,
                "submission_id": self.submission_id,
                "learning_goal_id": self.learning_goal_id
            }
        )
        run_tree = self._session_trace_context.__enter__()

        # ... existing session creation logic ...

        # Store the trace ID in the database
        self.session.langsmith_run_id = str(run_tree.id)
        db.session.commit()

        return {...}

    # Keep @traceable on process_message - it will auto-nest under parent
    @traceable(name="articulation_message_process", metadata={"harness_type": "articulation"})
    def process_message(self, user_message, ...):
        # ... existing logic (unchanged) ...

    def end_session(self):
        result = self._end_session_impl()

        # Close the parent trace context
        if self._session_trace_context:
            self._session_trace_context.__exit__(None, None, None)
            self._session_trace_context = None

        return result
```

### Step 2: Add Error Handling for Trace Context

Ensure traces close properly even on exceptions:

```python
def process_message(self, user_message, ...):
    try:
        return self._process_message_impl(user_message, ...)
    except Exception as e:
        # Log error to trace
        raise

def end_session(self):
    try:
        # ... existing end logic ...
    finally:
        if self._session_trace_context:
            self._session_trace_context.__exit__(None, None, None)
            self._session_trace_context = None
```

### Step 3: Add Integration Test for Thread Grouping

**File:** `tests/test_articulation_traces.py`

```python
class TestArticulationTraceGrouping:
    """Tests that verify trace hierarchy is correctly created."""

    @pytest.mark.integration
    def test_traces_share_trace_id(self, langsmith_enabled, articulation_test_data, client):
        """Verify all traces from a session share the same trace_id."""
        with app.app_context():
            data = articulation_test_data
            harness = ArticulationHarness(data['submission'].id, data['user'].id)

            session = harness.start_session()
            harness.process_message("1", input_mode='text')
            harness.process_message("Test explanation", input_mode='text')
            harness.end_session()

            # Verify langsmith_run_id was populated
            from models.agent_session import AgentSession
            db_session = AgentSession.query.get(session['session_id'])
            assert db_session.langsmith_run_id is not None

            # Wait for traces to sync, then query LangSmith
            time.sleep(3)

            from langsmith import Client
            ls_client = Client()
            runs = list(ls_client.list_runs(
                project_name='code-dojo-tests',
                filter=f'eq(trace_id, "{db_session.langsmith_run_id}")',
                limit=20
            ))

            # Should have parent + child traces
            assert len(runs) >= 2, f"Expected grouped traces, got {len(runs)}"

            # Verify hierarchy
            parent_runs = [r for r in runs if r.parent_run_id is None]
            assert len(parent_runs) == 1
            assert parent_runs[0].name == "articulation_harness_orchestration"
```

## Verification

After implementation:

1. **Run integration tests:**
   ```bash
   cd /Users/nathansuberi/Documents/GitHub/code-dojo
   source venv/bin/activate
   pytest tests/test_articulation_traces.py -v -s -m integration
   ```

2. **Check AI Eval Viewer:**
   - Open http://localhost:5173
   - Navigate to Digi-Trainer feature
   - Verify threads show ONE entry per session (not per message)
   - Click a thread to see nested span tree:
     ```
     articulation_harness_orchestration (parent)
     ├── articulation_message_process
     │   └── evaluate_rubric_item
     ├── articulation_message_process
     │   └── evaluate_rubric_item
     └── ...
     ```

3. **Verify database:**
   ```python
   from models.agent_session import AgentSession
   session = AgentSession.query.first()
   print(session.langsmith_run_id)  # Should have a UUID
   ```

## Key Points

- **Why context manager?** LangSmith's `trace()` context automatically sets `trace_id` and `parent_run_id` for nested `@traceable` calls
- **Why remove @traceable from start_session?** We need manual control to keep the context open across multiple method calls
- **Keep @traceable on process_message** - it will automatically nest under the active parent context
- **langsmith_run_id field already exists** - just needs to be populated (line 22 in agent_session.py)
