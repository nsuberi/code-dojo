# Architecture PR Analyzer

A Claude Code plugin for comprehensive architectural analysis of pull requests. Visualizes codebase architecture changes across multiple granularity levels with Mermaid diagrams and git diff-style reports.

## Features

- **Multi-granularity analysis**: High-level (system components), medium (modules/services), low (classes/functions/endpoints)
- **Cross-repository support**: Analyze PRs in any GitHub repository via URL
- **Rich visualizations**: Mermaid diagrams showing before/after architecture states
- **Git diff-style reports**: Architectural changes presented in familiar diff format
- **Comprehensive detection**: Tracks dependencies, API endpoints, database schemas, data flows
- **Custom granularities**: Define your own analysis levels (e.g., microservice-level, data-model-focused)
- **GitHub integration**: Direct PR API integration via MCP server

## Installation

### Prerequisites

1. **Node.js**: Required for GitHub MCP server (`npx`)
2. **GitHub Personal Access Token**: For accessing PR data

### Steps

1. Clone or download this plugin to your Claude plugins directory
2. Configure your GitHub token (see Configuration section)
3. Restart Claude Code

## Configuration

### GitHub Token Setup

Create a GitHub Personal Access Token:

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

### Basic Usage

Analyze a PR in your current repository:

```
/arch-analyze high
/arch-analyze medium --pr 123
/arch-analyze low
```

### Cross-Repository Analysis

Analyze PRs in any GitHub repository using a URL:

```
/arch-analyze medium --pr https://github.com/facebook/react/pull/12345
```

### Natural Language

You can also use natural language:

```
/arch-analyze "show me endpoint-level changes"
/arch-analyze "what changed at the system level?"
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

### Auto-Detection

If you don't specify a PR number, the plugin will:
1. Detect PRs associated with your current branch
2. Auto-select if only one PR found
3. Prompt you to choose if multiple PRs exist

## Output

Analysis reports are saved to `.claude/analyses/` with timestamped filenames:

```
.claude/analyses/pr-facebook-react-12345-2026-01-19-143022.md
```

Each report includes:
- Executive summary
- Architecture diagrams (before/after)
- Impact assessment
- Changes by system component
- New architectural patterns
- Dependencies and ripple effects
- Detailed file-by-file breakdown

## Examples

### Example 1: Analyze Current PR

```bash
# Switch to your feature branch
git checkout feature/add-oauth

# Analyze at medium granularity
/arch-analyze medium
```

### Example 2: Compare Granularities

```bash
# High-level overview
/arch-analyze high --pr 123

# Detailed endpoint-level analysis
/arch-analyze low --pr 123
```

### Example 3: External Repository

```bash
# Analyze a dependency's PR before upgrading
/arch-analyze medium --pr https://github.com/lodash/lodash/pull/5432
```

## Troubleshooting

### "GitHub token not found"

Ensure your token is configured in either:
- `.claude/arch-pr-analyzer.local.md` (preferred)
- Environment variable `GITHUB_TOKEN`

Verify with: `/arch-analyze --verify-token`

### "Could not access PR"

Possible causes:
1. Invalid PR number or URL
2. Repository is private and token lacks access
3. Token needs `repo` scope for private repos

### "MCP server not starting"

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

- **0.1.0** (2026-01-19): Initial release
  - Multi-granularity analysis (high, medium, low)
  - Cross-repository PR support
  - GitHub MCP integration
  - Custom granularity definitions
  - Mermaid diagram generation
