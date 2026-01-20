# Architecture PR Analyzer - Local Settings (EXAMPLE)
# This file shows the format for storing your GitHub token locally
# Copy to: .claude/arch-pr-analyzer.local.md
# This file is git-ignored to protect your token

## GitHub Configuration

github_token: ghp_your_personal_access_token_here

## Token Scopes Required
# - repo: For analyzing private repository PRs (full access)
# - public_repo: For public repositories only (more limited)
#
# Recommendation: Use 'repo' scope for maximum flexibility

## How to Create a Token
# 1. Go to GitHub Settings > Developer settings > Personal access tokens
# 2. Click "Generate new token (classic)"
# 3. Give it a name: "Claude Architecture Analyzer"
# 4. Select scope: "repo" (or "public_repo" for public repos only)
# 5. Generate and copy the token
# 6. Paste it above on the github_token line
