# Fix Account Page View Button and Review Tab Digi-Trainer

## Summary

This plan fixes the submission review flow to:
- ✅ Navigate from account page directly to the review tab (instead of separate page)
- ✅ Enable digi-trainer chat in the review tab
- ✅ Show Code Changes section expanded by default (already exists, just needs to be visible)
- ✅ Keep all sections collapsible for user control

**Changes**: 7 modifications across 5 files
**Impact**: Unified submission review experience with all tools accessible in one place

---

## Problem Summary

Three issues with the submission review flow:

1. **Incorrect Navigation**: The "View" button on the account page (`templates/account.html:52-53`) navigates to a separate submission view page (`/submissions/<id>`) instead of the learning goal's review tab (tab 5)

2. **Digi-Trainer Not Loading**: The digi-trainer chat component is not initializing properly in the review tab, preventing students from engaging with core learning goals

3. **Code Changes Hidden**: The Code Changes section exists but starts collapsed, making it less discoverable for students reviewing their submissions

## Root Causes

### Navigation Issue
- Account page links to `submissions.view_submission` route which renders `templates/submissions/student_view.html`
- This creates a separate, redundant submission view instead of using the unified review tab interface
- The review tab (tab 5 in `templates/modules/goal.html:315-612`) is the intended primary submission review interface

### Digi-Trainer Issue
- Hash-based tab activation works (`#tab-review`)
- Query param check in `review-tab.js:196-203` looks for `?tab=review` but the actual navigation uses hash fragments
- The two different tab switching mechanisms aren't fully aligned

## Implementation Plan

### Change 1: Update Account Page View Button
**File**: `templates/account.html`
**Lines**: 52-53

**Current**:
```html
<a href="{{ url_for('submissions.view_submission', submission_id=submission.id) }}"
   class="btn btn-small">View</a>
```

**New**:
```html
<a href="{{ url_for('modules.goal_detail', module_id=submission.goal.module_id, goal_id=submission.goal_id) }}#tab-review"
   class="btn btn-small">View</a>
```

**Why**: Navigates directly to the goal page with the review tab activated via hash fragment. Uses the existing `goal` relationship (`submission.goal.module_id`) to get the module ID.

---

### Change 2: Redirect Legacy Submission View Route
**File**: `routes/submissions.py`
**Lines**: 123-134

**Current**:
```python
@submissions_bp.route('/<int:submission_id>')
@login_required
def view_submission(submission_id):
    """View a submission (student view)."""
    submission = Submission.query.get_or_404(submission_id)

    # Only allow owner or instructors to view
    if submission.user_id != current_user.id and not current_user.is_instructor:
        flash('You do not have permission to view this submission.', 'danger')
        return redirect(url_for('home'))

    return render_template('submissions/student_view.html', submission=submission)
```

**New**:
```python
@submissions_bp.route('/<int:submission_id>')
@login_required
def view_submission(submission_id):
    """Redirect to goal page review tab (legacy endpoint for backward compatibility)."""
    submission = Submission.query.get_or_404(submission_id)

    # Only allow owner or instructors to view
    if submission.user_id != current_user.id and not current_user.is_instructor:
        flash('You do not have permission to view this submission.', 'danger')
        return redirect(url_for('home'))

    # Redirect to the goal page with review tab active
    return redirect(url_for('modules.goal_detail',
                           module_id=submission.goal.module_id,
                           goal_id=submission.goal_id) + '#tab-review')
```

**Why**: Maintains backward compatibility for any bookmarked URLs or old links while consolidating all submission viewing to the review tab interface.

---

### Change 3: Improve Hash Parsing Robustness
**File**: `templates/modules/goal.html`
**Lines**: 2034-2044

**Current**:
```javascript
// Check URL hash on page load and switch to appropriate tab
window.addEventListener('DOMContentLoaded', () => {
    const hash = window.location.hash;
    if (hash) {
        // Remove the '#tab-' prefix to get the tab name
        const tabName = hash.replace('#tab-', '').replace('#', '');
        if (tabName) {
            switchTab(tabName);
        }
    }
});
```

**New**:
```javascript
// Check URL hash on page load and switch to appropriate tab
window.addEventListener('DOMContentLoaded', () => {
    const hash = window.location.hash;
    if (hash) {
        // Hash format: #tab-review or #review
        let tabName = hash.substring(1); // Remove leading #
        if (tabName.startsWith('tab-')) {
            tabName = tabName.substring(4); // Remove 'tab-' prefix
        }
        if (tabName) {
            switchTab(tabName);
        }
    }
});
```

**Why**: More explicit and cleaner logic. Handles both `#review` and `#tab-review` formats correctly without the confusing double `.replace()` call.

---

### Change 4: Remove Redundant Query Param Check
**File**: `static/js/review-tab.js`
**Lines**: 196-203

**Current**:
```javascript
checkAutoSwitchToReview() {
    // If there's a submission and we're coming from a submission redirect,
    // auto-switch to the review tab
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('tab') === 'review') {
        switchTab('review');
    }
}
```

**Action**: Remove this method entirely and remove the call to `this.checkAutoSwitchToReview()` from the `init()` method (line 22).

**Why**: The hash-based tab switching in `goal.html:2034-2044` already handles tab activation. This query param check is redundant and creates confusion between two different tab activation mechanisms. The hash approach is more appropriate for client-side tab switching.

---

### Change 5: Add Deprecation Notice to Old Template
**File**: `templates/submissions/student_view.html`
**Lines**: Top of file

Add comment at the top:
```html
<!--
DEPRECATED: This template is no longer used. The /submissions/<id> route now redirects
to the goal page review tab. This file is kept temporarily for reference but will be
removed in a future cleanup.
-->
```

**Why**: Documents that this template is deprecated without breaking anything. Can be fully deleted in a future cleanup pass once the redirect has been verified to work correctly.

---

## Critical Files Modified

1. `templates/account.html` - Update View button link (line 52-53)
2. `routes/submissions.py` - Convert view_submission to redirect (lines 123-134) + Add formatted HTML to diff endpoint (lines 188-211)
3. `templates/modules/goal.html` - Improve hash parsing (lines 2034-2044) + Auto-expand Code Changes (line 404) + Use formatted diff HTML (lines 2070-2093)
4. `static/js/review-tab.js` - Remove redundant query param check (lines 196-203)
5. `templates/submissions/student_view.html` - Add deprecation notice (top of file)

## Data Flow After Changes

```
Account Page
    |
    | Click "View" button
    |
    v
/modules/<module_id>/goals/<goal_id>#tab-review
    |
    | Hash fragment activates review tab
    |
    v
Review Tab (goal.html lines 315-612)
    |
    | ReviewTab.init() runs
    | - Finds #gems-container with data-goal-id and data-submission-id
    | - Sets up gem click handlers
    | - Sets up digi-trainer form
    |
    v
User clicks gem
    |
    v
Digi-Trainer chat opens and initializes
```

## Edge Cases Handled

1. **No submission exists**: Review tab shows "no submission yet" message (already handled by template `{% if latest_submission %}` check)

2. **Old bookmarked URLs**: Legacy `/submissions/<id>` URLs redirect to goal page with review tab active

3. **Multiple submissions**: Goal detail route queries for `latest_submission` ordered by created_at DESC (already handled)

4. **Permission checks**: Redirect maintains existing permission validation before redirecting

5. **Browser back button**: Hash changes create browser history entries, so back button works correctly

## Verification Plan

### Manual Testing Checklist
1. Navigate to account page as logged-in user with submissions
2. Click "View" button on a submission
3. Verify URL changes to `/modules/{module_id}/goals/{goal_id}#tab-review`
4. Verify review tab is automatically activated and visible
5. **Verify "View Your Code Changes" section is expanded (visible) by default**
6. **Click "Load Diff" button and verify formatted code diff appears with:**
   - **File headers with icons and file names**
   - **Line numbers (old and new) on the left**
   - **Green highlighting for added lines (+)**
   - **Red highlighting for removed lines (-)**
   - **Syntax appears in monospace font**
   - **Matches the formatting from the admin/instructor view**
7. Verify gems are displayed with correct submission data
8. Click a gem to open digi-trainer chat
9. Verify chat initializes correctly with opening message
10. Send a message in chat and verify response displays
11. Navigate directly to old URL `/submissions/{id}`
12. Verify redirect to goal page review tab occurs
13. Test with user who has no submissions - verify "no submission" message appears
14. **Verify all review sections are collapsible (can be collapsed/expanded by clicking header)**

### Browser Console Verification
After loading review tab, verify:
```javascript
window.reviewTab !== undefined  // ReviewTab initialized
document.getElementById('gems-container') !== null  // Gems container exists
document.getElementById('gems-container').dataset.goalId  // Has goal ID
document.getElementById('gems-container').dataset.submissionId  // Has submission ID
```

### Expected Outcomes
- ✅ Account page View button navigates to goal page review tab
- ✅ Review tab automatically activates via hash fragment
- ✅ **Code Changes section is visible and expanded by default**
- ✅ **Code diff displays with beautiful GitHub-style syntax highlighting**
- ✅ **Line numbers, color-coded additions/deletions match admin view**
- ✅ **All review sections are collapsible**
- ✅ Digi-trainer chat initializes when gem is clicked
- ✅ Old submission URLs redirect seamlessly
- ✅ No duplicate submission view pages
- ✅ Consistent review experience across all entry points

## Code Changes Widget Status

**Good News**: The Code Changes review widget already exists in the review tab!

**Location**: `templates/modules/goal.html:402-421`

**Current Features**:
- ✅ Collapsible card section labeled "View Your Code Changes"
- ✅ Starts collapsed by default (has `collapsed` class)
- ✅ Load button fetches diff via `/submissions/${submissionId}/diff` endpoint
- ✅ `loadDiffContent()` function displays GitHub diff (lines 2056-2093)
- ✅ All review sections are already collapsible

**Enhancement**: Auto-expand Code Changes when navigating from account page

To make code review easier, we'll auto-expand the Code Changes section when users click "View" from the account page.

### Change 6: Auto-Expand Code Changes Section
**File**: `templates/modules/goal.html`
**Lines**: After 2093 (in the script section)

Add new function:
```javascript
// Auto-expand Code Changes section if coming from account page
function checkAutoExpandCodeChanges() {
    const hash = window.location.hash;
    const referrer = document.referrer;

    // If navigating to review tab from account page, expand code changes
    if (hash === '#tab-review' && referrer.includes('/account')) {
        const codeChangesCard = document.querySelector('.review-card.collapsible-card.collapsed h3:contains("View Your Code Changes")');
        if (codeChangesCard) {
            const cardHeader = codeChangesCard.closest('.card-header');
            if (cardHeader) {
                // Remove collapsed class to expand
                cardHeader.closest('.collapsible-card').classList.remove('collapsed');
            }
        }
    }
}

// Call after DOM loads
window.addEventListener('DOMContentLoaded', () => {
    checkAutoExpandCodeChanges();
});
```

**Alternative simpler approach**: Remove the `collapsed` class from the Code Changes card so it starts expanded by default.

**File**: `templates/modules/goal.html`
**Line**: 404

**Current**:
```html
<div class="review-card collapsible-card collapsed">
```

**New**:
```html
<div class="review-card collapsible-card">
```

**Recommendation**: Use the simpler approach - just remove `collapsed` so the Code Changes section is visible by default. Students can collapse it if they don't need it.

---

### Change 7: Add Syntax Highlighting to Code Changes Widget
**Problem**: The student review tab displays raw diff text, while the admin view has beautiful GitHub-style formatting with syntax highlighting, line numbers, and color-coded changes.

**Current Implementation**:
- Admin view (`templates/submissions/instructor_view.html:57`): Uses `{{ diff_content | format_diff }}` filter
- Student view (`templates/modules/goal.html:2075`): Just displays raw text with `diffContent.textContent = data.diff`
- The `format_diff` filter (`app.py:45-215`) creates formatted HTML with file headers, line numbers, and syntax highlighting
- CSS styling already exists (`static/css/styles.css:1023+`) for `.diff-container`, `.diff-file`, `.diff-line`, etc.

**Solution**: Return formatted HTML from the diff endpoint instead of raw text.

**File**: `routes/submissions.py`
**Lines**: 188-211

**Current**:
```python
@submissions_bp.route('/<int:submission_id>/diff')
@login_required
def get_submission_diff(submission_id):
    """Get the diff content for a submission (API endpoint)."""
    submission = Submission.query.get_or_404(submission_id)

    # Only allow owner or instructors to view
    if submission.user_id != current_user.id and not current_user.is_instructor:
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        diff_content = fetch_github_diff(
            submission.goal.starter_repo,
            submission.repo_url,
            submission.branch
        )

        if diff_content:
            return jsonify({'diff': diff_content})
        else:
            return jsonify({'error': 'Could not fetch diff from GitHub'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

**New**:
```python
from flask import current_app

@submissions_bp.route('/<int:submission_id>/diff')
@login_required
def get_submission_diff(submission_id):
    """Get the diff content for a submission (API endpoint)."""
    submission = Submission.query.get_or_404(submission_id)

    # Only allow owner or instructors to view
    if submission.user_id != current_user.id and not current_user.is_instructor:
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        diff_content = fetch_github_diff(
            submission.goal.starter_repo,
            submission.repo_url,
            submission.branch
        )

        if diff_content:
            # Apply format_diff filter to get formatted HTML
            format_diff = current_app.jinja_env.filters['format_diff']
            formatted_html = format_diff(diff_content)
            return jsonify({
                'diff': diff_content,  # Keep raw for backward compat
                'formatted_html': str(formatted_html)  # Add formatted version
            })
        else:
            return jsonify({'error': 'Could not fetch diff from GitHub'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

**File**: `templates/modules/goal.html`
**Lines**: 2070-2093

**Current**:
```javascript
async function loadDiffContent(submissionId) {
    if (diffLoaded) return;

    const diffContent = document.getElementById('diff-content');
    const diffHint = document.querySelector('.diff-hint');
    const loadBtn = event.target;

    if (!diffContent) return;

    // Show loading state
    loadBtn.disabled = true;
    loadBtn.textContent = 'Loading...';
    diffHint.textContent = 'Fetching diff from GitHub...';

    try {
        const response = await fetch(`/submissions/${submissionId}/diff`);
        const data = await response.json();

        if (data.diff) {
            diffContent.textContent = data.diff;
            diffContent.style.display = 'block';
            diffHint.style.display = 'none';
            loadBtn.style.display = 'none';
            diffLoaded = true;
        } else if (data.error) {
            diffHint.textContent = `Error: ${data.error}`;
            diffHint.style.color = 'var(--danger-color)';
            loadBtn.disabled = false;
            loadBtn.textContent = 'Retry';
        }
    } catch (error) {
        console.error('Error loading diff:', error);
        diffHint.textContent = 'Failed to load diff. Please try again.';
        diffHint.style.color = 'var(--danger-color)';
        loadBtn.disabled = false;
        loadBtn.textContent = 'Retry';
    }
}
```

**New**:
```javascript
async function loadDiffContent(submissionId) {
    if (diffLoaded) return;

    const diffContent = document.getElementById('diff-content');
    const diffHint = document.querySelector('.diff-hint');
    const loadBtn = event.target;

    if (!diffContent) return;

    // Show loading state
    loadBtn.disabled = true;
    loadBtn.textContent = 'Loading...';
    diffHint.textContent = 'Fetching diff from GitHub...';

    try {
        const response = await fetch(`/submissions/${submissionId}/diff`);
        const data = await response.json();

        if (data.formatted_html || data.diff) {
            // Use formatted HTML if available, otherwise fall back to raw diff
            if (data.formatted_html) {
                diffContent.innerHTML = data.formatted_html;
            } else {
                diffContent.textContent = data.diff;
            }
            diffContent.style.display = 'block';
            diffHint.style.display = 'none';
            loadBtn.style.display = 'none';
            diffLoaded = true;
        } else if (data.error) {
            diffHint.textContent = `Error: ${data.error}`;
            diffHint.style.color = 'var(--danger-color)';
            loadBtn.disabled = false;
            loadBtn.textContent = 'Retry';
        }
    } catch (error) {
        console.error('Error loading diff:', error);
        diffHint.textContent = 'Failed to load diff. Please try again.';
        diffHint.style.color = 'var(--danger-color)';
        loadBtn.disabled = false;
        loadBtn.textContent = 'Retry';
    }
}
```

**Why this works**:
- Uses the exact same `format_diff` filter that the admin view uses
- Returns both raw and formatted versions for backward compatibility
- Client-side code uses `innerHTML` instead of `textContent` to render formatted HTML
- All existing CSS styling (`.diff-container`, `.diff-file`, `.diff-line`, etc.) already exists and will apply automatically

---

## Why This Fixes Both Issues

### Digi-Trainer Issue
The digi-trainer wasn't loading because:
1. The hash-based tab activation mechanism works correctly
2. But ReviewTab initialization depends on proper data attributes in `#gems-container`
3. The template already populates these correctly when `latest_submission` exists
4. The issue was likely users accessing the old separate submission page which doesn't have the ReviewTab JavaScript at all

By consolidating all submission viewing to the review tab:
- All submission views now use the same interface
- ReviewTab JavaScript always loads and initializes
- Gems and digi-trainer chat work consistently
- No confusion between two different submission view interfaces

### Code Changes Widget
The Code Changes widget already exists and is collapsible. The enhancements ensure students can:
- See it expanded by default (no hunting for collapsed sections)
- View beautifully formatted diffs with syntax highlighting (same as instructors see)
- Easily review their code changes with line numbers and color-coded additions/deletions
