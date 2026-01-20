# GitHub-Style Diff Viewer Implementation Plan

## 📋 Problem Statement

The Code Changes block currently shows full file content rather than actual diffs. The `fetch_github_diff()` function returns complete files with `=== filename ===` headers, but no `+/-` line markers. The frontend `format_diff` filter is designed to handle unified diff format, but receives full file content instead, causing everything to render as gray "context lines" without highlighting what was actually added or removed.

**Goal:** Create a beautiful, polished, GitHub PR-style diff viewer that makes it immediately obvious what code students added (green) and removed (red), with professional visual presentation including line numbers, file stats, and intuitive UX.

---

## Current Architecture Overview

**Backend Flow:**
1. `services/github.py::fetch_github_diff()` - Fetches file trees from starter and student repos, returns full content of changed files
2. `routes/admin.py` - Calls `fetch_github_diff()` and passes result to template
3. Template filter `app.py::format_diff_filter()` - Expects unified diff format with `+/-` markers
4. `static/css/styles.css` - Has basic GitHub-style styling (lines 958-1122)

**Current Limitations:**
- Only shows full file content, not line-by-line diffs
- No indication of what lines were added/removed
- Cannot see what changed from the starter repo
- No line numbers
- No file statistics
- Uses GitHub API file tree comparison (SHA-based)

---

## Implementation Plan - Complete Polished Experience

### **Phase 1: Backend - Generate Unified Diff Format**

**Objective:** Modify `services/github.py::fetch_github_diff()` to generate proper unified diff format with comprehensive metadata.

**Implementation Approach: Use Python's `difflib`**

**Why difflib over GitHub Compare API:**
- No external dependencies (standard library)
- Full control over diff format and context
- Works across different repo forks without complex GitHub API calls
- More reliable, no cross-fork comparison issues
- Better error handling

**Detailed Implementation:**

1. **Modify `fetch_github_diff()` in `services/github.py` (lines 26-96):**
   - Fetch file content from BOTH starter and student repos
   - Handle files that exist only in student repo (new files - all lines are additions)
   - Handle files that exist only in starter repo (deleted files - all lines are deletions)
   - Generate unified diff using `difflib.unified_diff()` with 3 lines of context
   - Include comprehensive metadata for each file:
     - File path
     - Lines added count
     - Lines removed count
     - Whether file is new/deleted/modified

2. **Unified Diff Format Structure:**
   ```diff
   diff --git a/app.py b/app.py
   index abc123..def456 100644
   --- a/app.py
   +++ b/app.py
   @@ -10,7 +10,8 @@ def hello():
    context line
    context line
   -removed line
   +added line
    context line
   ```

3. **File Statistics Collection:**
   - Track additions/deletions per file
   - Format as metadata before diff content
   - Example: `FILE_STATS: app.py +15 -3`

4. **Error Handling:**
   - Handle GitHub API rate limiting gracefully (show error message)
   - Handle missing files/repos
   - Handle binary files (skip with message "Binary file changed")
   - Handle large files (files > 1000 lines, show truncation message)
   - Return meaningful error messages that help debugging

**Files to Modify:**
- `/Users/nathansuberi/Documents/GitHub/code-dojo/services/github.py` (lines 26-96)

**Key Code Changes:**
```python
import difflib
from typing import Dict, List, Tuple

def fetch_github_diff(starter_repo_url, student_repo_url, branch='main'):
    """
    Generate unified diff between starter and student repos.
    Returns formatted diff with file stats and proper +/- markers.
    """
    # 1. Fetch file trees from both repos
    # 2. Identify changed/new/deleted files
    # 3. For each changed file:
    #    a. Fetch content from both repos
    #    b. Generate unified diff using difflib.unified_diff()
    #    c. Calculate stats (lines added/removed)
    # 4. Format output with file headers and stats
    # 5. Return complete diff string
```

---

### **Phase 2: Frontend - Enhanced Diff Rendering with Line Numbers & Stats**

**Objective:** Create a beautiful, GitHub-style diff viewer with line numbers, file statistics, and professional visual presentation.

#### **2.1: Update `format_diff` Filter**

**Modify `app.py::format_diff_filter()` (lines 45-82):**

**New Features to Add:**
1. **Line Numbers:**
   - Parse `@@ -old_start,old_count +new_start,new_count @@` hunk headers
   - Track old (left) and new (right) line numbers
   - Display both line numbers for each line
   - Format: `<span class="line-num old">123</span><span class="line-num new">125</span>`

2. **File Statistics Header:**
   - Parse `FILE_STATS:` metadata from diff
   - Display prominently above each file
   - Format: `<div class="file-stats">app.py <span class="additions">+15</span> <span class="deletions">-3</span></div>`

3. **File Type Indicators:**
   - Show icons based on file type (.py, .js, .html, etc.)
   - Use color coding for file names

4. **Enhanced Structure:**
   ```html
   <div class="diff-file">
     <div class="diff-file-header">
       <span class="file-icon">📄</span>
       <span class="file-name">app.py</span>
       <span class="file-stats">
         <span class="additions">+15</span>
         <span class="deletions">-3</span>
       </span>
     </div>
     <div class="diff-content">
       <div class="diff-line diff-added">
         <span class="line-num old"></span>
         <span class="line-num new">45</span>
         <span class="diff-marker">+</span>
         <span class="diff-text">    new_code_here()</span>
       </div>
       <!-- more lines -->
     </div>
   </div>
   ```

5. **Handle Edge Cases:**
   - Empty lines (preserve formatting)
   - Very long lines (add horizontal scroll)
   - Binary files (show message, no content)
   - New files (all lines green, no old line numbers)
   - Deleted files (all lines red, no new line numbers)

**Files to Modify:**
- `/Users/nathansuberi/Documents/GitHub/code-dojo/app.py` (lines 45-82)

#### **2.2: Update Template Structure**

**Modify `templates/submissions/instructor_view.html` (lines 33-43):**

**Enhancements:**
1. Add summary stats at top (total files changed, lines added/removed)
2. Add "View on GitHub" link to student repo
3. Better empty state with helpful messaging
4. Add loading indicator support (for future async loading)

**New Structure:**
```html
<!-- Code Diff Section -->
<section class="diff-section">
    <h2>Code Changes</h2>

    {% if diff_content %}
        <!-- Summary Stats -->
        <div class="diff-summary">
            <span class="stat">📊 <strong>{{ file_count }}</strong> files changed</span>
            <span class="stat additions">+{{ total_additions }} additions</span>
            <span class="stat deletions">-{{ total_deletions }} deletions</span>
            <a href="{{ submission.repo_url }}" target="_blank" class="view-on-github">
                View on GitHub →
            </a>
        </div>

        <!-- Diff Container -->
        <div class="diff-container">
            {{ diff_content | format_diff }}
        </div>
    {% else %}
        <div class="empty-state">
            <p>Could not load code diff.</p>
            <p class="help-text">This could be due to API rate limits or repository access issues.</p>
            <a href="{{ submission.repo_url }}" target="_blank" class="btn-secondary">
                View repository directly on GitHub
            </a>
        </div>
    {% endif %}
</section>
```

**Files to Modify:**
- `/Users/nathansuberi/Documents/GitHub/code-dojo/templates/submissions/instructor_view.html` (lines 33-43)

---

### **Phase 3: Visual Polish - Professional GitHub-Style Styling**

**Objective:** Make the diff viewer visually stunning and match GitHub's professional PR aesthetic.

#### **3.1: Enhanced CSS Styling**

**Modify `static/css/styles.css` (enhance existing styles at lines 958-1122):**

**New Styles to Add:**

1. **Summary Stats Bar:**
   ```css
   .diff-summary {
       background: #161b22;
       border: 1px solid #30363d;
       border-radius: 6px;
       padding: 16px;
       margin-bottom: 16px;
       display: flex;
       align-items: center;
       gap: 24px;
       font-size: 14px;
   }

   .diff-summary .stat {
       display: flex;
       align-items: center;
       gap: 6px;
       color: #8b949e;
   }

   .diff-summary .stat strong {
       color: #c9d1d9;
   }

   .diff-summary .additions {
       color: #3fb950;
       font-weight: 600;
   }

   .diff-summary .deletions {
       color: #f85149;
       font-weight: 600;
   }
   ```

2. **Line Numbers:**
   ```css
   .line-num {
       display: inline-block;
       width: 50px;
       padding-right: 10px;
       text-align: right;
       color: #6e7681;
       user-select: none;
       font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace;
       font-size: 12px;
   }

   .line-num.old {
       border-right: 1px solid #30363d;
   }

   .line-num.new {
       border-right: 1px solid #30363d;
       margin-right: 10px;
   }

   /* Empty line numbers for added lines (no old line num) */
   .diff-added .line-num.old::after {
       content: ' ';
   }

   /* Empty line numbers for removed lines (no new line num) */
   .diff-removed .line-num.new::after {
       content: ' ';
   }
   ```

3. **File Headers with Stats:**
   ```css
   .diff-file {
       margin-bottom: 24px;
       border: 1px solid #30363d;
       border-radius: 6px;
       overflow: hidden;
       background: #0d1117;
   }

   .diff-file-header {
       background: #161b22;
       padding: 12px 16px;
       display: flex;
       align-items: center;
       gap: 8px;
       border-bottom: 1px solid #30363d;
       font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace;
       font-size: 14px;
       font-weight: 600;
       color: #c9d1d9;
   }

   .file-icon {
       font-size: 16px;
   }

   .file-name {
       flex: 1;
       color: #58a6ff;
   }

   .file-stats {
       display: flex;
       gap: 12px;
       font-size: 12px;
       font-weight: 600;
   }

   .file-stats .additions {
       color: #3fb950;
   }

   .file-stats .deletions {
       color: #f85149;
   }
   ```

4. **Enhanced Diff Lines:**
   ```css
   .diff-line {
       display: flex;
       align-items: stretch;
       font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace;
       font-size: 12px;
       line-height: 20px;
       background: #0d1117;
   }

   .diff-line:hover {
       background: #161b22;
   }

   .diff-added {
       background-color: #0d3818;
   }

   .diff-added:hover {
       background-color: #04260f;
   }

   .diff-added .diff-marker {
       background-color: #0d3818;
       color: #3fb950;
   }

   .diff-added .diff-text {
       background-color: #0d3818;
   }

   .diff-removed {
       background-color: #3d1319;
   }

   .diff-removed:hover {
       background-color: #4b1e26;
   }

   .diff-removed .diff-marker {
       background-color: #3d1319;
       color: #f85149;
   }

   .diff-removed .diff-text {
       background-color: #3d1319;
   }

   .diff-context {
       color: #c9d1d9;
   }

   .diff-marker {
       display: inline-block;
       width: 20px;
       text-align: center;
       user-select: none;
       padding: 0 8px;
       color: #6e7681;
   }

   .diff-text {
       flex: 1;
       padding-right: 16px;
       white-space: pre-wrap;
       word-break: break-all;
   }
   ```

5. **Empty State Improvements:**
   ```css
   .empty-state {
       text-align: center;
       padding: 48px 24px;
       background: #0d1117;
       border: 1px solid #30363d;
       border-radius: 6px;
       color: #8b949e;
   }

   .empty-state p {
       margin-bottom: 12px;
       font-size: 16px;
   }

   .empty-state .help-text {
       font-size: 14px;
       color: #6e7681;
   }

   .empty-state .btn-secondary {
       display: inline-block;
       margin-top: 16px;
       padding: 8px 16px;
       background: #21262d;
       color: #c9d1d9;
       border: 1px solid #30363d;
       border-radius: 6px;
       text-decoration: none;
       font-size: 14px;
       transition: all 0.2s;
   }

   .empty-state .btn-secondary:hover {
       background: #30363d;
       border-color: #8b949e;
   }
   ```

6. **View on GitHub Link:**
   ```css
   .view-on-github {
       color: #58a6ff;
       text-decoration: none;
       font-size: 14px;
       font-weight: 500;
       margin-left: auto;
       transition: color 0.2s;
   }

   .view-on-github:hover {
       color: #79c0ff;
       text-decoration: underline;
   }
   ```

7. **Hunk Headers:**
   ```css
   .diff-hunk {
       background: #1c2633;
       color: #8b949e;
       padding: 6px 16px;
       font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace;
       font-size: 12px;
       border-top: 1px solid #30363d;
       border-bottom: 1px solid #30363d;
       margin: 8px 0;
   }
   ```

8. **Responsive Design:**
   ```css
   @media (max-width: 768px) {
       .diff-summary {
           flex-direction: column;
           align-items: flex-start;
           gap: 12px;
       }

       .line-num {
           width: 40px;
           font-size: 11px;
       }

       .diff-text {
           font-size: 11px;
       }
   }
   ```

**Files to Modify:**
- `/Users/nathansuberi/Documents/GitHub/code-dojo/static/css/styles.css` (lines 958-1122 and additions)

---

### **Phase 4: Backend Summary Statistics**

**Objective:** Calculate and pass summary statistics to the template.

**Modify `routes/admin.py` (lines 29-71):**

**Add Statistics Calculation:**
```python
@admin_bp.route('/submissions/<int:submission_id>/review', methods=['GET', 'POST'])
def review_submission(submission_id):
    # ... existing code ...

    # Fetch diff
    diff_content = fetch_github_diff(goal.starter_repo, submission.repo_url, submission.branch)

    # Calculate summary stats from diff_content
    diff_stats = calculate_diff_stats(diff_content)  # New helper function

    return render_template(
        'submissions/instructor_view.html',
        submission=submission,
        form=form,
        diff_content=diff_content,
        file_count=diff_stats['file_count'],
        total_additions=diff_stats['total_additions'],
        total_deletions=diff_stats['total_deletions']
    )
```

**Add Helper Function in `services/github.py`:**
```python
def calculate_diff_stats(diff_content):
    """
    Calculate summary statistics from diff content.
    Returns dict with file_count, total_additions, total_deletions.
    """
    if not diff_content:
        return {'file_count': 0, 'total_additions': 0, 'total_deletions': 0}

    file_count = diff_content.count('diff --git')
    total_additions = diff_content.count('\n+') - diff_content.count('\n+++')
    total_deletions = diff_content.count('\n-') - diff_content.count('\n---')

    return {
        'file_count': file_count,
        'total_additions': total_additions,
        'total_deletions': total_deletions
    }
```

**Files to Modify:**
- `/Users/nathansuberi/Documents/GitHub/code-dojo/routes/admin.py` (lines 29-71)
- `/Users/nathansuberi/Documents/GitHub/code-dojo/services/github.py` (add new function)

---

### **Phase 5: Testing & Validation**

**Comprehensive Test Cases:**

#### **5.1: Functional Tests**

1. **Basic Diff Scenarios:**
   - Student adds new lines to starter code → All additions show green with "+" markers
   - Student removes lines from starter code → All removals show red with "-" markers
   - Student modifies existing lines → Old line red, new line green
   - Student adds AND removes lines → Both colors visible
   - Multiple files changed → Each file shown separately with stats

2. **Edge Cases:**
   - **New file added by student (not in starter):**
     - All lines should be green
     - No old line numbers (left column empty)
     - File header shows file as new

   - **File deleted by student (exists in starter):**
     - All lines should be red
     - No new line numbers (right column empty)
     - File header shows file as deleted

   - **Empty file changes:**
     - Handle gracefully, show appropriate message

   - **Binary file changes:**
     - Display message: "Binary file modified" (no diff content)

   - **Very large file (1000+ lines):**
     - Test scroll performance
     - Consider truncation message if needed

   - **No changes:**
     - Files are identical
     - Show message: "No changes detected in key files"

3. **Line Number Accuracy:**
   - Verify old line numbers match starter file
   - Verify new line numbers match student file
   - Test with multiple hunks in same file
   - Test line numbers around context lines

4. **File Statistics:**
   - Verify +/- counts match actual additions/deletions
   - Test with files that have only additions
   - Test with files that have only deletions
   - Test with mixed changes

#### **5.2: Error Scenarios**

1. **Invalid Repo URLs:**
   - Malformed GitHub URL → Show error message
   - Non-existent repo → Show error message
   - Private repo without access → Show error message

2. **API Issues:**
   - **Rate limit exceeded (403):**
     - Show friendly error message
     - Suggest waiting or adding GitHub token
     - Provide "View on GitHub" fallback link

   - **Network timeouts:**
     - Show connection error message
     - Provide retry option

3. **Branch Issues:**
   - Non-existent branch → Show error message
   - Empty branch → Show "no changes" message

#### **5.3: Visual Testing**

1. **Color Accuracy:**
   - Additions: Verify green background (#0d3818) and green marker (#3fb950)
   - Deletions: Verify red background (#3d1319) and red marker (#f85149)
   - Context: Verify gray text (#c9d1d9) on dark background (#0d1117)
   - Hunk headers: Verify blue-gray background (#1c2633)

2. **Typography:**
   - Verify monospace font renders correctly
   - Check font size is readable (12px)
   - Verify line height for proper spacing (20px)

3. **Layout:**
   - Line numbers align properly (50px width each)
   - Diff marker column is consistent (20px width)
   - Text doesn't overflow container
   - Horizontal scroll works for long lines

4. **Responsive Design:**
   - Test on mobile (320px width)
   - Test on tablet (768px width)
   - Test on desktop (1920px width)
   - Verify summary stats stack properly on mobile

5. **Interactive Elements:**
   - Hover states work on diff lines
   - Links are clickable (View on GitHub)
   - Scrolling is smooth for large diffs

#### **5.4: Cross-Browser Testing**

- Chrome/Edge (Chromium)
- Firefox
- Safari
- Mobile browsers

#### **5.5: Manual Testing Steps**

```bash
# 1. Setup test data
python seed_data.py  # If not already seeded

# 2. Run Flask app
python app.py

# 3. Navigate to instructor review
# http://localhost:5000/admin/submissions/<submission_id>/review

# 4. Verify checklist:
# [ ] Diff loads without errors
# [ ] Green highlights on additions
# [ ] Red highlights on deletions
# [ ] Line numbers display correctly
# [ ] File stats show correct counts (+X -Y)
# [ ] Summary stats at top match file stats
# [ ] "View on GitHub" link works
# [ ] Empty state shows for invalid repos
# [ ] Error messages are clear and helpful
# [ ] Styling matches GitHub PR aesthetic
# [ ] Responsive on mobile/tablet
# [ ] No console errors in browser DevTools

# 5. Test with different scenarios:
# - Create submission with real GitHub repo
# - Test with forked repo that has changes
# - Test with invalid repo URL
# - Test with private repo (should gracefully fail)
```

**Files for Testing:**
- Run application: `/Users/nathansuberi/Documents/GitHub/code-dojo/app.py`
- Test endpoint: http://localhost:5000/admin/submissions/<id>/review
- Check browser console for JavaScript errors
- Use browser DevTools to inspect CSS rendering

---

### **Phase 6: Performance & Optimization**

**Current Performance Concerns:**
- Diff generated on every page load (not cached)
- GitHub API rate limits: 60 requests/hour (unauthenticated)
- Multiple API calls per diff (file tree + file content for each file)
- Large diffs (many files or long files) could be slow

#### **6.1: Implement Diff Caching**

**Objective:** Store generated diffs to avoid repeated API calls.

**Approach:**

1. **Add `diff_content` column to Submission model:**
   ```python
   # models/submission.py
   class Submission(db.Model):
       # ... existing columns ...
       diff_content = db.Column(db.Text, nullable=True)
       diff_generated_at = db.Column(db.DateTime, nullable=True)
   ```

2. **Generate diff when submission is created:**
   ```python
   # routes/submissions.py - create endpoint
   # After creating submission:
   diff_content = fetch_github_diff(goal.starter_repo, repo_url, branch)
   submission.diff_content = diff_content
   submission.diff_generated_at = datetime.utcnow()
   db.session.commit()
   ```

3. **Use cached diff in review endpoint:**
   ```python
   # routes/admin.py - review endpoint
   # Check if diff is cached
   if submission.diff_content:
       diff_content = submission.diff_content
   else:
       # Fallback: generate on-demand
       diff_content = fetch_github_diff(goal.starter_repo, submission.repo_url, submission.branch)
   ```

4. **Add "Refresh Diff" button (optional):**
   - Button in instructor view to regenerate diff
   - Useful if student updates their repo after submission

**Files to Modify:**
- `/Users/nathansuberi/Documents/GitHub/code-dojo/models/submission.py` (add columns)
- `/Users/nathansuberi/Documents/GitHub/code-dojo/routes/submissions.py` (cache on create)
- `/Users/nathansuberi/Documents/GitHub/code-dojo/routes/admin.py` (use cache)

#### **6.2: Add GitHub Token Support**

**Objective:** Increase API rate limit from 60 to 5000 requests/hour.

**Approach:**

1. **Add to config:**
   ```python
   # config.py
   class Config:
       GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', None)
   ```

2. **Use token in requests:**
   ```python
   # services/github.py
   headers = {}
   if config.GITHUB_TOKEN:
       headers['Authorization'] = f'token {config.GITHUB_TOKEN}'

   response = requests.get(url, headers=headers, timeout=10)
   ```

3. **Document in README:**
   - How to create GitHub Personal Access Token
   - Required scopes: `public_repo` (for public repos)
   - How to set environment variable

**Files to Modify:**
- `/Users/nathansuberi/Documents/GitHub/code-dojo/config.py` (add GITHUB_TOKEN)
- `/Users/nathansuberi/Documents/GitHub/code-dojo/services/github.py` (use token in requests)

#### **6.3: Add Loading State**

**Objective:** Show loading indicator for slow diff generation.

**Approach:**

1. **Add loading state to template:**
   ```html
   <div id="diff-loading" class="loading-state">
       <div class="spinner"></div>
       <p>Loading code changes...</p>
   </div>

   <div id="diff-content" class="diff-container" style="display: none;">
       <!-- Diff content -->
   </div>
   ```

2. **Add JavaScript to show/hide:**
   ```javascript
   // Show loading initially
   document.getElementById('diff-loading').style.display = 'block';

   // When page loads, hide loading and show content
   window.addEventListener('load', function() {
       document.getElementById('diff-loading').style.display = 'none';
       document.getElementById('diff-content').style.display = 'block';
   });
   ```

**Files to Modify:**
- `/Users/nathansuberi/Documents/GitHub/code-dojo/templates/submissions/instructor_view.html`
- `/Users/nathansuberi/Documents/GitHub/code-dojo/static/css/styles.css` (add loading spinner CSS)

---

## Implementation Roadmap

### **Complete Implementation (All Phases - Priority)**

**Phase 1: Backend Diff Generation (CRITICAL)**
- ✅ Implement `difflib.unified_diff()` in `fetch_github_diff()`
- ✅ Generate proper unified diff format with +/- markers
- ✅ Handle new files (all additions)
- ✅ Handle deleted files (all deletions)
- ✅ Include file statistics metadata
- ✅ Robust error handling

**Phase 2: Frontend Rendering (CRITICAL)**
- ✅ Update `format_diff` filter to add line numbers
- ✅ Parse hunk headers to track line numbers
- ✅ Display old/new line numbers side-by-side
- ✅ Parse and display file statistics
- ✅ Update template with summary stats
- ✅ Enhanced HTML structure

**Phase 3: Visual Polish (CRITICAL)**
- ✅ Comprehensive CSS styling for GitHub-style aesthetic
- ✅ Line number styling and alignment
- ✅ File header with stats styling
- ✅ Summary stats bar styling
- ✅ Enhanced diff line colors (green/red)
- ✅ Improved empty state
- ✅ Responsive design for mobile/tablet
- ✅ "View on GitHub" link styling

**Phase 4: Backend Statistics (CRITICAL)**
- ✅ Calculate summary statistics (files changed, total +/-)
- ✅ Pass statistics to template
- ✅ Add helper function for stats calculation

**Phase 5: Testing (CRITICAL)**
- ✅ Test all functional scenarios
- ✅ Test edge cases (new files, deleted files, etc.)
- ✅ Visual testing across browsers
- ✅ Responsive testing
- ✅ Error scenario testing

**Phase 6: Performance Optimization (HIGH PRIORITY)**
- ✅ Implement diff caching in database
- ✅ Add GitHub token support
- ✅ Add loading state for slow generation
- ✅ Database migration for new columns

---

## Success Criteria

**The implementation is complete when:**

1. ✅ **Functionality:**
   - Diff accurately shows all added lines (green with +)
   - Diff accurately shows all removed lines (red with -)
   - Line numbers are correct and aligned
   - File statistics are accurate
   - Summary statistics match individual file stats

2. ✅ **Visual Quality:**
   - Matches GitHub PR aesthetic exactly
   - Green additions with proper color (#3fb950)
   - Red deletions with proper color (#f85149)
   - Professional typography and spacing
   - Clean, intuitive layout
   - Beautiful empty states

3. ✅ **User Experience:**
   - Immediately obvious what changed
   - Easy to scan additions and deletions
   - Line numbers help locate code in files
   - Summary stats provide quick overview
   - Helpful error messages
   - Responsive on all device sizes

4. ✅ **Performance:**
   - Page loads in < 2 seconds for typical diffs
   - Diffs are cached to avoid repeated API calls
   - Graceful handling of rate limits
   - Smooth scrolling for large diffs

5. ✅ **Robustness:**
   - Handles all edge cases gracefully
   - Clear error messages
   - No visual bugs or layout issues
   - Works across major browsers
   - Accessible and keyboard-navigable

---

## Key Files Reference

### **Critical Files (Must Modify):**
1. `/Users/nathansuberi/Documents/GitHub/code-dojo/services/github.py` (lines 26-96)
   - Core diff generation logic

2. `/Users/nathansuberi/Documents/GitHub/code-dojo/app.py` (lines 45-82)
   - Diff rendering filter with line numbers

3. `/Users/nathansuberi/Documents/GitHub/code-dojo/static/css/styles.css` (lines 958-1122+)
   - Complete visual styling

4. `/Users/nathansuberi/Documents/GitHub/code-dojo/templates/submissions/instructor_view.html` (lines 33-43)
   - Template structure with stats

5. `/Users/nathansuberi/Documents/GitHub/code-dojo/routes/admin.py` (lines 29-71)
   - Pass statistics to template

### **Secondary Files (For Optimization):**
6. `/Users/nathansuberi/Documents/GitHub/code-dojo/models/submission.py`
   - Add diff caching columns

7. `/Users/nathansuberi/Documents/GitHub/code-dojo/config.py`
   - Add GitHub token config

8. `/Users/nathansuberi/Documents/GitHub/code-dojo/routes/submissions.py`
   - Cache diff on creation

---

## Data Flow

```
Instructor views submission review
  ↓
routes/admin.py::review_submission()
  ↓
services/github.py::fetch_github_diff(starter_url, student_url, branch)
  ├─ Fetch file trees from both repos (GitHub API)
  ├─ Identify changed files (SHA comparison)
  ├─ For each changed file:
  │   ├─ Fetch content from starter repo
  │   ├─ Fetch content from student repo
  │   ├─ Generate unified diff with difflib
  │   └─ Add file statistics metadata
  ↓
Return unified diff string with stats
  ↓
routes/admin.py calculates summary stats
  ↓
Pass diff_content + stats to template
  ↓
template renders with {{ diff_content | format_diff }}
  ↓
app.py::format_diff_filter()
  ├─ Parse unified diff format
  ├─ Extract line numbers from hunk headers
  ├─ Generate HTML with line numbers
  ├─ Add CSS classes for styling
  └─ Return formatted HTML
  ↓
CSS renders beautiful GitHub-style diff
  ├─ Green backgrounds for additions
  ├─ Red backgrounds for deletions
  ├─ Line numbers styled and aligned
  ├─ File headers with stats
  └─ Summary bar at top
```

---

## Testing Commands

```bash
# Run Flask application
python app.py

# Navigate to instructor review page
# http://localhost:5000/admin/submissions/<submission_id>/review

# For testing, you can use these demo repos:
# Starter: https://github.com/octocat/Hello-World
# Student: (fork with changes)

# Check console for errors
# Browser DevTools → Console

# Inspect styling
# Browser DevTools → Elements → Inspect diff viewer

# Test responsiveness
# Browser DevTools → Toggle device toolbar
# Test at: 320px (mobile), 768px (tablet), 1920px (desktop)
```

---

## Example Unified Diff Output

**Goal:** The `fetch_github_diff()` function should produce output like this:

```diff
diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -10,7 +10,8 @@ def hello():
     print("Starting app")
     return "Hello"
-    return "Old line"
+    return "New line"
+    print("Added line")
     # Context continues

diff --git a/models.py b/models.py
--- a/models.py
+++ b/models.py
@@ -15,6 +15,12 @@ class User:
     def __init__(self, name):
         self.name = name
+        self.created_at = datetime.now()
+
+    def get_profile(self):
+        return {
+            'name': self.name,
+            'created': self.created_at
+        }
```

**Result:** This will render as:
- Line numbers on left (old) and right (new)
- Red background for `- return "Old line"`
- Green background for `+ return "New line"` and `+ print("Added line")`
- File stats: `app.py +2 -1`
- Summary: `2 files changed +8 -1`

---

This comprehensive plan provides complete context for implementing a polished, professional GitHub-style diff viewer that will delight instructors and make code review intuitive and efficient.
