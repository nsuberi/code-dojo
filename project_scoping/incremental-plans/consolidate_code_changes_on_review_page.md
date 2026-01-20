# Plan: Fix PR Code Changes Visualization

## Overview
Investigate and fix the "Code Changes" dropdown visualization in the Review tab. The implementation appears complete (CSS, JavaScript, API endpoints all exist), but the file content is not displaying correctly as shown in the React example.

## Current Implementation Status

### ✅ Already Implemented
1. **PR-based submission system** - Users submit PR URLs, not repo+branch
2. **GitHub API integration** - Fetches PR metadata and file changes via `/submissions/<id>/files`
3. **UI structure** - "Pull Request Information" and "Code Changes" sections exist side-by-side in goal.html (lines 360-499)
4. **JavaScript rendering** - review-tab.js has complete diff rendering logic (lines 245-435)
5. **CSS styling** - styles.css contains comprehensive diff visualization styles (lines 2629-2825)

### 🔍 Investigation Findings

**User Report:** Diffs are loading and displaying, but they look wrong (no colors, bad formatting) when tested with a real PR.

**Key Files:**
- **Template:** `/Users/nathansuberi/Documents/GitHub/code-dojo/templates/modules/goal.html` (lines 465-499)
- **JavaScript:** `/Users/nathansuberi/Documents/GitHub/code-dojo/static/js/review-tab.js` (lines 245-435)
- **Styles:** `/Users/nathansuberi/Documents/GitHub/code-dojo/static/css/styles.css` (lines 2629-2825)
- **API Route:** `/Users/nathansuberi/Documents/GitHub/code-dojo/routes/submissions.py` (lines 286-313)

**Root Cause Identified: CSS Styling Issues**

Since diffs are loading but displaying incorrectly, the issue is CSS-related, not JavaScript or API:

1. **CSS conflicts** - Multiple `.diff-line` definitions in styles.css (lines 1124 vs 2725) - earlier dark theme styles (#0d1117 background) conflict with later light theme styles
2. **CSS specificity issues** - Earlier `.diff-viewer` and `.diff-container` dark theme styles (lines 585-1350) may be overriding the correct light theme styles (lines 2629-2825)
3. **Missing CSS properties** - React example has critical properties not in current CSS:
   - `word-break: break-all` on `.diff-line` - prevents horizontal overflow
   - `border-right: 1px solid #e2e8f0` on `.line-number` - visual separation
   - `user-select: none` on `.line-number` - prevents line number selection
   - `flex-shrink: 0` on `.line-number` - prevents column collapsing
4. **Background color issues** - `.diff-line.context` uses `var(--card-bg)` which may be transparent or wrong color

## Implementation Plan

### Step 1: Diagnose CSS Specificity and Conflicts

**Actions:**
1. Use browser DevTools Elements inspector on a rendered diff line
2. Check "Computed" tab to see which CSS rules are being applied
3. Look for strikethrough styles indicating overridden rules
4. Verify that color styles (green/red backgrounds) are being applied
5. Check if dark theme styles from earlier in CSS file are taking precedence

**Expected Findings:**
- Dark theme backgrounds (#0d1117, #161b22) being applied instead of light (#dcfce7, #fee2e2)
- Line numbers missing border-right separator
- Long lines causing horizontal scroll issues
- Context lines showing wrong background color

### Step 2: Fix CSS Conflicts and Add Missing Properties

**File:** `static/css/styles.css`

**Critical Actions (in order):**

1. **Remove ALL old dark theme diff styles** (lines ~585-1350):
   - Delete `.diff-viewer` styles with dark backgrounds (#1e293b, #0d1117)
   - Delete `.diff-container` styles with dark backgrounds (#0d1117)
   - Delete `.diff-file-header` styles with dark backgrounds (#161b22)
   - Delete `.diff-line` styles with dark backgrounds (lines ~1124-1133)
   - These are conflicting with the correct light theme styles below

2. **Keep ONLY the light theme styles** (lines ~2629-2825) and enhance them:

   ```css
   /* File Tree - KEEP AS IS */
   .file-tree { ... }

   /* Diff Container - KEEP AS IS */
   .diff-container {
       margin-bottom: 1rem;
   }

   /* Diff Viewer - KEEP AS IS */
   .diff-viewer {
       border: 1px solid var(--border-color);
       border-radius: 8px;
       overflow: hidden;
   }

   /* Diff File Header - KEEP AS IS */
   .diff-file-header {
       padding: 0.75rem 1rem;
       background: #f1f5f9;
       border-bottom: 1px solid var(--border-color);
       display: flex;
       align-items: center;
       justify-content: space-between;
   }

   /* Diff Content Container - ENHANCE */
   .diff-content {
       overflow-x: auto;
       background: white; /* ADD THIS - ensure white background */
   }

   /* Diff Lines - ENHANCE */
   .diff-line {
       display: flex;
       font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
       font-size: 12px;
       line-height: 1.5;
       white-space: pre-wrap;
       word-break: break-all; /* ADD THIS - prevents overflow */
   }

   /* Line Numbers - ENHANCE */
   .line-number {
       min-width: 50px;
       padding: 2px 10px;
       text-align: right;
       color: #64748b; /* Specific color instead of var */
       background: #f8fafc; /* Specific color instead of var */
       border-right: 1px solid #e2e8f0; /* ADD THIS - visual separator */
       user-select: none; /* ADD THIS - prevents selection */
       flex-shrink: 0; /* ADD THIS - prevents shrinking */
   }

   /* Line Content - ENHANCE */
   .line-content {
       flex: 1;
       padding: 2px 10px;
       overflow-wrap: break-word; /* ADD THIS - better word breaking */
   }

   /* Addition Lines - KEEP BUT VERIFY */
   .diff-line.add {
       background: #dcfce7; /* Light green */
       border-left: 3px solid #86efac; /* Green border */
   }

   .diff-line.add .line-number {
       background: #dcfce7; /* Match parent */
   }

   /* Deletion Lines - KEEP BUT VERIFY */
   .diff-line.remove {
       background: #fee2e2; /* Light red */
       border-left: 3px solid #fca5a5; /* Red border */
   }

   .diff-line.remove .line-number {
       background: #fee2e2; /* Match parent */
   }

   /* Context Lines - FIX */
   .diff-line.context {
       background: white; /* Change from var(--card-bg) to explicit white */
   }

   /* Hunk Headers - KEEP */
   .diff-line.hunk {
       background: #e0f2fe; /* Light blue */
       color: #64748b;
       font-weight: 600;
   }

   .diff-line.hunk .line-content {
       color: #0369a1;
       padding: 4px 10px;
   }
   ```

3. **Add "No diff" styling**:
   ```css
   .no-diff {
       padding: 2rem;
       text-align: center;
       color: var(--text-secondary);
       background: #f8fafc;
       border-radius: 8px;
       font-style: italic;
   }
   ```

**Why:** Multiple style definitions with conflicting colors are causing the dark theme to appear. The React example works because it uses inline styles that have highest specificity. We need to remove conflicts and use specific color values instead of CSS variables that might resolve incorrectly.

### Step 3: Verify JavaScript is Correct (No Changes Expected)

**File:** `static/js/review-tab.js`

**Verification Steps:**
1. Confirm `parseDiffToHtml()` (lines 371-418) generates correct class names:
   - `.diff-line.hunk` for hunk headers
   - `.diff-line.add` for additions
   - `.diff-line.remove` for deletions
   - `.diff-line.context` for context lines
   - `.line-number` for line numbers (two per line)
   - `.line-content` for actual code content

2. Confirm structure matches React example:
   ```html
   <div class="diff-line add">
       <div class="line-number"></div>      <!-- old line # (empty for additions) -->
       <div class="line-number">123</div>    <!-- new line # -->
       <div class="line-content">+added code</div>
   </div>
   ```

**Expected Result:** JavaScript is likely fine since diffs are rendering, just without proper styling. No changes needed unless class names don't match CSS.

### Step 4: Test the Fix

**Testing with Browser DevTools:**

1. **Clear browser cache** to ensure new CSS loads
2. **Hard refresh** the page (Cmd+Shift+R / Ctrl+Shift+R)
3. **Open DevTools** → Elements tab
4. **Inspect a diff line element**:
   - Should have class `diff-line add` (or `remove`, `context`, `hunk`)
   - Computed styles should show:
     - Background: `#dcfce7` for additions (green)
     - Background: `#fee2e2` for deletions (red)
     - Background: `white` for context
     - Border-left: green or red 3px solid
5. **Inspect a line number element**:
   - Should have class `line-number`
   - Computed styles should show:
     - Background: `#f8fafc`
     - Border-right: `1px solid #e2e8f0`
     - User-select: `none`

**Visual Verification:**
- ✅ Additions show with light green background
- ✅ Deletions show with light red background
- ✅ Context lines show with white background
- ✅ Line numbers are in a separate column with light gray background
- ✅ Vertical line separates line numbers from content
- ✅ Long lines wrap without breaking layout
- ✅ Hunk headers show with light blue background

### Step 5: Additional Improvements (Optional)

**Only if basic styling is working correctly:**

1. **Add syntax highlighting** (future enhancement):
   - Use Prism.js or Highlight.js for code syntax coloring
   - Apply after diff is rendered
   - Respect file type (Python, JavaScript, etc.)

2. **Add diff stats summary**:
   - Show total lines changed at top of diff
   - Display visual bar graph of additions/deletions
   - Match GitHub's diff stats display

3. **Add copy button**:
   - Allow users to copy file content
   - Add "Copy" button to diff-file-header
   - Use Clipboard API

4. **Improve performance**:
   - Lazy load diffs (only render when file is expanded)
   - Virtualize long diffs (only render visible lines)
   - Add loading skeleton while rendering

## Alternative Approach (If Current Implementation Has Fundamental Issues)

If investigation reveals that the current implementation has architectural problems, consider:

1. **Replace with server-side rendering:**
   - Generate formatted HTML on the backend (format_diff already exists in app.py)
   - Send pre-rendered HTML to frontend
   - Eliminates JavaScript complexity
   - Better for SEO and accessibility

2. **Use GitHub's embed API:**
   - Leverage GitHub's native diff rendering
   - Requires less custom CSS/JS
   - Always matches GitHub's UI

3. **Simplify to "View on GitHub" link:**
   - Remove complex diff visualization entirely
   - Direct users to PR page on GitHub
   - Reduces maintenance burden
   - Ensures accurate representation

## Files to Modify

**Critical Files:**
1. `/Users/nathansuberi/Documents/GitHub/code-dojo/static/css/styles.css` - Fix CSS conflicts and add missing properties
2. `/Users/nathansuberi/Documents/GitHub/code-dojo/static/js/review-tab.js` - Add error handling and logging
3. `/Users/nathansuberi/Documents/GitHub/code-dojo/routes/submissions.py` - Improve API error responses

**Supporting Files:**
4. `/Users/nathansuberi/Documents/GitHub/code-dojo/templates/modules/goal.html` - May need HTML structure adjustments

## Verification Steps

### Manual Testing
1. Open browser DevTools (Console + Network tabs)
2. Navigate to a challenge with an existing submission
3. Switch to Review tab
4. Click "Load Code Changes" button
5. Monitor:
   - Network requests to `/submissions/<id>/files`
   - Console logs showing fetched data
   - DOM updates in Elements tab
   - Any JavaScript errors

### Debugging Questions to Answer
- **Is the API call succeeding?** Check Network tab for 200 status
- **Is the data being returned?** Check response JSON has `files` array with `patch` fields
- **Is JavaScript executing?** Check Console for logs
- **Are CSS classes being applied?** Check Elements tab for `.diff-line`, `.add`, `.remove` classes
- **Are styles being computed correctly?** Check Computed styles in DevTools

### Common Issues and Solutions

| Issue | Symptom | Solution |
|-------|---------|----------|
| Nothing happens on click | Button doesn't respond | Check JavaScript console for errors, verify function is defined |
| API returns 404 | "Error loading changes" message | Verify submission ID exists and PR URL is valid |
| API returns 403 | Rate limit message | Add GitHub token to config, implement caching |
| Files load but no diffs show | File list visible, but clicking does nothing | Check if `patch` field is empty, verify `toggleFileDiff()` is working |
| Diffs show but ugly | Text visible but not colored | Check CSS is loading, verify class names match |
| Long lines break layout | Horizontal overflow issues | Add `word-break`, `overflow-x: auto` |

## Expected Outcome

After implementing this plan:
1. **Code Changes section will render correctly** with color-coded diffs matching the React example
2. **File list will show** with proper icons, names, and stats
3. **Clicking files will expand** beautifully formatted diffs
4. **Error cases will be handled** with clear user feedback
5. **Performance will be acceptable** even with large PRs

The implementation will match the React example's functionality while leveraging the existing Flask/Jinja2 architecture.
