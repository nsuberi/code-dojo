# Architecture PR Analyzer - Plugin Settings Template
# Copy this file to your project's .claude/ directory and customize as needed
# File: .claude/arch-pr-analyzer.md

## Default Behavior

default_granularity: medium
# Options: high, medium, low, or custom level name

output_verbosity: detailed
# Options: detailed, summary, minimal
# - detailed: Full analysis with all sections
# - summary: Executive summary + key changes only
# - minimal: Just the architecture diagram + impact

auto_save_analyses: true
# Save analysis to .claude/analyses/ automatically

display_in_conversation: true
# Show summary in chat (in addition to file)

---

## GitHub Integration

github_token: [see .claude/arch-pr-analyzer.local.md for token]
# DO NOT put your actual token here - use .local.md file

default_repository: null
# Optional: Set default owner/repo to avoid typing it every time
# Format: "owner/repo" (e.g., "facebook/react")
# If set, /arch-analyze 123 will use this repo

---

## Output Preferences

include_diagrams: true
# Generate Mermaid diagrams in analysis

diagram_types: [mermaid, ascii]
# Which diagram formats to generate
# Options: mermaid, ascii
# Multiple types can be specified

save_to_directory: .claude/analyses/
# Where to save analysis markdown files

filename_format: "pr-{owner}-{repo}-{number}-{timestamp}"
# Customize output filename
# Available variables: {owner}, {repo}, {number}, {timestamp}, {granularity}

---

## Architecture Documentation

architecture_doc_paths:
  - docs/architecture.md
  - README.md
  - docs/ARCHITECTURE.md
  - .claude/architecture-context.md
# Paths to your architecture documentation
# Claude will read these for context before analyzing PRs
# Helps identify component boundaries and architectural patterns

component_definitions_file: .claude/components.yaml
# Optional: YAML file defining your architecture components

---

## Analysis Customization

always_include_sections:
  - executive_summary
  - architecture_diagram
  - impact_assessment
  - changes_by_component
# Always include these sections regardless of verbosity setting

optional_sections:
  - detailed_file_catalog
  - dependency_graph
  - api_surface_changes
  - database_schema_changes
  - data_flow_analysis
# Include these based on what changed in the PR

highlight_breaking_changes: true
# Use special formatting for breaking changes

show_code_snippets: true
# Include relevant code snippets in analysis

max_snippet_lines: 10
# Maximum lines per code snippet

---

## Custom Granularity Levels

custom_granularities:
  - name: microservice
    description: "Microservice-level analysis for microservice architectures"
    config_file: .claude/granularity-microservice.md

  - name: data-model
    description: "Focus on data model and schema changes"
    config_file: .claude/granularity-data-model.md

# Define custom analysis perspectives
# See examples/ directory for custom granularity templates

---

## Performance & Caching

cache_pr_data: true
# Cache PR data to reduce API calls

cache_duration_hours: 24
# How long to cache PR data

max_files_to_analyze: 100
# Safety limit: Skip analysis if PR has more than this many files
# Prevents timeout on massive PRs

parallel_file_analysis: true
# Analyze multiple files in parallel (faster)

max_parallel_requests: 5
# Maximum concurrent GitHub API requests

---

## Notifications & Integration

post_comment_to_pr: false
# Automatically post analysis as PR comment
# Requires write access to repository

comment_format: summary
# Options: summary, full
# What to include in PR comment

notify_on_breaking_changes: true
# Alert user if breaking changes detected

slack_webhook: null
# Optional: Post analysis summary to Slack
# Format: https://hooks.slack.com/services/YOUR/WEBHOOK/URL

---

## Advanced

enable_experimental_features: false
# Enable experimental analysis techniques

log_level: info
# Options: debug, info, warn, error

dry_run_mode: false
# Show what would be analyzed without actually analyzing

include_git_history_context: true
# Fetch commit messages and history for additional context

max_commit_history: 20
# How many commits to analyze for context
