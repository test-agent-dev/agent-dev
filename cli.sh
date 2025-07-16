#!/bin/bash

# TESTIA AI Agent - CLI Script

export PYTHONPATH=$(pwd)/src

# Check if running in Docker
if [ -f /.dockerenv ]; then
    cd /app
fi

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | xargs)
fi

# Run CLI
python src/cli/main.py "$@"
