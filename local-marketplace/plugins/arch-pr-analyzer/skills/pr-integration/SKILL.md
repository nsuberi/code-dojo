---
name: PR Integration
description: This skill should be used when integrating with GitHub Pull Requests, fetching PR data via MCP server, parsing GitHub PR URLs, detecting repositories from git remotes, or handling cross-repository PR analysis. Load when user asks to "fetch PR data", "parse GitHub URL", "get PR details", "list PR files", "detect current repository", or "analyze cross-repository PR".
version: 0.1.0
---

# PR Integration with GitHub MCP

## Overview

This skill provides patterns for integrating with GitHub Pull Requests via the GitHub MCP server. The MCP server enables cross-repository operations, allowing analysis of PRs in any repository the token has access to.

## GitHub MCP Server Configuration

### MCP Server Setup

The plugin uses the official GitHub MCP server configured in `.mcp.json`:

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

**Server type:** stdio (npx command)
**Package:** `@modelcontextprotocol/server-github`
**Authentication:** Personal Access Token via environment variable

### Required Token Scopes

**For public repositories:**
- `public_repo`: Access to public repositories

**For private repositories:**
- `repo`: Full repository access (includes private repositories)

**Recommended:** Use `repo` scope for maximum flexibility

## Core MCP Operations

### 1. List Pull Requests

**Tool:** `list_pull_requests`

**Purpose:** Find PRs by criteria or list all PRs in a repository

**Parameters:**
```json
{
  "owner": "facebook",
  "repo": "react",
  "state": "open",
  "per_page": 30,
  "page": 1
}
```

**Use cases:**
- Auto-detect PR from current branch
- List all open PRs in repository
- Find specific PR by branch name

**Example usage:**
```javascript
// Find PRs for current branch
const branch = await exec('git rev-parse --abbrev-ref HEAD');
const prs = await github.list_pull_requests({
  owner: "myorg",
  repo: "myrepo",
  state: "open",
  head: `myorg:${branch}`  // Filter by head branch
});
```

### 2. Get PR Details

**Tool:** `get_pull_request`

**Purpose:** Retrieve complete PR metadata

**Parameters:**
```json
{
  "owner": "vercel",
  "repo": "next.js",
  "pull_number": 67890
}
```

**Returns:**
- Title and description/body
- Base branch (target) and head branch (source)
- Base commit SHA and head commit SHA
- Author information
- State (open, closed, merged)
- Mergeable status
- Created/updated timestamps
- Labels, reviewers, assignees

**Use cases:**
- Get PR context for analysis
- Extract commit SHAs for file comparison
- Check PR status and metadata

### 3. List Changed Files

**Tool:** `list_pr_files`

**Purpose:** Get all files changed in the PR with diff statistics

**Parameters:**
```json
{
  "owner": "facebook",
  "repo": "react",
  "pull_number": 12345,
  "per_page": 100
}
```

**Returns array of:**
```json
{
  "filename": "src/auth/login.py",
  "status": "modified",
  "additions": 45,
  "deletions": 12,
  "changes": 57,
  "patch": "@@  -10,7 +10,8 @@\n..."
}
```

**File statuses:**
- `added`: New file
- `modified`: Changed file
- `removed`: Deleted file
- `renamed`: File moved/renamed

**Use cases:**
- Identify which files changed
- Get line change statistics
- Extract diffs for analysis

### 4. Get File Contents

**Tool:** `get_file_contents`

**Purpose:** Fetch file content at specific commit

**Parameters:**
```json
{
  "owner": "myorg",
  "repo": "myrepo",
  "path": "src/auth/login.py",
  "ref": "abc123def456"
}
```

**Use cases:**
- Get file at base commit (before state)
- Get file at head commit (after state)
- Compare files across commits

**Strategy for before/after analysis:**
1. Use `get_pull_request` to get base_sha and head_sha
2. Fetch file at base: `get_file_contents(path, ref=base_sha)`
3. Fetch file at head: `get_file_contents(path, ref=head_sha)`
4. Compare contents locally

### 5. List Commits

**Tool:** `list_commits`

**Purpose:** Get commit history for context

**Parameters:**
```json
{
  "owner": "myorg",
  "repo": "myrepo",
  "sha": "feature-branch",
  "per_page": 20
}
```

**Returns array of:**
- Commit SHA
- Commit message
- Author information
- Timestamp
- Parent commits

**Use cases:**
- Understand evolution of changes
- Extract commit messages for context
- Identify related commits

### 6. Add Comment to PR (Optional)

**Tool:** `create_issue_comment`

**Purpose:** Post analysis results back to PR

**Parameters:**
```json
{
  "owner": "myorg",
  "repo": "myrepo",
  "issue_number": 123,
  "body": "## Architectural Analysis\n\n..."
}
```

**Note:** PRs are issues in GitHub API, so use `issue_number` for PR number

**Requires:** Write access to repository (`repo` scope)

**Use case:** Share analysis summary in PR for team visibility

## Cross-Repository Analysis

### GitHub PR URL Parsing

**URL format:**
```
https://github.com/{owner}/{repo}/pull/{number}
```

**Parsing logic:**
```javascript
function parseGitHubPRUrl(url) {
  const regex = /github\.com\/([^\/]+)\/([^\/]+)\/pull\/(\d+)/;
  const match = url.match(regex);

  if (!match) {
    throw new Error('Invalid GitHub PR URL');
  }

  return {
    owner: match[1],
    repo: match[2],
    prNumber: parseInt(match[3], 10)
  };
}
```

**Examples:**
- `https://github.com/facebook/react/pull/12345` → owner=facebook, repo=react, pr=12345
- `https://github.com/vercel/next.js/pull/67890` → owner=vercel, repo=next.js, pr=67890

### Current Repository Detection

**Get git remote URL:**
```bash
git remote get-url origin
```

**Remote URL formats:**
- HTTPS: `https://github.com/owner/repo.git`
- SSH: `git@github.com:owner/repo.git`

**Parsing logic:**
```javascript
function parseGitRemote(remoteUrl) {
  // HTTPS format
  let match = remoteUrl.match(/github\.com\/([^\/]+)\/([^\/\.]+)/);
  if (match) {
    return { owner: match[1], repo: match[2] };
  }

  // SSH format
  match = remoteUrl.match(/github\.com:([^\/]+)\/([^\/\.]+)/);
  if (match) {
    return { owner: match[1], repo: match[2] };
  }

  throw new Error('Could not parse GitHub remote URL');
}
```

### Access Control

**Token must have appropriate access:**

**Public repos:**
- Any valid token with `public_repo` or `repo` scope

**Private repos:**
- Token must have `repo` scope
- Token owner must have repository access (collaborator or org member)

**Organization repos:**
- Token owner must be org member with appropriate permissions
- Org settings may restrict personal access tokens

## Error Handling

### Common Errors

**404 Not Found:**
- Repository doesn't exist, OR
- Token lacks access, OR
- PR number is invalid

**Handle:** Provide clear guidance on checking access and PR number

**403 Forbidden:**
- Token lacks required scopes
- Rate limit exceeded
- Repository access denied

**Handle:** Check token scopes, rate limits

**422 Unprocessable Entity:**
- Invalid parameters
- PR number doesn't exist in that repository

**Handle:** Validate inputs, check PR number

### Error Messages

**For 404 errors:**
```
Could not access PR #123 in facebook/react.

Possible causes:
1. Repository doesn't exist or is private
2. Your GitHub token lacks access to this repository
3. PR number is incorrect

If this is a private repository, ensure your token has 'repo' scope
and you have repository access.
```

**For 403 errors:**
```
Access denied to facebook/react.

Your token needs:
- Scope: 'repo' for private repos, 'public_repo' for public
- Repository access: Collaborator or org member

Check token permissions: GitHub Settings > Developer settings > PAT
```

**For rate limit:**
```
GitHub API rate limit exceeded.

Status:
- Limit: 5,000/hour
- Remaining: 0
- Resets: {timestamp}

Options:
1. Wait for reset
2. Enable caching: cache_pr_data: true
```

## Usage Patterns

### Pattern 1: Current Repository Analysis

**Scenario:** User runs `/arch-analyze 123` in their project

**Steps:**
1. Get current repo: `git remote get-url origin`
2. Parse to extract owner/repo
3. Use PR number from user
4. Fetch PR data from current repo

```javascript
const remoteUrl = await exec('git remote get-url origin');
const { owner, repo } = parseGitRemote(remoteUrl);
const prNumber = 123;

const pr = await github.get_pull_request({ owner, repo, pull_number: prNumber });
```

### Pattern 2: Cross-Repository Analysis

**Scenario:** User provides full GitHub URL

**Steps:**
1. Parse GitHub URL
2. Extract owner, repo, prNumber
3. Fetch PR data from specified repo

```javascript
const url = "https://github.com/facebook/react/pull/12345";
const { owner, repo, prNumber } = parseGitHubPRUrl(url);

const pr = await github.get_pull_request({ owner, repo, pull_number: prNumber });
```

### Pattern 3: Auto-Detect from Branch

**Scenario:** User runs `/arch-analyze` with no PR specified

**Steps:**
1. Get current repo
2. Get current branch: `git rev-parse --abbrev-ref HEAD`
3. Search for PRs with this head branch
4. Handle 0, 1, or multiple results

```javascript
const { owner, repo } = parseGitRemote(await exec('git remote get-url origin'));
const branch = await exec('git rev-parse --abbrev-ref HEAD');

const prs = await github.list_pull_requests({
  owner,
  repo,
  state: 'open',
  head: `${owner}:${branch}`
});

if (prs.length === 1) {
  // Exactly one PR - use it
  analyzePR(prs[0]);
} else if (prs.length > 1) {
  // Multiple PRs - ask user to select
  askUserToChoose(prs);
} else {
  // No PRs - prompt for PR number
  askForPRNumber();
}
```

## Rate Limiting

**GitHub API limits:**
- Authenticated: 5,000 requests/hour
- Search API: 30 requests/minute

**Best practices:**
1. **Cache PR data:** Use `cache_pr_data` setting
2. **Batch requests:** Fetch files in parallel but respect limits
3. **Check rate limit:** Monitor `X-RateLimit-Remaining` header
4. **Exponential backoff:** On 429 responses

**Check rate limit:**
```javascript
const rateLimit = await github.get_rate_limit();
if (rateLimit.remaining < 100) {
  console.warn('Approaching rate limit');
}
```

## Security Considerations

### Token Storage

**Never:**
- Commit tokens to version control
- Log tokens to console
- Include tokens in error messages

**Always:**
- Store in `.claude/arch-pr-analyzer.local.md`
- Add `*.local.md` to `.gitignore`
- Support environment variable fallback

### Private Repository Protection

**When analyzing private repos:**
- Verify token has access before fetching
- Don't log sensitive data
- Warn user about access requirements

### URL Validation

**Before parsing:**
- Validate URL format
- Sanitize user input
- Confirm domain is `github.com`

## Advanced Techniques

### Pagination Handling

For large PRs with many files:

```javascript
async function getAllPRFiles(owner, repo, prNumber) {
  let page = 1;
  let allFiles = [];
  const perPage = 100;

  while (true) {
    const files = await github.list_pr_files({
      owner,
      repo,
      pull_number: prNumber,
      per_page: perPage,
      page: page
    });

    allFiles = allFiles.concat(files);

    if (files.length < perPage) {
      break; // Last page
    }

    page++;
  }

  return allFiles;
}
```

### Diff Parsing

The `patch` field from `list_pr_files` contains unified diff format:

```diff
@@ -10,7 +10,8 @@ def login(credentials):
     if not user:
-        return None
+        raise AuthenticationError("Invalid credentials")
+
     session = create_session(user)
     return session
```

**Parse with caution:** Complex diffs may need specialized parsers

## Integration with Architectural Analysis

**Workflow:**

1. **PR Integration (this skill):**
   - Fetch PR metadata
   - Get changed files
   - Extract diffs

2. **Architectural Analysis:**
   - Analyze file changes
   - Detect patterns
   - Build dependency graphs
   - Generate diagrams

3. **Report Generation:**
   - Combine PR context + analysis
   - Format as markdown
   - Save to file

**Separation benefits:**
- Test PR fetching independently
- Reuse analysis logic for other sources (GitLab, Bitbucket)
- Mock PR data for testing

## Additional Resources

### Reference Files

For detailed patterns, see:

- **`references/mcp-server-tools.md`** - Complete GitHub MCP server tool reference with all parameters and return values
- **`references/error-handling.md`** - Comprehensive error handling patterns for all GitHub API errors

### Example Files

Working examples in `examples/`:

- **`cross-repo-analysis.md`** - Complete cross-repository analysis workflow
- **`auto-detection.md`** - Branch-based PR auto-detection example

## Best Practices

**DO:**
- Parse URLs carefully with proper validation
- Handle all error cases with helpful messages
- Respect rate limits
- Cache PR data when appropriate
- Verify token access before fetching
- Use cross-repository support for external dependencies

**DON'T:**
- Skip error handling
- Ignore rate limits
- Log sensitive data
- Hard-code repository assumptions
- Skip URL validation
- Forget to handle pagination

## Quick Reference

### MCP Tools Summary

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `list_pull_requests` | Find/list PRs | owner, repo, state, head (branch filter) |
| `get_pull_request` | PR details | owner, repo, pull_number |
| `list_pr_files` | Changed files | owner, repo, pull_number, per_page |
| `get_file_contents` | File at commit | owner, repo, path, ref (commit SHA) |
| `list_commits` | Commit history | owner, repo, sha (branch name) |
| `create_issue_comment` | Post comment | owner, repo, issue_number, body |

### Parsing Functions

**GitHub URL:**
```
https://github.com/{owner}/{repo}/pull/{number}
  → parseGitHubPRUrl(url) → {owner, repo, prNumber}
```

**Git Remote:**
```
https://github.com/{owner}/{repo}.git
git@github.com:{owner}/{repo}.git
  → parseGitRemote(url) → {owner, repo}
```

### Common Workflows

1. **Current repo PR:** Get repo → Fetch PR by number
2. **External repo PR:** Parse URL → Fetch PR from external repo
3. **Auto-detect:** Get repo + branch → List PRs → Select one
4. **Full analysis:** Get PR → List files → Fetch file contents → Analyze

Focus on robust error handling and clear user feedback for smooth cross-repository operation.
