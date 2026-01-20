# Code Dojo Local Plugin Marketplace

This directory contains local Claude Code plugins for the Code Dojo project.

## Available Plugins

### arch-pr-analyzer
Architectural analysis plugin for repositories - analyze current directory state or pull requests with multi-granularity reports and diagrams.

**Features:**
- Directory analysis (default): Snapshot of current architecture
- PR analysis: Compare changes before/after
- Visual Mermaid diagrams
- Multi-granularity (system/module/detailed)
- Includes uncommitted changes
- Cross-repository PR support

## Installation

To use these local plugins in Claude Code, follow these steps:

### 1. Add the Local Marketplace

From within the Claude Code CLI, add this directory as a marketplace:

```bash
/plugin marketplace add ./local-marketplace
```

Or from your terminal:

```bash
claude plugin marketplace add ./local-marketplace
```

### 2. Install a Plugin

Once the marketplace is added, install the plugin you want to use:

```bash
/plugin install arch-pr-analyzer@code-dojo-plugins
```

You'll be prompted to choose an installation scope:
- **user**: Available across all your projects
- **project**: Shared with collaborators via `.claude/settings.json`
- **local**: Only in the current repository

### 3. Use the Plugin

After installation, the plugin's commands and skills are available. For arch-pr-analyzer:

- Commands: `/arch-pr-analyzer:arch-analyze`
- Skills: Architectural analysis and PR integration capabilities
- Agents: Architecture analyzer for deep codebase analysis

## Plugin Structure

```
local-marketplace/
├── .claude-plugin/
│   └── marketplace.json          # Marketplace catalog
└── plugins/
    └── arch-pr-analyzer/
        ├── .claude-plugin/
        │   └── plugin.json       # Plugin manifest
        ├── agents/               # AI agents
        ├── commands/             # Slash commands
        ├── skills/               # Plugin skills
        └── README.md             # Plugin documentation
```

## Managing Plugins

- **List marketplaces**: `/plugin marketplace list`
- **List installed plugins**: `/plugin list`
- **Uninstall a plugin**: `/plugin uninstall arch-pr-analyzer`
- **Remove marketplace**: `/plugin marketplace remove code-dojo-plugins`

## Development

To add new plugins to this marketplace:

1. Create a new directory under `plugins/`
2. Add `.claude-plugin/plugin.json` with plugin metadata
3. Add your plugin components (commands, skills, agents)
4. Update `marketplace.json` to include the new plugin

For more information on plugin development, see the [Claude Code Plugin Documentation](https://docs.claude.ai/docs/claude-code-plugin-development).
