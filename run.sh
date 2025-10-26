#!/bin/bash

# Trading Chatbot Startup Script
# This script sets up and runs the trading chatbot application

set -e  # Exit on error

echo "==================================="
echo "Trading Chatbot Startup"
echo "==================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    echo "Please copy .env.example to .env and configure your settings"
    exit 1
fi

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}UV not found. Installing...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

echo -e "${GREEN}✓ UV installed${NC}"

# Create virtual environment if it doesn't exist
if [ ! -d .venv ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    uv venv
fi

echo -e "${GREEN}✓ Virtual environment ready${NC}"

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
uv pip install -r requirements.txt

echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create necessary directories
mkdir -p logs/evaluations tmp/uploads

echo -e "${GREEN}✓ Directories created${NC}"

# Note: Data files are now stored in src/data/ directory
# The application will automatically load them from there

# Run tests (optional)
if [ "$1" == "--test" ]; then
    echo -e "${YELLOW}Running tests...${NC}"
    pytest tests/ -v
    echo -e "${GREEN}✓ Tests passed${NC}"
fi

# Start Docker services if requested
if [ "$1" == "--docker" ]; then
    echo -e "${YELLOW}Starting Docker services...${NC}"
    docker-compose -f docker/docker-compose.yml up -d
    echo -e "${GREEN}✓ Docker services started${NC}"
    echo "Waiting for services to be ready..."
    sleep 5
fi

# Run the application
echo -e "${GREEN}Starting Trading Chatbot...${NC}"
echo "==================================="
echo "API will be available at: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "==================================="

# Run with uvicorn
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Trap Ctrl+C and cleanup
trap 'echo -e "\n${YELLOW}Shutting down...${NC}"; exit 0' INT