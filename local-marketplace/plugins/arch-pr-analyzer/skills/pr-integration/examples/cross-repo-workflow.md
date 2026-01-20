## Cross-Repository PR Analysis Workflow Example

This example shows how to analyze a PR from an external repository (e.g., a dependency you're considering upgrading).

### Scenario

You're using `lodash` v4.17.20 and considering upgrading to v4.17.21. You want to review the architectural changes in the PR that introduced the new version.

### Step 1: Find the PR URL

From lodash repository: `https://github.com/lodash/lodash/pull/5432`

### Step 2: Parse the URL

```javascript
function parseGitHubPRUrl(url) {
  const regex = /github\.com\/([^\/]+)\/([^\/]+)\/pull\/(\d+)/;
  const match = url.match(regex);

  if (!match) {
    throw new Error('Invalid GitHub PR URL format');
  }

  return {
    owner: match[1],      // "lodash"
    repo: match[2],       // "lodash"
    prNumber: parseInt(match[3], 10)  // 5432
  };
}

const { owner, repo, prNumber } = parseGitHubPRUrl("https://github.com/lodash/lodash/pull/5432");
```

### Step 3: Fetch PR Data

```javascript
// Get PR details
const pr = await github.get_pull_request({
  owner: "lodash",
  repo: "lodash",
  pull_number: 5432
});

console.log(`PR Title: ${pr.title}`);
console.log(`State: ${pr.state}`);
console.log(`Base: ${pr.base.ref} → Head: ${pr.head.ref}`);
```

**Output:**
```
PR Title: Fix security vulnerability in template function
State: closed (merged)
Base: master → Head: fix/template-security
```

### Step 4: Get Changed Files

```javascript
const files = await github.list_pr_files({
  owner: "lodash",
  repo: "lodash",
  pull_number: 5432,
  per_page: 100
});

console.log(`Files changed: ${files.length}`);

for (const file of files) {
  console.log(`${file.status}: ${file.filename} (+${file.additions}, -${file.deletions})`);
}
```

**Output:**
```
Files changed: 4
modified: src/template.js (+23, -8)
modified: test/template.test.js (+45, -12)
added: docs/security.md (+56, -0)
modified: README.md (+3, -1)
```

### Step 5: Analyze Changes

```javascript
// Focus on template.js changes
const templateFile = files.find(f => f.filename === 'src/template.js');

// Get before/after content
const [beforeContent, afterContent] = await Promise.all([
  github.get_file_contents({
    owner: "lodash",
    repo: "lodash",
    path: "src/template.js",
    ref: pr.base.sha
  }),
  github.get_file_contents({
    owner: "lodash",
    repo: "lodash",
    path: "src/template.js",
    ref: pr.head.sha
  })
]);

// Decode base64
const before = Buffer.from(beforeContent.content, 'base64').toString('utf8');
const after = Buffer.from(afterContent.content, 'base64').toString('utf8');

// Analyze architectural impact
analyzeCodeChanges(before, after);
```

### Step 6: Generate Cross-Repo Analysis Report

```markdown
# Architectural Analysis: lodash PR #5432

**External Repository:** lodash/lodash
**PR:** Fix security vulnerability in template function
**Analyzed for:** Upgrade impact assessment

## Changes Summary

**Scope:** Low (1 core function modified)
**Risk:** High (Security fix - breaking behavior change)
**Complexity:** Low (31 lines across 1 core file)

## Core Change: Template Function

**What changed:**
- Added input sanitization to prevent code injection
- Changed escaping behavior for template variables
- Added security validation layer

**Impact on your application:**
If you use `_.template()` with user-provided input:
- ✅ **Benefit:** Protection against code injection attacks
- ⚠️ **Breaking:** Templates with special characters may render differently
- 🔴 **Action required:** Test all template usage

## Upgrade Recommendation

**Should upgrade:** YES - Security fix
**Priority:** High
**Testing required:**
1. Test all uses of `_.template()` in your codebase
2. Check templates with special characters: `<`, `>`, `&`, `"`, `'`
3. Verify no rendering changes in production templates

## Your Codebase Usage

**Found 12 uses of _.template():**
- `src/email/templates.js`: 8 instances
- `src/reports/generator.js`: 3 instances
- `src/admin/export.js`: 1 instance

**Recommendation:** Review all 12 uses before upgrading

---

**Analysis performed:** 2026-01-19 14:45:00
**Cross-repository analysis:** lodash/lodash
**Tool:** Claude Architecture PR Analyzer v0.1.0
```

### Step 7: Save Results

```javascript
const analysis = {
  repository: { owner: "lodash", repo: "lodash" },
  prNumber: 5432,
  title: pr.title,
  impact: "high-security",
  recommendation: "upgrade",
  yourUsageCount: 12,
  testingRequired: true
};

// Save to .claude/analyses/
const filename = `pr-lodash-lodash-5432-${timestamp}.md`;
await saveAnalysis(filename, reportContent);

console.log(`Cross-repository analysis saved: ${filename}`);
```

## Benefits of Cross-Repository Analysis

**For dependency upgrades:**
1. **Informed decisions:** Understand what changed before upgrading
2. **Risk assessment:** Identify breaking changes in dependencies
3. **Testing strategy:** Know what to test in your codebase
4. **Impact preview:** See architectural changes before they affect you

**For learning:**
1. Study how other projects solve problems
2. Understand architectural patterns in popular libraries
3. Learn from security fixes and improvements

**For contributing:**
1. Analyze PRs before submitting similar changes
2. Understand project architecture before contributing
3. Review related PRs for context

## Error Handling for Cross-Repository

```javascript
async function analyzeCrossRepoPR(url) {
  // Parse URL
  let owner, repo, prNumber;
  try {
    ({ owner, repo, prNumber } = parseGitHubPRUrl(url));
  } catch (error) {
    return {
      success: false,
      error: "Invalid GitHub PR URL. Expected format: https://github.com/owner/repo/pull/123"
    };
  }

  // Check access
  try {
    const pr = await github.get_pull_request({ owner, repo, pull_number: prNumber });
    return { success: true, data: pr };
  } catch (error) {
    if (error.status === 404) {
      return {
        success: false,
        error: `Could not access ${owner}/${repo} PR #${prNumber}.

Possible reasons:
1. Repository is private and your token lacks access
2. PR number doesn't exist
3. Repository doesn't exist

If this is a private repo, ensure your token has 'repo' scope.`
      };
    } else if (error.status === 403) {
      return {
        success: false,
        error: `Access forbidden to ${owner}/${repo}.

Your token may need:
- Higher rate limit (currently exceeded)
- Different scopes (private repo requires 'repo')
- Repository access (be added as collaborator)`
      };
    }

    throw error;  // Unexpected error
  }
}
```

## Complete CLI Example

```bash
# Analyze external repository PR
/arch-analyze medium --pr https://github.com/lodash/lodash/pull/5432

# Output shows:
# - Cross-repository indicator
# - Security/upgrade impact assessment
# - Testing recommendations for your codebase
# - File saved with cross-repo prefix
```

This cross-repository capability enables analyzing any public (or accessible private) GitHub PR to inform upgrade decisions, security assessments, and architectural learning.
