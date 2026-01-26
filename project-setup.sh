#!/bin/bash
# project-setup.sh - Run this before starting a Claude Code session
# Usage: source project-setup.sh (or . project-setup.sh)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔧 Setting up code-dojo development environment..."
echo ""

# =============================================================================
# Node.js Version Check
# =============================================================================
REQUIRED_NODE_MAJOR=23

check_node_version() {
    if ! command -v node &> /dev/null; then
        echo "❌ Node.js is not installed"
        echo "   Install Node.js 23+ or use nvm: nvm install 23"
        return 1
    fi

    NODE_VERSION=$(node --version | sed 's/v//' | cut -d. -f1)

    if [ "$NODE_VERSION" -lt "$REQUIRED_NODE_MAJOR" ]; then
        echo "❌ Node.js version too old: $(node --version)"
        echo "   Required: v${REQUIRED_NODE_MAJOR}+ for MCP servers"

        if command -v nvm &> /dev/null; then
            echo ""
            echo "   You have nvm installed. Run:"
            echo "   nvm install 23 && nvm use 23 && nvm alias default 23"
        fi
        return 1
    else
        echo "✅ Node.js version: $(node --version)"
    fi
}

# =============================================================================
# Environment Variables
# =============================================================================
load_env_vars() {
    if [ -f .env ]; then
        echo "✅ Loading .env variables..."
        set -a
        source .env
        set +a

        # Verify critical variables (without exposing values)
        if [ -n "$GITHUB_PERSONAL_ACCESS_TOKEN" ]; then
            echo "   ✓ GITHUB_PERSONAL_ACCESS_TOKEN is set"
        else
            echo "   ⚠️  GITHUB_PERSONAL_ACCESS_TOKEN is not set"
        fi

        if [ -n "$ANTHROPIC_API_KEY" ]; then
            echo "   ✓ ANTHROPIC_API_KEY is set"
        else
            echo "   ⚠️  ANTHROPIC_API_KEY is not set (needed for AI feedback)"
        fi
    else
        echo "⚠️  No .env file found"
        echo "   Create one with your API keys (see .env.example if available)"
    fi
}

# =============================================================================
# Python Virtual Environment
# =============================================================================
setup_python_venv() {
    if [ -d "venv" ]; then
        echo "✅ Python virtual environment found"

        # Check if we should activate it
        if [ -z "$VIRTUAL_ENV" ]; then
            echo "   Activating venv..."
            source venv/bin/activate
            echo "   ✓ venv activated: $(python --version)"
        else
            echo "   ✓ Already activated: $(python --version)"
        fi
    else
        echo "⚠️  No Python virtual environment found"
        echo "   Create one with: python3 -m venv venv"
    fi
}

# =============================================================================
# npm/npx Health Check
# =============================================================================
check_npm_health() {
    if npm --version &> /dev/null; then
        echo "✅ npm version: $(npm --version)"
    else
        echo "❌ npm is broken or not installed"
        echo "   This will prevent MCP servers from working"
        return 1
    fi
}

# =============================================================================
# MCP Server Readiness
# =============================================================================
check_mcp_readiness() {
    echo ""
    echo "📡 MCP Server Readiness:"

    # Check if GitHub MCP can potentially work
    if [ -n "$GITHUB_PERSONAL_ACCESS_TOKEN" ] && [ "$NODE_VERSION" -ge "$REQUIRED_NODE_MAJOR" ]; then
        echo "   ✓ GitHub MCP should work (token set, Node OK)"
    else
        echo "   ✗ GitHub MCP may fail (check token and Node version)"
    fi
}

# =============================================================================
# Run All Checks
# =============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Load nvm if available (needed for node version switching)
if [ -s "$HOME/.nvm/nvm.sh" ]; then
    source "$HOME/.nvm/nvm.sh"
fi

check_node_version
echo ""
check_npm_health
echo ""
load_env_vars
echo ""
setup_python_venv
check_mcp_readiness

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ Setup complete! You can now run: claude"
echo ""
