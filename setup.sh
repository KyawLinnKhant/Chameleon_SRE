#!/bin/bash

# Chameleon-SRE Setup Script
# Automated installation and configuration

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🦎 Chameleon-SRE Setup Script"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 is installed"
        return 0
    else
        echo -e "${RED}✗${NC} $1 is not installed"
        return 1
    fi
}

# Step 1: Check prerequisites
echo "Step 1: Checking prerequisites..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

MISSING_DEPS=0

check_command python3 || MISSING_DEPS=1
check_command docker || MISSING_DEPS=1
check_command kubectl || MISSING_DEPS=1
check_command minikube || MISSING_DEPS=1
check_command ollama || MISSING_DEPS=1

echo ""

if [ $MISSING_DEPS -eq 1 ]; then
    echo -e "${YELLOW}⚠ Some dependencies are missing.${NC}"
    echo ""
    echo "Installation instructions:"
    echo "  Python:   https://www.python.org/downloads/"
    echo "  Docker:   https://docs.docker.com/get-docker/"
    echo "  kubectl:  brew install kubectl"
    echo "  minikube: brew install minikube"
    echo "  Ollama:   https://ollama.ai/download"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 2: Python environment setup
echo ""
echo "Step 2: Setting up Python environment..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v conda &> /dev/null; then
    echo "Using Conda environment..."
    conda create -n chameleon-sre python=3.10 -y || true
    source $(conda info --base)/etc/profile.d/conda.sh
    conda activate chameleon-sre
else
    echo "Using venv..."
    python3 -m venv venv
    source venv/bin/activate
fi

echo -e "${GREEN}✓${NC} Python environment activated"

# Step 3: Install dependencies
echo ""
echo "Step 3: Installing Python dependencies..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}✓${NC} Dependencies installed"

# Step 4: Start Ollama
echo ""
echo "Step 4: Setting up Ollama..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if Ollama is running
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Ollama is already running"
else
    echo "Starting Ollama server..."
    ollama serve > /dev/null 2>&1 &
    sleep 3
    
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Ollama server started"
    else
        echo -e "${RED}✗${NC} Failed to start Ollama"
        echo "Please start manually: ollama serve"
    fi
fi

# Pull model
echo "Checking for llama3.2 model..."
if ollama list | grep -q "llama3.2"; then
    echo -e "${GREEN}✓${NC} llama3.2 model already downloaded"
else
    echo "Downloading llama3.2 model (this may take a few minutes)..."
    ollama pull llama3.2
    echo -e "${GREEN}✓${NC} Model downloaded"
fi

# Step 5: Start Minikube
echo ""
echo "Step 5: Setting up Kubernetes..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if minikube status | grep -q "Running"; then
    echo -e "${GREEN}✓${NC} Minikube is already running"
else
    echo "Starting Minikube..."
    minikube start --driver=docker
    echo -e "${GREEN}✓${NC} Minikube started"
fi

# Step 6: Initialize ChromaDB
echo ""
echo "Step 6: Initializing knowledge base..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python scripts/ingest_docs.py

echo -e "${GREEN}✓${NC} Knowledge base initialized"

# Step 7: Run tests
echo ""
echo "Step 7: Running tests..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

pytest tests/ -v --tb=short

echo -e "${GREEN}✓${NC} All tests passed"

# Step 8: Infrastructure test
echo ""
echo "Step 8: Testing Kubernetes connectivity..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python scripts/test_k8s.py

# Final summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next steps:"
echo "  1. Run the agent: python src/main.py"
echo "  2. Or use make: make run"
echo "  3. Deploy to K8s: make k8s-deploy"
echo ""
echo "For help: make help"
echo ""
