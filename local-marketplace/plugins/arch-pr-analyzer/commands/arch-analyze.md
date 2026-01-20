---
name: arch-analyze
description: Analyze architecture of current directory or pull request at multiple granularity levels with visual diagrams
argument-hint: "[granularity] [--pr <number|url>] [--snapshot]"
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Task
  - AskUserQuestion
---

# Architecture Analyzer Command

Perform comprehensive architectural analysis with multi-granularity reports and Mermaid diagrams. Supports two modes:
- **Directory Mode (Default):** Analyze current directory state with snapshot diagrams
- **PR Mode:** Analyze pull request changes with before/after comparison

## Purpose

This command triggers the architecture-analyzer agent to:

**Directory Mode:**
1. Verify current directory is a git repository
2. Enumerate all tracked files (via git-integration skill)
3. Read file contents including uncommitted changes
4. Analyze current architecture at specified granularity
5. Generate snapshot diagram showing current structure
6. Save analysis to `.claude/analyses/` directory

**PR Mode:**
1. Detect or accept PR context (current repo or cross-repository)
2. Fetch PR data via GitHub MCP server (via pr-integration skill)
3. Analyze architectural changes at specified granularity
4. Generate visual diagrams showing before/after architecture
5. Produce git diff-style architectural change report
6. Save analysis to `.claude/analyses/` directory

## Analysis Mode Detection

### Directory Mode (DEFAULT)
Triggered when `--pr` flag is **NOT** present.

**Behavior:**
- Analyzes current working directory state
- Snapshot analysis (no before/after comparison)
- Includes all tracked files in repository
- Includes uncommitted and untracked changes by default
- Uses local git commands via git-integration skill

**When to use:** Understanding current architecture state, documentation, baseline snapshots

### PR Mode (OPTIONAL)
Triggered when `--pr` flag **IS** present.

**Behavior:**
- Analyzes GitHub pull request changes
- Comparison analysis (base commit vs head commit)
- Shows before/after architectural changes
- Uses GitHub MCP server via pr-integration skill

**When to use:** Code review, impact assessment, merge decisions

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

### PR Parameter (OPTIONAL)

**Format:** `--pr [<value>]`

**When omitted:** Directory mode (analyze current state)

**When present:**
1. **Auto-detect:** `--pr` with no value → detect PR from current branch
2. **PR number**: `--pr 123` → analyze PR in current repo
3. **GitHub URL**: `--pr https://github.com/owner/repo/pull/123` → cross-repo analysis

**Auto-detection logic (when `--pr` has no value):**
1. Get current branch: `git rev-parse --abbrev-ref HEAD`
2. Query GitHub API for PRs with this head branch
3. If exactly one PR found → use it automatically
4. If multiple PRs found → use AskUserQuestion to let user select
5. If no PRs found → use AskUserQuestion to prompt for PR number/URL

### --snapshot Flag (OPTIONAL)

**Format:** `--snapshot`

**Purpose:** Explicitly indicate snapshot-only analysis (no comparison)

**Note:** This is the default behavior in directory mode, so the flag is optional for clarity.

**Example:**
```bash
/arch-analyze --snapshot       # Same as /arch-analyze
/arch-analyze high --snapshot  # High granularity snapshot
```

## Command Execution Flow

### Step 1: Parse Arguments and Detect Mode

Extract granularity and mode from user input.

**Example inputs:**

**Directory Mode (no --pr flag):**
- `/arch-analyze` → directory mode, medium granularity
- `/arch-analyze high` → directory mode, high granularity
- `/arch-analyze --snapshot` → directory mode (explicit), medium granularity
- `/arch-analyze low --snapshot` → directory mode, low granularity

**PR Mode (with --pr flag):**
- `/arch-analyze --pr` → PR mode, auto-detect PR, medium granularity
- `/arch-analyze medium --pr 123` → PR mode, PR #123, medium granularity
- `/arch-analyze --pr https://github.com/facebook/react/pull/12345` → PR mode, cross-repo
- `/arch-analyze high --pr 456` → PR mode, PR #456, high granularity

**Granularity resolution:**
```
Input: "high" → granularity = "high"
Input: "show endpoint changes" → use inference → granularity = "low"
Input: "" (empty) → granularity = "medium" (default)
Input: "microservice" → check custom granularities → granularity = "microservice"
```

**Mode detection:**
```
Parse arguments:
  ├─ Granularity: First positional arg (default: medium)
  └─ Mode detection:
      ├─ If --pr flag present → PR Mode
      └─ If --pr flag absent → Directory Mode (DEFAULT)
```

**PR resolution (only in PR mode):**
```
Input: "--pr" → auto-detect from current branch
Input: "--pr 123" → prNumber = 123, use current repo
Input: "--pr https://github.com/facebook/react/pull/12345" → owner="facebook", repo="react", prNumber=12345
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

### Step 4: Mode-Specific Preparation

**For Directory Mode:**

1. Verify current directory is a git repository:
   ```bash
   git rev-parse --is-inside-work-tree
   ```
   If false, show error and exit (see Error Handling section)

2. Get repository metadata:
   ```bash
   REPO_ROOT=$(git rev-parse --show-toplevel)
   REPO_NAME=$(basename -s .git $(git remote get-url origin 2>/dev/null) || basename "$REPO_ROOT")
   CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
   ```

3. Detect uncommitted/untracked files:
   ```bash
   MODIFIED_COUNT=$(git status --porcelain | grep -c "^ M\|^M \|^MM" || echo "0")
   UNTRACKED_COUNT=$(git ls-files --others --exclude-standard | wc -l | tr -d ' ')
   ```

4. Set context for analyzer:
   ```json
   {
     "mode": "directory",
     "repoPath": "/path/to/repo",
     "repoName": "code-dojo",
     "currentBranch": "feature/new-feature",
     "granularity": "medium",
     "includeUncommitted": true,
     "snapshot": true
   }
   ```

**For PR Mode:**

1. **If PR URL provided:**
   - Parse URL to extract owner, repo, prNumber
   - Use those values directly

2. **If PR number provided:**
   - Get current repo from git: `git remote get-url origin`
   - Parse to extract owner and repo
   - Use provided PR number

3. **If auto-detecting:**
   - Get current repo from git
   - Get current branch: `git rev-parse --abbrev-ref HEAD`
   - Use GitHub MCP to search for PRs: `list_pull_requests` with head filter
   - Handle results:
     - 0 PRs: Ask user for PR number/URL
     - 1 PR: Use automatically, inform user
     - 2+ PRs: Use AskUserQuestion to let user select

4. Set context for analyzer:
   ```json
   {
     "mode": "pr",
     "owner": "myorg",
     "repo": "myrepo",
     "prNumber": 123,
     "granularity": "medium"
   }
   ```

### Step 5: Launch Architecture Analyzer Agent

Invoke the `architecture-analyzer` agent with Task tool.

**Directory Mode Prompt:**

```
Task(
  subagent_type: "general-purpose",
  description: "Analyze directory architecture",
  prompt: "Analyze architecture of current directory at {granularity} granularity.

  Mode: Directory Analysis (Snapshot)
  Repository: {repoPath}
  Repository Name: {repoName}
  Current Branch: {currentBranch}
  Granularity: {granularity}
  Include Uncommitted: {includeUncommitted}

  Your task:
  1. Use git-integration skill to enumerate all tracked files
  2. Read current file contents (includes uncommitted changes)
  3. Apply architectural-analysis skill techniques
  4. Generate architecture snapshot diagram (current state only)
  5. Create analysis report showing current architecture
  6. Save to .claude/analyses/snapshot-{repoName}-{branch}-{timestamp}.md
  7. Display architecture summary in conversation"
)
```

**PR Mode Prompt:**

```
Task(
  subagent_type: "general-purpose",
  description: "Analyze PR architecture",
  prompt: "Analyze architectural changes in PR #{prNumber} in {owner}/{repo} at {granularity} granularity.

  Mode: Pull Request Analysis
  Repository: {owner}/{repo}
  PR Number: {prNumber}
  Granularity: {granularity}
  Settings: {settings}

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

After agent completes, display mode-specific output.

**Directory Mode Output:**
```
✓ Architecture Snapshot Complete

Repository: {repoName}
Branch: {currentBranch}
Granularity: {granularity}

Architecture Summary:
[2-3 sentence overview of current architecture]

Components identified: {count}
Files analyzed: {count}
Uncommitted changes: {included/excluded}

Full snapshot saved to:
.claude/analyses/snapshot-{repoName}-{branch}-{timestamp}.md
```

**Example:**
```
✓ Architecture Snapshot Complete

Repository: code-dojo
Branch: feature/pr-submission
Granularity: medium

Architecture Summary:
Flask-based code review platform with modular architecture. Three main
layers: presentation (templates), business logic (routes/services), and
data (models). Integrates with GitHub API for PR analysis.

Components identified: 5
Files analyzed: 47
Uncommitted changes: Included (9 modified, 3 untracked)

Full snapshot saved to:
.claude/analyses/snapshot-code-dojo-feature-pr-submission-2026-01-19-143022.md
```

**PR Mode Output:**
```
✓ Architectural Analysis Complete

PR #{number}: {title}
Repository: {owner}/{repo}
Granularity: {granularity}

Executive Summary:
[2-3 paragraph overview of architectural changes]

Impact: {scope}, {risk}
Components affected: {count}
Files changed: {count}

Breaking changes detected:
- [List of breaking changes]

Full analysis saved to:
.claude/analyses/pr-{owner}-{repo}-{number}-{timestamp}.md
```

**Example:**
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

### Directory Mode Errors

#### Not a Git Repository

**When:** Running directory mode in a non-git directory

**Error message:**
```
Error: Not a git repository

Current directory is not a git repository: {path}

To analyze a directory, navigate to a git repository:
  cd /path/to/your/repo

Or to analyze a GitHub PR instead:
  /arch-analyze --pr <number|url>
```

#### Git Command Failures

**When:** Git operations fail (permissions, corrupted repo, etc.)

**Error message:**
```
Error: Git operation failed

Failed to execute: {git command}
Error: {error message}

Ensure:
1. You have git installed
2. Current directory is a valid git repository
3. You have read permissions for the repository
```

#### No Files Found

**When:** Repository has no tracked files

**Error message:**
```
Warning: No files to analyze

No tracked files found in repository.

This might occur if:
1. Repository is empty
2. All files are untracked (run: git add .)
3. Current directory is not the repository root
```

### General Errors

#### Invalid Granularity

If granularity cannot be resolved (no exact match, inference fails):
```
Could not determine granularity level from input: "{input}"

Valid options:
- Exact: high, medium, low
- Custom: {list custom levels from settings}
- Natural language: "show endpoint-level changes", "system components", etc.

Example: /arch-analyze medium --pr 123
```

### PR Mode Errors

#### PR Not Found

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

### Directory Mode Examples

#### Example 1: Analyze current directory (default)
```bash
/arch-analyze
```
- Directory mode (default)
- Medium granularity
- Includes uncommitted changes
- Saves snapshot to `.claude/analyses/`

#### Example 2: High-level system components
```bash
/arch-analyze high
```
- Directory mode
- High granularity (system/domain level)
- Shows major architectural components

#### Example 3: Detailed class/function level
```bash
/arch-analyze low
```
- Directory mode
- Low granularity (detailed)
- Shows classes, functions, endpoints

#### Example 4: Explicit snapshot flag
```bash
/arch-analyze --snapshot
```
- Directory mode (explicit)
- Medium granularity
- Same as Example 1 but more explicit

### PR Mode Examples

#### Example 5: Auto-detect PR from current branch
```bash
/arch-analyze --pr
```
- PR mode
- Auto-detects PR from current branch
- Medium granularity

#### Example 6: Analyze specific PR in current repo
```bash
/arch-analyze high --pr 123
```
- PR mode
- PR #123 in current repository
- High granularity (system component level)

#### Example 7: Detailed PR analysis
```bash
/arch-analyze low --pr 456
```
- PR mode
- PR #456 in current repository
- Low granularity (class/function/endpoint level)

#### Example 8: Cross-repository PR analysis
```bash
/arch-analyze medium --pr https://github.com/facebook/react/pull/12345
```
- PR mode
- Analyzes external React PR
- Medium granularity

#### Example 9: Natural language granularity with PR
```bash
/arch-analyze "show me what microservices changed" --pr 789
```
- PR mode
- Infers custom 'microservice' granularity
- PR #789 in current repository

#### Example 10: Custom granularity for database changes
```bash
/arch-analyze data-model --pr 321
```
- PR mode
- Uses custom 'data-model' granularity
- Focuses on database schema changes in PR #321

## Integration with Skills

This command works in conjunction with:

1. **architectural-analysis skill**: Provides techniques for analyzing code structure, dependencies, APIs, database schemas, data flows (used in both modes)
2. **git-integration skill**: Provides local git repository operations for directory analysis (used in directory mode)
3. **pr-integration skill**: Provides patterns for GitHub PR API usage, URL parsing, error handling (used in PR mode)

The architecture-analyzer agent automatically loads the appropriate skills based on the analysis mode.

## Notes for Implementation

When implementing this command:

1. **Detect mode first**: Check for `--pr` flag to determine directory vs PR mode
2. **Parse arguments carefully**: Support both exact keywords and natural language
3. **Directory mode is default**: When `--pr` is absent, use directory analysis
4. **Verify git repo early**: In directory mode, fail fast if not a git repository
5. **Handle cross-repository**: In PR mode, parse GitHub URLs correctly
6. **Provide helpful errors**: Guide users to fix configuration issues
7. **Load settings**: Check for `.claude/arch-pr-analyzer.md` configuration
8. **Verify access**: In PR mode, test GitHub token before attempting analysis
9. **Auto-detect smartly**: Make the common case seamless (directory by default, PR auto-detect when needed)
10. **Display progress**: Keep user informed during long-running analysis
11. **Save output**: Always save full report to file (different naming for each mode)
12. **Summarize in chat**: Show key findings in conversation

Remember: This command's job is to orchestrate the analysis by:
- Parsing user input and detecting mode
- Loading configuration
- Verifying access (git repo for directory mode, GitHub token for PR mode)
- Determining context (directory metadata or PR context)
- Launching the architecture-analyzer agent with appropriate prompt
- Displaying mode-specific results

The actual analysis work is done by the agent using the appropriate skills:
- Directory mode: git-integration + architectural-analysis
- PR mode: pr-integration + architectural-analysis
