# Plan: Verify AI Eval Viewer Integration & Harness Behavior

## Overview

Following the main plan in `project_scoping/incremental-plans/ai-eval-viewer/adding-integration-tests-and-configuring-improvement-loop-plan.md` to verify:
1. AI Eval Viewer correctly displays traces
2. LangSmith threads are properly configured
3. Harness correctly detects good conversations → awards gems
4. Harness correctly detects bad conversations → marks as needs work
5. Frustration detection → ends topic immediately, marks engaged

---

## Current Status

### Integration Tests: ✅ ALL PASSING (10/10)

```
pytest tests/test_articulation_traces.py -v -s -m integration
============ 10 passed, 1 skipped in 90.15s =============

✅ TestArticulationGemAcquisition::test_successful_articulation_session
   - Good explanation → 💎 Mastery demonstrated! (Passed: 1)

✅ TestArticulationFailedUnderstanding::test_failed_articulation_session
   - Vague responses → Progressive hints → 🔵 Good engagement! (Engaged: 1)

✅ TestArticulationMixedProgress::test_partial_understanding

✅ TestArticulationGuidedMode::test_guided_mode_progression

✅ TestInstructorUnlockThreshold::test_instructor_unlock_after_threshold
   - After 2 topics engaged → can_request_instructor: True

✅ TestArticulationTraceGrouping::test_traces_grouped_as_thread
   - langsmith_run_id populated in AgentSession

✅ TestArticulationTraceGrouping::test_trace_context_closes_on_exception

✅ TestFrustrationDetection::test_frustration_ends_topic_and_marks_needs_work
   - "I give up" → frustration_detected: True, topic_ended: True

✅ TestFrustrationDetection::test_frustration_resets_goal_state
   - current_goal_index: None after frustration

✅ TestFrustrationDetection::test_frustration_logged_in_trace_metadata
```

### Files Modified

| File | Status | Changes |
|------|--------|---------|
| `services/socratic_harness_base.py` | ✅ | Expanded frustration signals (17 patterns) |
| `services/articulation_harness.py` | ✅ | Added `_handle_frustration_and_end_topic()`, frustration detection in `process_message()`, trace metadata |
| `tests/test_articulation_traces.py` | ✅ | Added `TestFrustrationDetection` class (3 tests) |
| `ai-eval-viewer/tests/frustration-traces.spec.ts` | ✅ | NEW - Playwright tests for trace display |

---

## Remaining Verification Steps

### Step 1: Verify AI Eval Viewer Shows Traces

**Issue:** LangSmith queries in tests return 0 traces. Need to verify:
1. Traces are being sent to correct project (`code-dojo-tests`)
2. `session_id` metadata is present for thread grouping
3. AI Eval Viewer can display the traces

**Action:**
```bash
cd ai-eval-viewer && npm run dev
# Open http://localhost:5173
# Navigate to Digi-Trainer feature
# Check for threads with traces
```

### Step 2: Run Playwright Tests for AI Eval Viewer

```bash
cd ai-eval-viewer && npm run test:e2e -- tests/frustration-traces.spec.ts
```

### Step 3: Manual Verification in AI Eval Viewer

- [ ] Dashboard shows Digi-Trainer with trace count > 0
- [ ] Thread list shows articulation sessions
- [ ] Clicking thread shows span tree
- [ ] Span metadata shows `frustration_detected` flag
- [ ] Empathetic responses visible in frustrated traces
- [ ] Annotation panel opens (press 'a')
- [ ] Notes can be added to spans

---

## Harness Behavior Summary

| Scenario | Input | Expected Behavior | Status |
|----------|-------|-------------------|--------|
| Good explanation | Clear, detailed response | 💎 Passed - gem awarded | ✅ |
| Vague explanation | Generic, unclear response | Progressive hints → 🔵 Engaged after 3 attempts | ✅ |
| Frustration signal | "I give up", "skip this", etc. | Immediate end, 🔵 Engaged, empathetic response | ✅ |
| Topic selection | "1" or topic name | Focus on selected topic | ✅ |
| Guided mode | "Guide me through all" | Auto-advance through topics | ✅ |
| Instructor unlock | 50% topics engaged | `can_request_instructor: True` | ✅ |

---

## Verification Checklist

**Integration Tests:**
- [x] Good conversations award gems (passed status)
- [x] Bad conversations mark as needs work (engaged status)
- [x] Frustration detection ends topic immediately
- [x] Frustration marks topic as engaged (not passed)
- [x] State resets after frustration
- [x] Trace metadata includes frustration_detected

**AI Eval Viewer:**
- [ ] Traces visible in Digi-Trainer feature
- [ ] Thread grouping works (traces grouped by session_id)
- [ ] Span tree displays correctly
- [ ] Metadata visible in span details
- [ ] Playwright tests pass

---

## Next Steps

1. Start AI Eval Viewer and verify traces are visible
2. Run Playwright tests against live viewer
3. Document any issues found in trace display
4. Update main plan file with results
