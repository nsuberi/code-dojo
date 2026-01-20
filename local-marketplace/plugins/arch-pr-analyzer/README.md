# Architecture Analyzer

A Claude Code plugin for comprehensive architectural analysis of codebases. Analyze current directory state or pull request changes with multi-granularity reports and visual diagrams.

## Features

- **Directory Analysis (Default)**: Analyze current codebase architecture with snapshot diagrams
- **Pull Request Analysis**: Compare architectural changes between base and head commits
- **Multi-granularity analysis**: High-level (system components), medium (modules/services), low (classes/functions/endpoints)
- **Uncommitted Changes**: Includes work-in-progress for real-time feedback
- **Rich visualizations**: Mermaid diagrams showing architecture (snapshot or before/after)
- **Cross-repository support**: Analyze PRs in any GitHub repository via URL
- **Comprehensive detection**: Tracks dependencies, API endpoints, database schemas, data flows
- **Custom granularities**: Define your own analysis levels (e.g., microservice-level, data-model-focused)
- **GitHub integration**: Direct PR API integration via MCP server (PR mode only)

## Installation

### Prerequisites

**For Directory Analysis (Default Mode):**
- Git installed and accessible
- A git repository to analyze

**For PR Analysis Mode:**
- Node.js (for GitHub MCP server via `npx`)
- GitHub Personal Access Token

### Steps

1. Clone or download this plugin to your Claude plugins directory
2. (Optional) Configure GitHub token for PR mode (see Configuration section)
3. Restart Claude Code

## Configuration

### Directory Mode (No Configuration Required)

Directory analysis works out of the box - just navigate to a git repository and run `/arch-analyze`.

### PR Mode: GitHub Token Setup

**Only needed for PR analysis.** Create a GitHub Personal Access Token:

1. Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Give it a descriptive name: "Claude Architecture Analyzer"
4. Select scopes:
   - ✅ **repo** (for private repositories) OR
   - ✅ **public_repo** (for public repositories only)
5. Click "Generate token" and copy it

### Configure Token (Choose One Method)

**Method A: Settings File (Recommended)**

Create `.claude/arch-pr-analyzer.local.md` in your project:

```markdown
# Architecture PR Analyzer - Local Settings

## GitHub Configuration

github_token: ghp_your_personal_access_token_here
```

**Method B: Environment Variable**

Add to your shell profile (`~/.bashrc`, `~/.zshrc`):

```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

### Plugin Settings (Optional)

Copy the template settings file to customize behavior:

```bash
cp .claude/arch-pr-analyzer.md.example .claude/arch-pr-analyzer.md
```

Edit `.claude/arch-pr-analyzer.md` to configure:
- Default granularity level
- Output preferences
- Architecture documentation paths
- Custom granularity definitions

## Usage

### Directory Analysis (Default)

Analyze current directory architecture - **no PR required**:

```bash
# Basic analysis (medium granularity)
/arch-analyze

# System-level components
/arch-analyze high

# Detailed classes/functions
/arch-analyze low

# Explicit snapshot
/arch-analyze --snapshot
```

**What it does:**
- Analyzes all tracked files in your repository
- Includes uncommitted and untracked changes
- Generates architecture snapshot diagram
- Saves report to `.claude/analyses/snapshot-{repo}-{branch}-{timestamp}.md`

### Pull Request Analysis

Analyze PR changes with `--pr` flag:

```bash
# Auto-detect PR from current branch
/arch-analyze --pr

# Analyze specific PR in current repo
/arch-analyze medium --pr 123

# Detailed PR analysis
/arch-analyze low --pr 456
```

### Cross-Repository PR Analysis

Analyze PRs in any GitHub repository using a URL:

```bash
/arch-analyze medium --pr https://github.com/facebook/react/pull/12345
```

### Natural Language

You can also use natural language:

```bash
# Directory mode
/arch-analyze "show me the current architecture"

# PR mode
/arch-analyze "show me endpoint-level changes" --pr 123
```

### Granularity Levels

**Built-in levels:**
- `high`: System/domain components (Auth System, API Gateway, Data Layer)
- `medium`: Modules/packages/services (auth.users, api.endpoints.orders)
- `low`: Classes/functions/endpoints (UserService.authenticate(), POST /api/login)

**Custom levels** (if configured):
- `microservice`: Microservice-level analysis
- `data-model`: Database schema and data model focus
- Your own custom definitions

### Auto-Detection (PR Mode)

When using `--pr` without a value, the plugin will:
1. Detect PRs associated with your current branch
2. Auto-select if only one PR found
3. Prompt you to choose if multiple PRs exist

## Analysis Modes

### Directory Mode (Default)

**When:** No `--pr` flag specified
**Analyzes:** Current working directory state
**Output:** Architecture snapshot (current state)
**Includes:** All tracked files plus uncommitted changes
**Use for:** Understanding existing architecture, documentation, baseline snapshots

### PR Mode

**When:** `--pr` flag specified
**Analyzes:** GitHub pull request changes
**Output:** Before/after comparison
**Includes:** Only files changed in the PR
**Use for:** Code review, impact assessment, merge decisions

## Output

Analysis reports are saved to `.claude/analyses/` with mode-specific filenames:

**Directory mode:**
```
.claude/analyses/snapshot-{repo}-{branch}-{timestamp}.md
```

**PR mode:**
```
.claude/analyses/pr-{owner}-{repo}-{number}-{timestamp}.md
```

### Directory Mode Reports Include:
- Executive summary
- Architecture snapshot diagram (current state)
- Component catalog
- API surface analysis
- Database schema
- Dependencies
- Data flows
- Uncommitted changes list

### PR Mode Reports Include:
- Executive summary
- Architecture diagrams (before/after)
- Impact assessment
- Changes by system component
- New architectural patterns
- Breaking changes
- Dependencies and ripple effects
- Detailed file-by-file breakdown

## Examples

### Example 1: Analyze Current Directory

```bash
# Basic directory analysis
cd /path/to/your/project
/arch-analyze

# Get high-level system components
/arch-analyze high

# Detailed class/function analysis
/arch-analyze low
```

**Output:**
- Snapshot of current architecture
- All tracked files analyzed
- Uncommitted changes included
- Report saved with current branch name

### Example 2: Analyze PR Before Merging

```bash
# Switch to your feature branch
git checkout feature/add-oauth

# Auto-detect and analyze PR
/arch-analyze --pr

# Or specify PR number
/arch-analyze medium --pr 123
```

**Output:**
- Before/after architecture comparison
- Impact assessment for merge decision
- Breaking changes highlighted

### Example 3: Compare Granularities

```bash
# High-level overview of directory
/arch-analyze high

# Detailed endpoint-level PR analysis
/arch-analyze low --pr 123
```

### Example 4: External Repository PR

```bash
# Analyze a dependency's PR before upgrading
/arch-analyze medium --pr https://github.com/lodash/lodash/pull/5432
```

## Troubleshooting

### Directory Mode Issues

#### "Not a git repository"

**Error:** Current directory is not a git repository

**Solution:**
```bash
# Initialize git repo first
git init
git add .
git commit -m "Initial commit"

# Then analyze
/arch-analyze
```

#### "No files found"

**Error:** No tracked files found in repository

**Possible causes:**
1. Repository is empty
2. All files are untracked (run: `git add .`)
3. Current directory is not the repository root

#### "Git command failed"

**Error:** Failed to execute git command

**Solutions:**
- Ensure git is installed: `git --version`
- Check file permissions
- Verify repository is not corrupted

### PR Mode Issues

#### "GitHub token not found"

**Only affects PR mode.** Ensure your token is configured in either:
- `.claude/arch-pr-analyzer.local.md` (preferred)
- Environment variable `GITHUB_TOKEN`

Verify with: `/arch-analyze --verify-token`

#### "Could not access PR"

Possible causes:
1. Invalid PR number or URL
2. Repository is private and token lacks access
3. Token needs `repo` scope for private repos

#### "MCP server not starting"

Ensure Node.js is installed:
```bash
node --version
npx --version
```

## Advanced Features

### Custom Granularity Definitions

Define your own analysis perspectives in `.claude/arch-pr-analyzer.md`:

```markdown
## Custom Granularity: microservice

custom_granularities:
  - name: microservice
    description: "Microservice-level analysis"
    config_file: .claude/granularity-microservice.md
```

See `examples/granularity-microservice.md` for template.

### Architecture Context

Help the analyzer understand your architecture by creating:
- `docs/architecture.md` - Your architecture documentation
- `.claude/architecture-context.md` - Custom architecture notes
- `.claude/components.yaml` - Component definitions

The analyzer will read these files for context.

## Contributing

Feedback and contributions welcome! This plugin is designed to be extensible with custom granularities and analysis techniques.

## License

MIT

## Version History

- **1.0.0** (2026-01-19): Directory analysis support
  - **NEW:** Directory mode (default) - analyze current codebase without PRs
  - **NEW:** Includes uncommitted and untracked changes
  - **NEW:** git-integration skill for local repository operations
  - PR mode now optional via `--pr` flag
  - Multi-granularity analysis (high, medium, low)
  - Cross-repository PR support
  - GitHub MCP integration
  - Custom granularity definitions
  - Mermaid diagram generation
