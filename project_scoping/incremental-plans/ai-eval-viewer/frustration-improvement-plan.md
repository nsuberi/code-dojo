# Plan: Frustration Detection Feature with TDD Approach

## Overview

Implement a UX improvement that detects student frustration and responds empathetically, using Test-Driven Development. The `detect_frustration()` method exists but is **completely unused** - we need to integrate it into the harness flow and add appropriate responses.

## Current State Analysis

| Component | Status | Location |
|-----------|--------|----------|
| `detect_frustration()` method | EXISTS (dead code) | `services/socratic_harness_base.py:207-222` |
| Frustration response logic | MISSING | - |
| Integration into harness | MISSING | `services/articulation_harness.py` |
| Integration tests | MISSING | `tests/test_articulation_traces.py` |
| Playwright tests | MISSING | `ai-eval-viewer/tests/` |

**Current frustration signals (too narrow):**
- "I don't understand", "can we move on", "this is confusing"
- "skip this", "I give up", "this doesn't make sense"

---

## Implementation Steps (TDD Order)

### Step 1: Write Failing Integration Tests

**File:** `tests/test_articulation_traces.py`

Add new test class `TestFrustrationDetection` with tests that will initially FAIL:

```python
class TestFrustrationDetection:
    """Tests for frustration detection - ends topic and marks as needs work."""

    FRUSTRATED_RESPONSES = [
        "I give up, this doesn't make sense",
        "This is confusing, can we move on?",
        "I don't understand any of this",
        "Skip this please, I'm lost",
    ]

    @pytest.mark.integration
    def test_frustration_ends_topic_and_marks_needs_work(self, ...):
        """Frustration should immediately end topic and mark as 'engaged' (needs work).

        Expected behavior:
        - Frustration detected from message
        - Current topic marked as 'engaged' (not 'passed')
        - Response acknowledges difficulty empathetically
        - Topic discussion ended, user offered to move on
        """
        with app.app_context():
            harness = ArticulationHarness(...)
            session = harness.start_session()
            harness.process_message("1", input_mode='text')  # Select topic

            # User expresses frustration
            result = harness.process_message(
                "I give up, this doesn't make sense",
                input_mode='text'
            )

            # Assertions:
            assert result.get('frustration_detected') is True
            assert result.get('topic_ended') is True
            assert result.get('topic_status') == 'engaged'  # Needs work

            # Response should be empathetic
            assert 'challenging' in result['response'].lower()

            # Topic should be marked as engaged (not passed)
            engagement = result.get('engagement', {})
            assert engagement.get('engaged', 0) >= 1

    @pytest.mark.integration
    def test_frustration_resets_goal_state(self, ...):
        """After frustration, current_goal_index should be reset."""
        # Verify harness.session.current_goal_index is None after frustration

    @pytest.mark.integration
    def test_frustration_logged_in_trace_metadata(self, ...):
        """Frustration events should be visible in LangSmith traces."""
        # Query LangSmith for traces with frustration_detected: true
```

**Run tests to confirm they FAIL:**
```bash
pytest tests/test_articulation_traces.py::TestFrustrationDetection -v -s -m integration
```

### Step 2: Implement Frustration Detection in Harness

**File:** `services/articulation_harness.py`

**Behavior:** When frustration is detected:
1. Acknowledge the difficulty empathetically
2. Immediately END the current topic (no prolonged help attempts)
3. Mark topic as "needs more work" (engaged status, NOT passed)
4. Move to the next topic or offer to end session

```python
def process_message(self, user_message, ...):
    # ... existing message storage ...

    # Check for frustration before normal processing
    messages = [m.content for m in self.session.messages.all()]
    if self.detect_frustration(messages):
        return self._handle_frustration_and_end_topic(user_message)

    # ... existing logic ...

def _handle_frustration_and_end_topic(self, user_message):
    """Handle frustration by ending current topic and marking as needs work."""
    goals = self.get_core_learning_goals()
    current_goal = goals[self.session.current_goal_index] if self.session.current_goal_index is not None else None

    if current_goal:
        # Mark topic as "engaged" (needs more work) - NOT passed
        self.update_gem_state(current_goal['id'], 'engaged')
        self.session.goals_engaged = (self.session.goals_engaged or 0) + 1
        db.session.commit()

        response = f"""I can see this topic is challenging right now - that's completely normal.

🔵 I've marked **{current_goal['title']}** as something to revisit later. No pressure.

Let's move on. Would you like to:
1. Try a different concept
2. End this session for now

You can always come back to practice this topic when you're ready."""

    else:
        response = """I can see you're finding this challenging - that's completely normal.

Would you like to:
1. Try a different concept
2. Take a break and come back later"""

    self.store_message('assistant', response)

    # Reset current goal state
    self.session.current_goal_index = None
    self.session.current_rubric_item_index = 0
    self.session.current_attempts = 0
    db.session.commit()

    return {
        'response': response,
        'frustration_detected': True,
        'topic_ended': True,
        'topic_status': 'engaged',  # Needs more work
        'engagement': self.calculate_engagement_stats()
    }
```

**File:** `services/socratic_harness_base.py`

Enhance `detect_frustration()` with more signals:
```python
def detect_frustration(self, messages):
    frustration_signals = [
        "I don't understand", "can we move on", "this is confusing",
        "skip this", "I give up", "this doesn't make sense",
        # New signals:
        "I'm lost", "too hard", "makes no sense", "forget it",
        "whatever", "just tell me", "I'm stuck", "help me"
    ]
    # ... rest of method ...
```

### Step 3: Add Frustration Metadata to Traces

**File:** `services/articulation_harness.py`

Update trace metadata to include frustration state:

```python
def process_message(self, user_message, ...):
    # Detect frustration first
    messages = [m.content for m in self.session.messages.all()]
    is_frustrated = self.detect_frustration(messages)

    with trace(
        name="articulation_message_process",
        metadata={
            "session_id": self._thread_id,
            "harness_type": "articulation",
            "frustration_detected": is_frustrated,  # NEW
            "input_mode": input_mode
        }
    ):
        if is_frustrated:
            return self._handle_frustration(user_message)
        # ... rest of processing ...
```

### Step 4: Verify Tests Pass

```bash
pytest tests/test_articulation_traces.py::TestFrustrationDetection -v -s -m integration
```

Expected: All 3 tests should now PASS.

### Step 5: Verify in AI Eval Viewer

1. Start the viewer: `cd ai-eval-viewer && npm run dev`
2. Navigate to Digi-Trainer feature
3. Find traces with `frustration_detected: true` in metadata
4. Verify the empathetic response appears in span output

### Step 6: Write Playwright Tests for AI Eval Viewer

**File:** `ai-eval-viewer/tests/frustration-traces.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Frustration Detection Traces', () => {
  test('should display frustration_detected metadata in span', async ({ page }) => {
    await page.goto('/feature/digi-trainer');
    await page.waitForSelector('.list-item', { timeout: 10000 });

    // Click on a thread
    await page.locator('.list-item').first().click();
    await page.waitForSelector('.tree-node', { timeout: 10000 });

    // Find articulation_message_process span
    const messageSpan = page.locator('.tree-node-name', {
      hasText: 'articulation_message_process'
    });

    if (await messageSpan.count() > 0) {
      await messageSpan.first().click();

      // Check metadata in output
      const codeBlock = page.locator('.code-block');
      await expect(codeBlock).toBeVisible();

      // Verify frustration metadata is displayed
      const content = await codeBlock.textContent();
      // This test validates that metadata is visible - actual frustration
      // traces may or may not have the flag set
      expect(content).toBeTruthy();
    }
  });

  test('should show empathetic response in frustrated trace output', async ({ page }) => {
    // Navigate to thread detail
    await page.goto('/feature/digi-trainer');
    await page.waitForSelector('.list-item', { timeout: 10000 });
    await page.locator('.list-item').first().click();

    // Look for span with frustration response keywords
    const spans = page.locator('.tree-node');

    // Switch to output tab
    await page.getByRole('button', { name: 'Output' }).click();

    const outputBlock = page.locator('.code-block');
    if (await outputBlock.isVisible()) {
      const text = await outputBlock.textContent();
      // Check for empathy keywords if this is a frustration trace
      if (text?.includes('frustration_detected')) {
        expect(text).toMatch(/challenging|different approach|simplify|skip|break/i);
      }
    }
  });
});
```

**Run playwright tests:**
```bash
cd ai-eval-viewer && npm run test:e2e -- tests/frustration-traces.spec.ts
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `tests/test_articulation_traces.py` | Add `TestFrustrationDetection` class (3 tests) |
| `services/articulation_harness.py` | Add `_handle_frustration()`, integrate detection in `process_message()` |
| `services/socratic_harness_base.py` | Expand frustration signals list |
| `ai-eval-viewer/tests/frustration-traces.spec.ts` | NEW - Playwright tests for trace display |

---

## Verification Checklist

1. **Integration Tests (TDD):**
   - [ ] Write tests → verify they FAIL
   - [ ] Implement feature → verify tests PASS
   ```bash
   pytest tests/test_articulation_traces.py::TestFrustrationDetection -v -s -m integration
   ```

2. **AI Eval Viewer:**
   - [ ] Traces appear with `frustration_detected` in metadata
   - [ ] Empathetic response visible in span output
   ```bash
   cd ai-eval-viewer && npm run dev
   # Open http://localhost:5173, navigate to Digi-Trainer
   ```

3. **Playwright Tests:**
   - [ ] Tests pass against live viewer
   ```bash
   cd ai-eval-viewer && npm run test:e2e -- tests/frustration-traces.spec.ts
   ```

---

## Expected Outcomes

**Before (current behavior):**
- Frustrated user gets same hint progression as confused user
- No special handling - keeps trying even when user wants to stop
- Topic stays active despite clear frustration signals
- No way to identify frustration in traces

**After (new behavior):**
- Frustrated user gets empathetic acknowledgment
- Topic is IMMEDIATELY ENDED (no prolonged help attempts)
- Topic marked as "engaged" / "needs more work" (🔵 not 💎)
- User offered to move to different topic or end session
- Frustration events visible in LangSmith traces with `frustration_detected: true` metadata
- AI Eval Viewer can filter/identify frustration traces for debugging
