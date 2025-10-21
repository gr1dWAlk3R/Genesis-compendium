#!/bin/bash
# Quick setup script for Resonance Math Memory Agent

set -e

echo "=================================="
echo "RESONANCE MATH MEMORY AGENT SETUP"
echo "=================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found. Please install Python 3.8+"
    exit 1
fi

echo "✓ Python found: $(python3 --version)"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate
echo "✓ Virtual environment created"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Setup .env if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your ANTHROPIC_API_KEY"
    echo "   Get your key from: https://console.anthropic.com/"
    echo ""
else
    echo "✓ .env file already exists"
    echo ""
fi

# Create data directory
mkdir -p data/chroma
echo "✓ Data directory created"
echo ""

echo "=================================="
echo "SETUP COMPLETE"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Edit .env and add your ANTHROPIC_API_KEY"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Ingest knowledge: python src/ingest_knowledge.py"
echo "4. Start chatting: python src/memory_agent.py"
echo ""
