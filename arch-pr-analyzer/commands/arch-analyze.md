---
name: arch-analyze
description: Analyze architectural changes in a pull request at multiple granularity levels with visual diagrams
argument-hint: "[granularity] [--pr <number|url>]"
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Task
  - AskUserQuestion
---

# Architecture PR Analyzer Command

Perform comprehensive architectural analysis of pull request changes with multi-granularity reports and Mermaid diagrams.

## Purpose

This command triggers the architecture-analyzer agent to:
1. Detect or accept PR context (current repo or cross-repository)
2. Fetch PR data via GitHub MCP server
3. Analyze architectural changes at specified granularity
4. Generate visual diagrams showing before/after architecture
5. Produce git diff-style architectural change report
6. Save analysis to `.claude/analyses/` directory

## Argument Parsing

### Granularity Parameter

**Format:** First positional argument (optional)

**Options:**
1. **Exact keywords** (preferred for speed):
   - `high` - System/domain level components
   - `medium` - Module/package/service level (default)
   - `low` - Class/function/endpoint level
   - `<custom>` - User-defined granularity (e.g., `microservice`, `data-model`)

2. **Natural language** (fallback):
   - "show me endpoint-level changes" → infers `low`
   - "system-level impact" → infers `high`
   - "what modules changed" → infers `medium`

**Parsing logic:**
- Try exact match first against: high, medium, low, custom names
- If no match, use small LLM inference to map to standard level
- Default to `medium` if omitted or cannot infer

### PR Parameter

**Format:** `--pr <value>` (optional)

**Accepted values:**
1. **PR number**: `--pr 123` (uses current repository)
2. **GitHub URL**: `--pr https://github.com/owner/repo/pull/123` (cross-repository)
3. **Auto-detect**: Omit parameter to detect from current branch

**Auto-detection logic:**
1. Get current branch: `git rev-parse --abbrev-ref HEAD`
2. Query GitHub API for PRs with this head branch
3. If exactly one PR found → use it automatically
4. If multiple PRs found → use AskUserQuestion to let user select
5. If no PRs found → use AskUserQuestion to prompt for PR number/URL

## Command Execution Flow

### Step 1: Parse Arguments

Extract granularity and PR parameters from user input.

**Example inputs:**
- `/arch-analyze high`
- `/arch-analyze medium --pr 123`
- `/arch-analyze --pr https://github.com/facebook/react/pull/12345`
- `/arch-analyze "show me what changed at the endpoint level"`
- `/arch-analyze` (no args - auto-detect both)

**Granularity resolution:**
```
Input: "high" → granularity = "high"
Input: "show endpoint changes" → use inference → granularity = "low"
Input: "" (empty) → granularity = "medium" (default)
Input: "microservice" → check custom granularities → granularity = "microservice"
```

**PR resolution:**
```
Input: "--pr 123" → prNumber = 123, use current repo
Input: "--pr https://github.com/facebook/react/pull/12345" → owner="facebook", repo="react", prNumber=12345
Input: (omitted) → auto-detect from current branch
```

### Step 2: Load Settings

Read configuration from `.claude/arch-pr-analyzer.md` if it exists:
- `default_granularity` - Override default if not specified
- `default_repository` - Use if PR not specified and auto-detect fails
- `output_verbosity` - Controls report detail level
- `include_diagrams` - Whether to generate Mermaid diagrams
- Other preferences (see settings template)

### Step 3: Verify GitHub Token

**Token loading order:**
1. Check `.claude/arch-pr-analyzer.local.md` for `github_token:` field
2. Check environment variable `GITHUB_TOKEN`
3. If neither exists, provide setup instructions and exit

**Special argument:** `--verify-token`
If user runs `/arch-analyze --verify-token`, test token and show:
- Token validity
- Scopes available
- Rate limit status
- Sample accessible repositories

### Step 4: Determine Repository Context

**If PR URL provided:**
- Parse URL to extract owner, repo, prNumber
- Use those values directly

**If PR number provided:**
- Get current repo from git: `git remote get-url origin`
- Parse to extract owner and repo
- Use provided PR number

**If auto-detecting:**
- Get current repo from git
- Get current branch: `git rev-parse --abbrev-ref HEAD`
- Use GitHub MCP to search for PRs: `list_pull_requests` with head filter
- Handle results:
  - 0 PRs: Ask user for PR number/URL
  - 1 PR: Use automatically, inform user
  - 2+ PRs: Use AskUserQuestion to let user select

### Step 5: Launch Architecture Analyzer Agent

Invoke the `architecture-analyzer` agent with Task tool:

```
Task(
  subagent_type: "general-purpose",  // or specific agent type if available
  description: "Analyze PR architecture",
  prompt: "Analyze architectural changes in PR #{prNumber} in {owner}/{repo} at {granularity} granularity.

  Context:
  - Repository: {owner}/{repo}
  - PR Number: {prNumber}
  - Granularity: {granularity}
  - Settings: {settings}

  Your task:
  1. Use GitHub MCP server to fetch PR details, files, and diffs
  2. Apply architectural-analysis skill techniques
  3. Apply pr-integration skill patterns
  4. Generate before/after architecture diagrams
  5. Create comprehensive analysis report
  6. Save to .claude/analyses/pr-{owner}-{repo}-{prNumber}-{timestamp}.md
  7. Display executive summary in conversation"
)
```

### Step 6: Display Results

After agent completes:
1. Show executive summary in conversation
2. Show high-level architectural changes
3. Indicate where full report was saved
4. Provide quick stats (files changed, components affected, risk level)

**Example output:**
```
✓ Architectural Analysis Complete

PR #123: Add OAuth2 Authentication
Repository: myorg/myrepo
Granularity: medium

Executive Summary:
Authentication system expanded to support OAuth2. Changes affect Auth module,
API Gateway, and introduce new dependency on Payment Service for subscription
validation.

Impact: Medium scope, High risk (breaking changes to auth API)
Components affected: 3 (Auth, API, Payments)
Files changed: 16 files

Breaking changes detected:
- Removed endpoint: GET /auth/legacy/user
- Modified auth flow (session handling changed)

Full analysis saved to:
.claude/analyses/pr-myorg-myrepo-123-2026-01-19-143022.md
```

## Error Handling

### Invalid Granularity

If granularity cannot be resolved (no exact match, inference fails):
```
Could not determine granularity level from input: "{input}"

Valid options:
- Exact: high, medium, low
- Custom: {list custom levels from settings}
- Natural language: "show endpoint-level changes", "system components", etc.

Example: /arch-analyze medium --pr 123
```

### PR Not Found

If PR number/URL is invalid:
```
Could not find PR #{number} in {owner}/{repo}.

Please verify:
1. PR number is correct
2. Repository is correct: {owner}/{repo}
3. Your GitHub token has access to this repository

To analyze a different repository, use full URL:
/arch-analyze medium --pr https://github.com/owner/repo/pull/123
```

### No GitHub Token

If token is missing:
```
GitHub token not found.

To analyze PRs, configure your GitHub Personal Access Token:

Method 1 (Recommended): Settings file
1. Create: .claude/arch-pr-analyzer.local.md
2. Add line: github_token: ghp_your_token_here

Method 2: Environment variable
export GITHUB_TOKEN="ghp_your_token_here"

To create a token:
1. Go to: https://github.com/settings/tokens
2. Generate new token (classic)
3. Select scope: 'repo' (for private repos) or 'public_repo' (public only)
4. Copy token and configure above

Verify token works: /arch-analyze --verify-token
```

### Repository Access Denied

If token lacks access to repository:
```
Access denied to {owner}/{repo}.

Your token needs:
- Scope: 'repo' (for private repositories) or 'public_repo' (public)
- Repository access: Be a collaborator or organization member

For private repositories:
1. Ensure token has 'repo' scope (not just 'public_repo')
2. Verify you have access to {owner}/{repo}

For organization repositories:
1. Check organization settings allow personal access tokens
2. Verify you're a member with appropriate permissions
```

### Rate Limit Exceeded

If GitHub API rate limit hit:
```
GitHub API rate limit exceeded.

Current status:
- Limit: 5,000 requests/hour
- Remaining: 0
- Resets at: {reset_time}

Options:
1. Wait until rate limit resets
2. Use a different token with higher limits
3. Enable caching in settings: cache_pr_data: true
```

### PR Too Large

If PR exceeds max_files_to_analyze limit:
```
PR #{number} has {count} files changed, exceeding limit of {max}.

Large PRs may timeout or consume excessive resources.

Options:
1. Increase limit in settings: max_files_to_analyze: {higher_value}
2. Analyze a subset: Focus on specific directories
3. Use higher granularity: /arch-analyze high --pr {number}

To proceed anyway: /arch-analyze {granularity} --pr {number} --force
```

## Special Arguments

### --verify-token

Test GitHub token configuration:
```
/arch-analyze --verify-token
```

Checks:
- Token is configured
- Token is valid
- Shows available scopes
- Shows rate limit status
- Lists sample accessible repositories

### --force

Skip safety limits (use with caution):
```
/arch-analyze medium --pr 123 --force
```

Bypasses:
- `max_files_to_analyze` limit
- Confirmation prompts

### --output <path>

Override output location:
```
/arch-analyze high --pr 123 --output ./my-analysis.md
```

Default: `.claude/analyses/pr-{owner}-{repo}-{number}-{timestamp}.md`

### --help

Display usage information:
```
/arch-analyze --help
```

Shows:
- Command syntax
- Granularity options
- PR parameter formats
- Examples
- Configuration guidance

## Examples

### Example 1: Analyze current PR with defaults
```
/arch-analyze
```
- Uses default granularity (medium)
- Auto-detects PR from current branch
- Saves to default location

### Example 2: High-level analysis with explicit PR
```
/arch-analyze high --pr 123
```
- System component level
- PR #123 in current repository

### Example 3: Detailed endpoint analysis
```
/arch-analyze low --pr 456
```
- Class/function/endpoint level
- PR #456 in current repository

### Example 4: Cross-repository analysis
```
/arch-analyze medium --pr https://github.com/facebook/react/pull/12345
```
- Analyzes React PR (external repository)
- Medium granularity

### Example 5: Natural language granularity
```
/arch-analyze "show me what microservices changed" --pr 789
```
- Infers custom 'microservice' granularity
- PR #789 in current repository

### Example 6: Custom granularity
```
/arch-analyze data-model --pr 321
```
- Uses custom 'data-model' granularity
- Focuses on database schema changes

## Integration with Skills

This command works in conjunction with:

1. **architectural-analysis skill**: Provides techniques for analyzing code structure, dependencies, APIs, database schemas, data flows
2. **pr-integration skill**: Provides patterns for GitHub PR API usage, URL parsing, error handling

The architecture-analyzer agent automatically loads these skills when triggered.

## Notes for Implementation

When implementing this command:

1. **Parse arguments carefully**: Support both exact keywords and natural language
2. **Handle cross-repository**: Parse GitHub URLs correctly
3. **Provide helpful errors**: Guide users to fix configuration issues
4. **Load settings**: Check for `.claude/arch-pr-analyzer.md` configuration
5. **Verify access**: Test GitHub token before attempting analysis
6. **Auto-detect smartly**: Make the common case (current repo, current branch) seamless
7. **Display progress**: Keep user informed during long-running analysis
8. **Save output**: Always save full report to file
9. **Summarize in chat**: Show key findings in conversation

Remember: This command's job is to orchestrate the analysis by:
- Parsing user input
- Loading configuration
- Verifying access
- Determining PR context
- Launching the architecture-analyzer agent
- Displaying results

The actual analysis work is done by the agent using the skills.
