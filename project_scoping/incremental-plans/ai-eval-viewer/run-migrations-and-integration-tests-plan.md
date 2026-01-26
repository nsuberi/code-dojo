# Plan: Migration & Integration Test Verification for Topic-Level Threads

## Status: Implementation Complete → Migration & Verification Required

The topic-level threads feature has been implemented. Now we need to:
1. Create and run the database migration
2. Run integration tests to generate topic-level traces
3. Run Playwright tests to verify the viewer displays them correctly

---

## Step 1: Create Database Migration

**Create file:** `migrations/add_topic_thread_id.py`

```python
"""Migration to add current_topic_thread_id column to agent_sessions table.

This column stores the current topic's thread ID for trace continuity
across HTTP request boundaries in the articulation harness.

Usage:
    python migrations/add_topic_thread_id.py
    python migrations/add_topic_thread_id.py --rollback
"""

import os
import sys
import sqlite3

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from config import Config


def get_db_path():
    """Get database path from Flask config."""
    db_uri = Config.SQLALCHEMY_DATABASE_URI
    if db_uri.startswith('sqlite:///'):
        return db_uri.replace('sqlite:///', '')
    return None


def migrate():
    """Add current_topic_thread_id column to agent_sessions table."""
    db_path = get_db_path()
    if not db_path:
        print("Error: Only SQLite migrations supported by this script")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(agent_sessions)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'current_topic_thread_id' in columns:
            print("Column current_topic_thread_id already exists. Skipping.")
            return True

        # Add the column
        cursor.execute("""
            ALTER TABLE agent_sessions
            ADD COLUMN current_topic_thread_id VARCHAR(100)
        """)

        conn.commit()
        print("✓ Added current_topic_thread_id column to agent_sessions table")
        return True

    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def rollback():
    """Remove current_topic_thread_id column (SQLite requires table recreation)."""
    print("Note: SQLite doesn't support DROP COLUMN directly.")
    print("To rollback, recreate the table without the column.")
    return False


if __name__ == '__main__':
    if '--rollback' in sys.argv:
        rollback()
    else:
        migrate()
```

---

## Step 2: Run Migration

```bash
cd /Users/nathansuberi/Documents/GitHub/code-dojo
python migrations/add_topic_thread_id.py
```

---

## Step 3: Run Integration Tests

The integration tests send traces to the `code-dojo-tests` LangSmith project.

```bash
cd /Users/nathansuberi/Documents/GitHub/code-dojo

# Run all articulation integration tests
pytest tests/test_articulation_traces.py -v -s -m integration

# Or run specific test classes:
pytest tests/test_articulation_traces.py::TestArticulationGemAcquisition -v -s -m integration
pytest tests/test_articulation_traces.py::TestFrustrationDetection -v -s -m integration
pytest tests/test_articulation_traces.py::TestArticulationGuidedMode -v -s -m integration
```

**Expected traces in `code-dojo-tests` project:**
- `articulation_topic_conversation` - NEW topic-level traces
- `articulation_message_process` - with `topic_thread_id` in metadata
- `articulation_harness_orchestration` - session-level trace

---

## Step 4: Verify AI Eval Viewer Configuration

The viewer `.env` is already configured for the test project:
```
VITE_LANGSMITH_PROJECT_ID=2e739374-d9e5-41e8-8c6c-eef06e0ff2ef  # code-dojo-tests
```

The `langsmith.ts` has been updated to look for `articulation_topic_conversation` traces.

---

## Step 5: Run Playwright Tests

```bash
cd /Users/nathansuberi/Documents/GitHub/code-dojo/ai-eval-viewer

# Install dependencies if needed
npm install

# Run all E2E tests
npm run test:e2e

# Or run with UI for debugging
npm run test:e2e:ui
```

**Test files:**
- `tests/navigation.spec.ts` - Tests dashboard, thread list, span tree navigation
- `tests/frustration-traces.spec.ts` - Tests frustration metadata visibility

---

## Step 6: Manual Verification in Viewer

1. Start the viewer:
   ```bash
   cd ai-eval-viewer && npm run dev
   ```

2. Open http://localhost:5173

3. Click "Digi-Trainer" feature card

4. Verify:
   - Thread list shows `articulation_topic_conversation` traces
   - Each thread shows `goal_title` in metadata
   - Clicking a thread shows nested message spans
   - Spans have `topic_thread_id` linking them to parent topic

---

## Files Modified (Implementation Complete)

| File | Status |
|------|--------|
| `services/articulation_harness.py` | ✅ Complete |
| `models/agent_session.py` | ✅ Complete |
| `routes/agent_harness.py` | ✅ Complete |
| `ai-eval-viewer/src/services/langsmith.ts` | ✅ Complete |

## Files to Create

| File | Status |
|------|--------|
| `migrations/add_topic_thread_id.py` | ⏳ Pending |

---

## Test Verification Checklist

- [ ] Migration runs without errors
- [ ] Integration tests pass and generate traces
- [ ] `articulation_topic_conversation` traces appear in LangSmith
- [ ] Message traces have `topic_thread_id` metadata
- [ ] Playwright tests pass
- [ ] Viewer shows topic threads in Digi-Trainer
- [ ] Clicking thread shows nested message spans
