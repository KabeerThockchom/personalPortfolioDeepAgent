#!/bin/bash
# Start LangGraph server for deep-agents-ui integration
#
# Usage: ./start_langgraph_server.sh [port]
# Default port: 2024

set -e

PORT=${1:-2024}

echo "🚀 Starting LangGraph server for Personal Finance Deep Agent"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: Virtual environment not activated"
    echo "   Run: source venv/bin/activate"
    echo ""
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "   1. Copy .env.example to .env"
    echo "   2. Add your API keys"
    exit 1
fi

# Check if langgraph-cli is installed
if ! command -v langgraph &> /dev/null; then
    echo "❌ Error: langgraph-cli not installed"
    echo "   Run: pip install langgraph-cli"
    exit 1
fi

# Verify agent graph can be imported
echo "🔍 Verifying agent graph..."
if ! python3 -c "from src.agent_graph import graph" 2>/dev/null; then
    echo "❌ Error: Could not import agent graph"
    echo "   Check that all dependencies are installed: pip install -r requirements.txt"
    exit 1
fi
echo "✓ Agent graph verified"
echo ""

# Display configuration
echo "📋 Configuration:"
echo "   Server URL: http://127.0.0.1:$PORT"
echo "   Agent ID: finance-agent"
echo "   Graph module: src/agent_graph.py:graph"
echo "   Environment: .env"
echo ""

# Start server
echo "🌐 Starting server on port $PORT..."
echo "   Press Ctrl+C to stop"
echo ""

langgraph dev --port "$PORT"
