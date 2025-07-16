#!/bin/bash

# TESTIA AI Agent - Startup Script

echo "🚀 Starting TESTIA AI Agent..."

# Check if running in Docker
if [ -f /.dockerenv ]; then
    echo "📦 Running in Docker container"
    export PYTHONPATH=/app/src
    cd /app
else
    echo "💻 Running locally"
    export PYTHONPATH=$(pwd)/src
fi

# Load environment variables
if [ -f .env ]; then
    echo "📝 Loading environment variables..."
    export $(cat .env | grep -v '#' | xargs)
fi

# Check for required environment variables
if [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  Warning: No API keys found. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY"
fi

# Create necessary directories
mkdir -p data logs

# Start the application
echo "🎯 Starting TESTIA..."
python src/main.py
