#!/bin/bash
# Setup script for Local AI Coding Buddy

set -e

echo "======================================"
echo "Local AI Coding Buddy - Setup"
echo "======================================"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Error: docker-compose is not installed"
    exit 1
fi

echo "✓ Docker and docker-compose are installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "✓ Created .env file - please edit it with your settings"
    echo ""
fi

# Create models directory
echo "Creating models directory..."
mkdir -p models
echo "✓ Models directory created"
echo ""

# Download model (placeholder - user needs to do this manually)
echo "======================================"
echo "IMPORTANT: Model Download Required"
echo "======================================"
echo ""
echo "You need to download a GGUF model and place it in the models/ directory."
echo ""
echo "Recommended models:"
echo "  - CodeLlama 7B: https://huggingface.co/TheBloke/CodeLlama-7B-GGUF"
echo "  - Mistral 7B: https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF"
echo ""
echo "Download a model and save it as: models/base-model.gguf"
echo ""
read -p "Press Enter when you have downloaded a model..."
echo ""

# Check if model exists
if [ ! -f models/base-model.gguf ]; then
    echo "Warning: models/base-model.gguf not found"
    echo "You can continue, but the system won't work until you add a model"
    echo ""
fi

# Build containers
echo "Building Docker containers..."
echo "This may take several minutes..."
echo ""

docker-compose build

echo ""
echo "✓ Containers built successfully"
echo ""

# Create state directory
docker volume create coding-buddy-state 2>/dev/null || true

echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env file with your project path"
echo "2. Ensure your model is in models/base-model.gguf"
echo "3. Run: docker-compose up -d"
echo "4. Test: docker-compose exec orchestrator python -m orchestrator.main status"
echo ""
echo "For help, see README.md"
echo ""
