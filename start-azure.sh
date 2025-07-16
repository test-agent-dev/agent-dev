#!/bin/bash

# TESTIA AI Agent - Azure Setup Script

echo "🔧 Configuring TESTIA for Azure OpenAI..."

# Copy Azure environment file
if [ ! -f .env ]; then
    cp .env.azure .env
    echo "✅ Copied Azure configuration to .env"
else
    echo "⚠️  .env already exists, skipping copy"
fi

# Verify Azure OpenAI configuration
echo "🔍 Verifying Azure OpenAI configuration..."

if grep -q "AZURE_OPENAI_API_KEY=DFNfL" .env; then
    echo "✅ Azure OpenAI API Key configured"
else
    echo "❌ Azure OpenAI API Key not found in .env"
fi

if grep -q "arqhub9744923851.openai.azure.com" .env; then
    echo "✅ Azure OpenAI Endpoint configured"
else
    echo "❌ Azure OpenAI Endpoint not found in .env"
fi

echo "🚀 Starting TESTIA with Azure OpenAI..."

# Set Python path
export PYTHONPATH=$(pwd)/src

# Create necessary directories
mkdir -p data logs

# Load environment variables
export $(cat .env | grep -v '#' | xargs)

# Start the application
python src/main.py
