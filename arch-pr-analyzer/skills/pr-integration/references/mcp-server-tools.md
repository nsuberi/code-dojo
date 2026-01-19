## GitHub MCP Server Tool Reference

Complete reference for all GitHub MCP server tools used in PR integration.

## Tool: list_pull_requests

**Purpose:** List pull requests in a repository

**Parameters:**
```typescript
{
  owner: string;          // Repository owner (username or org)
  repo: string;           // Repository name
  state?: "open" | "closed" | "all";  // Default: "open"
  head?: string;          // Filter by head branch (format: "owner:branch")
  base?: string;          // Filter by base branch
  sort?: "created" | "updated" | "popularity" | "long-running";  // Default: "created"
  direction?: "asc" | "desc";  // Default: "desc"
  per_page?: number;      // Results per page (max: 100, default: 30)
  page?: number;          // Page number (default: 1)
}
```

**Returns:**
```typescript
Array<{
  number: number;
  title: string;
  state: "open" | "closed";
  user: { login: string; };
  created_at: string;
  updated_at: string;
  head: {
    ref: string;  // Branch name
    sha: string;  // Commit SHA
  };
  base: {
    ref: string;
    sha: string;
  };
}>
```

**Example:**
```javascript
// Find PR for current branch
const prs = await github.list_pull_requests({
  owner: "myorg",
  repo: "myrepo",
  state: "open",
  head: "myorg:feature-branch"
});
```

---

## Tool: get_pull_request

**Purpose:** Get details of a specific pull request

**Parameters:**
```typescript
{
  owner: string;          // Repository owner
  repo: string;           // Repository name
  pull_number: number;    // PR number
}
```

**Returns:**
```typescript
{
  number: number;
  title: string;
  body: string;           // PR description
  state: "open" | "closed";
  merged: boolean;
  mergeable: boolean | null;
  mergeable_state: string;
  user: {
    login: string;
    avatar_url: string;
  };
  head: {
    ref: string;         // Source branch name
    sha: string;         // Source commit SHA
    repo: {
      name: string;
      owner: { login: string; };
    };
  };
  base: {
    ref: string;         // Target branch name
    sha: string;         // Target commit SHA
    repo: {
      name: string;
      owner: { login: string; };
    };
  };
  created_at: string;
  updated_at: string;
  closed_at: string | null;
  merged_at: string | null;
  labels: Array<{
    name: string;
    color: string;
  }>;
  requested_reviewers: Array<{ login: string; }>;
  assignees: Array<{ login: string; }>;
}
```

**Example:**
```javascript
const pr = await github.get_pull_request({
  owner: "facebook",
  repo: "react",
  pull_number: 12345
});

console.log(`PR: ${pr.title}`);
console.log(`Base: ${pr.base.ref}, Head: ${pr.head.ref}`);
console.log(`Base SHA: ${pr.base.sha}, Head SHA: ${pr.head.sha}`);
```

---

## Tool: list_pr_files

**Purpose:** List files changed in a pull request

**Parameters:**
```typescript
{
  owner: string;
  repo: string;
  pull_number: number;
  per_page?: number;      // Default: 30, max: 100
  page?: number;          // Default: 1
}
```

**Returns:**
```typescript
Array<{
  filename: string;       // File path
  status: "added" | "modified" | "removed" | "renamed" | "copied" | "changed" | "unchanged";
  additions: number;      // Lines added
  deletions: number;      // Lines deleted
  changes: number;        // Total lines changed (additions + deletions)
  blob_url: string;       // URL to file on GitHub
  raw_url: string;        // URL to raw file content
  contents_url: string;   // API URL for file contents
  patch: string;          // Unified diff format (if available)
  previous_filename?: string;  // For renamed files
}>
```

**Example:**
```javascript
const files = await github.list_pr_files({
  owner: "myorg",
  repo: "myrepo",
  pull_number: 123,
  per_page: 100
});

for (const file of files) {
  console.log(`${file.status}: ${file.filename} (+${file.additions}, -${file.deletions})`);
}
```

**Pagination:**
```javascript
async function getAllFiles(owner, repo, prNumber) {
  let allFiles = [];
  let page = 1;

  while (true) {
    const files = await github.list_pr_files({
      owner, repo, pull_number: prNumber,
      per_page: 100, page
    });

    allFiles = allFiles.concat(files);

    if (files.length < 100) break;  // Last page
    page++;
  }

  return allFiles;
}
```

---

## Tool: get_file_contents

**Purpose:** Get content of a file at a specific commit

**Parameters:**
```typescript
{
  owner: string;
  repo: string;
  path: string;           // File path in repository
  ref?: string;           // Branch name, tag, or commit SHA (default: repo default branch)
}
```

**Returns:**
```typescript
{
  name: string;           // Filename
  path: string;           // Full path
  sha: string;            // File blob SHA
  size: number;           // File size in bytes
  url: string;            // API URL
  html_url: string;       // GitHub web URL
  git_url: string;        // Git blob URL
  download_url: string;   // Direct download URL
  type: "file";
  content: string;        // Base64 encoded content
  encoding: "base64";
}
```

**Decode content:**
```javascript
const fileData = await github.get_file_contents({
  owner: "myorg",
  repo: "myrepo",
  path: "src/auth/login.py",
  ref: "abc123def456"
});

const content = Buffer.from(fileData.content, 'base64').toString('utf8');
console.log(content);
```

**Before/after comparison:**
```javascript
// Get PR to find commit SHAs
const pr = await github.get_pull_request({owner, repo, pull_number});

// Get file at base commit (before)
const beforeFile = await github.get_file_contents({
  owner, repo,
  path: "src/auth/login.py",
  ref: pr.base.sha
});

// Get file at head commit (after)
const afterFile = await github.get_file_contents({
  owner, repo,
  path: "src/auth/login.py",
  ref: pr.head.sha
});

// Decode and compare
const beforeContent = Buffer.from(beforeFile.content, 'base64').toString('utf8');
const afterContent = Buffer.from(afterFile.content, 'base64').toString('utf8');
```

---

## Tool: list_commits

**Purpose:** List commits in a repository or branch

**Parameters:**
```typescript
{
  owner: string;
  repo: string;
  sha?: string;           // Branch name or commit SHA (default: repo default branch)
  path?: string;          // Filter by file path
  author?: string;        // Filter by author
  since?: string;         // ISO 8601 timestamp
  until?: string;         // ISO 8601 timestamp
  per_page?: number;      // Default: 30, max: 100
  page?: number;          // Default: 1
}
```

**Returns:**
```typescript
Array<{
  sha: string;
  commit: {
    message: string;
    author: {
      name: string;
      email: string;
      date: string;
    };
    committer: {
      name: string;
      email: string;
      date: string;
    };
  };
  author: {
    login: string;
    avatar_url: string;
  } | null;
  committer: {
    login: string;
  } | null;
  parents: Array<{ sha: string; }>;
}>
```

**Example:**
```javascript
// Get commits for PR branch
const commits = await github.list_commits({
  owner: "myorg",
  repo: "myrepo",
  sha: "feature-branch",
  per_page: 20
});

for (const commit of commits) {
  console.log(`${commit.sha.substring(0, 7)}: ${commit.commit.message}`);
}
```

---

## Tool: create_issue_comment

**Purpose:** Add a comment to an issue or pull request

**Parameters:**
```typescript
{
  owner: string;
  repo: string;
  issue_number: number;   // Use PR number here (PRs are issues)
  body: string;           // Comment text (markdown supported)
}
```

**Returns:**
```typescript
{
  id: number;
  body: string;
  user: { login: string; };
  created_at: string;
  updated_at: string;
  html_url: string;       // URL to comment
}
```

**Example:**
```javascript
const comment = await github.create_issue_comment({
  owner: "myorg",
  repo: "myrepo",
  issue_number: 123,    // PR number
  body: `## Architectural Analysis

**Impact:** Medium
**Risk:** Low

Full analysis: [link]`
});

console.log(`Comment posted: ${comment.html_url}`);
```

**Requires:** Write access to repository (repo scope)

---

## Tool: get_rate_limit

**Purpose:** Check current rate limit status

**Parameters:** None

**Returns:**
```typescript
{
  resources: {
    core: {
      limit: number;      // Max requests per hour
      remaining: number;  // Requests remaining
      reset: number;      // Unix timestamp when limit resets
      used: number;       // Requests used
    };
    search: {
      limit: number;
      remaining: number;
      reset: number;
      used: number;
    };
  };
  rate: {                 // Legacy format (same as core)
    limit: number;
    remaining: number;
    reset: number;
    used: number;
  };
}
```

**Example:**
```javascript
const rateLimit = await github.get_rate_limit();
const { remaining, limit, reset } = rateLimit.resources.core;

console.log(`Rate limit: ${remaining}/${limit}`);
console.log(`Resets at: ${new Date(reset * 1000)}`);

if (remaining < 100) {
  console.warn('Approaching rate limit!');
}
```

---

## Error Handling

### Common Error Codes

**404 Not Found:**
```json
{
  "message": "Not Found",
  "documentation_url": "https://docs.github.com/rest/..."
}
```

**Causes:**
- Repository doesn't exist
- Token lacks access (private repo)
- PR number doesn't exist
- Invalid owner/repo

**403 Forbidden:**
```json
{
  "message": "API rate limit exceeded",
  "documentation_url": "..."
}
```

**Causes:**
- Rate limit exceeded
- Token lacks required scopes
- Access denied

**422 Unprocessable Entity:**
```json
{
  "message": "Validation Failed",
  "errors": [...]
}
```

**Causes:**
- Invalid parameters
- PR number doesn't exist in repo
- Malformed request

### Error Handling Pattern

```javascript
async function safeGetPR(owner, repo, prNumber) {
  try {
    const pr = await github.get_pull_request({owner, repo, pull_number: prNumber});
    return { success: true, data: pr };
  } catch (error) {
    if (error.status === 404) {
      return {
        success: false,
        error: `PR #${prNumber} not found in ${owner}/${repo}. Check PR number and repository access.`
      };
    } else if (error.status === 403) {
      return {
        success: false,
        error: `Access denied to ${owner}/${repo}. Check token scopes and permissions.`
      };
    } else if (error.status === 422) {
      return {
        success: false,
        error: `Invalid request for PR #${prNumber}. Check parameters.`
      };
    } else {
      return {
        success: false,
        error: `GitHub API error: ${error.message}`
      };
    }
  }
}
```

---

## Rate Limiting Best Practices

**Check before expensive operations:**
```javascript
async function analyzePRWithRateCheck(owner, repo, prNumber) {
  // Check rate limit
  const rateLimit = await github.get_rate_limit();
  if (rateLimit.resources.core.remaining < 50) {
    throw new Error('Insufficient rate limit remaining. Please wait.');
  }

  // Proceed with analysis
  const pr = await github.get_pull_request({owner, repo, pull_number: prNumber});
  const files = await github.list_pr_files({owner, repo, pull_number: prNumber});
  // ...
}
```

**Implement exponential backoff:**
```javascript
async function withRetry(fn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (error.status === 429 && i < maxRetries - 1) {
        const waitTime = Math.pow(2, i) * 1000;  // 1s, 2s, 4s
        await new Promise(resolve => setTimeout(resolve, waitTime));
      } else {
        throw error;
      }
    }
  }
}

// Usage
const pr = await withRetry(() => github.get_pull_request({owner, repo, pull_number: 123}));
```

---

## Performance Optimization

**Parallel requests (respecting rate limits):**
```javascript
async function getPRDataParallel(owner, repo, prNumber) {
  // Fetch PR details and files in parallel
  const [pr, files] = await Promise.all([
    github.get_pull_request({owner, repo, pull_number: prNumber}),
    github.list_pr_files({owner, repo, pull_number: prNumber, per_page: 100})
  ]);

  return { pr, files };
}
```

**Batch file fetching (with concurrency limit):**
```javascript
async function batchFetchFiles(owner, repo, paths, ref, concurrency = 5) {
  const results = [];

  for (let i = 0; i < paths.length; i += concurrency) {
    const batch = paths.slice(i, i + concurrency);
    const batchResults = await Promise.all(
      batch.map(path => github.get_file_contents({owner, repo, path, ref}))
    );
    results.push(...batchResults);
  }

  return results;
}
```

---

## Complete Workflow Example

```javascript
async function analyzePR(owner, repo, prNumber) {
  // 1. Get PR details
  const pr = await github.get_pull_request({owner, repo, pull_number: prNumber});
  console.log(`Analyzing PR #${prNumber}: ${pr.title}`);

  // 2. Get changed files
  const files = await github.list_pr_files({owner, repo, pull_number: prNumber, per_page: 100});
  console.log(`Files changed: ${files.length}`);

  // 3. Get file contents for analysis (selective)
  const pythonFiles = files.filter(f => f.filename.endsWith('.py') && f.status !== 'removed');

  for (const file of pythonFiles) {
    // Get before and after content
    const [beforeContent, afterContent] = await Promise.all([
      github.get_file_contents({owner, repo, path: file.filename, ref: pr.base.sha})
        .catch(() => null),  // File might not exist in base
      github.get_file_contents({owner, repo, path: file.filename, ref: pr.head.sha})
    ]);

    // Analyze changes
    // ...
  }

  // 4. Get commit context
  const commits = await github.list_commits({owner, repo, sha: pr.head.ref, per_page: 20});
  console.log(`Commits in PR: ${commits.length}`);

  // 5. Generate report
  const report = generateReport(pr, files, commits);

  // 6. Optionally post comment
  if (shouldPostComment) {
    await github.create_issue_comment({
      owner, repo,
      issue_number: prNumber,
      body: report.summary
    });
  }

  return report;
}
```

This reference provides complete details for all GitHub MCP tools used in PR integration workflows.
