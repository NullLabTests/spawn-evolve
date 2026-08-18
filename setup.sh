#!/bin/bash
set -e

echo "=== spawn-evolve setup ==="

# System deps
sudo apt-get update -qq
sudo apt-get install -y -qq python3 python3-pip git curl jq > /dev/null 2>&1

# Python deps
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt 2>/dev/null || true

# Install opencode
if ! command -v opencode &> /dev/null; then
    echo "Installing opencode..."
    curl -fsSL https://opencode.ai/install | bash
    export PATH="$HOME/.opencode/bin:$PATH"
    echo 'export PATH="$HOME/.opencode/bin:$PATH"' >> ~/.bashrc
fi

# Verify opencode
opencode --version 2>/dev/null || echo "opencode installed (version check skipped)"

# Create directory structure
mkdir -p core arenas/adversarial arenas/escape arenas/puzzles \
         population generations logs reports .opencode/agents

echo "=== Setup complete ==="
echo "Run: ./run.sh pilot puzzles 10"
