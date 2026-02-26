#!/bin/bash
# =============================================================================
# SuperNova — FAANG-Grade Onboarding & Setup Script
#
# This script automates the environment validation, dependency installation,
# and initial orchestration of the SuperNova agent ecosystem.
# =============================================================================

set -e

# Colors for professional output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=====================================================================${NC}"
echo -e "${GREEN}      SuperNova AI — Intelligence Command Center Setup${NC}"
echo -e "${BLUE}=====================================================================${NC}"

# 1. Environment Check
echo -e "\n${BLUE}[1/5] Validating host environment...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 is not installed.${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed. Required for infrastructure.${NC}"
    exit 1
fi

if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}Notice: 'uv' not found. Recommended for faster setup.${NC}"
    echo -e "Installing uv via astral.sh..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
fi

# 2. Workspace Initialization
echo -e "\n${BLUE}[2/5] Initializing workspace...${NC}"
mkdir -p workspace
echo "✓ Jailed workspace directory created at ./workspace"

# 3. Secret Management
echo -e "\n${BLUE}[3/5] Configuring secrets...${NC}"
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${YELLOW}⚠ Created .env from example. Please fill in your API keys.${NC}"
    else
        echo -e "${RED}Error: .env.example not found.${NC}"
        exit 1
    fi
else
    echo "✓ .env file detected."
fi

# 4. Infrastructure Boot
echo -e "\n${BLUE}[4/5] Booting infrastructure (Docker)...${NC}"
if [ -f deploy/docker-compose.yml ]; then
    docker compose -f deploy/docker-compose.yml up -d
else
    # Fallback to current directory look for demo purposes
    if [ -f docker-compose.yml ]; then
        docker compose up -d
    else
        echo -e "${YELLOW}Notice: docker-compose.yml not found. Skipping infra boot.${NC}"
    fi
fi

# 5. Dependency Sync
echo -e "\n${BLUE}[5/5] Synchronizing dependencies...${NC}"
if [ -f pyproject.toml ]; then
    uv sync --all-extras
    echo -e "${GREEN}✓ Dependencies synchronized successfully.${NC}"
else
    echo -e "${YELLOW}Notice: pyproject.toml not found. Skipping sync.${NC}"
fi

echo -e "\n${GREEN}=====================================================================${NC}"
echo -e "${GREEN}Setup Complete! SuperNova is ready for ignition.${NC}"
echo -e "${BLUE}=====================================================================${NC}"
echo -e "\nTo start the agent: ${YELLOW}uvicorn api.gateway:app --reload${NC}"
echo -e "To monitor logs: ${YELLOW}tail -f var/log/supernova/agent.log${NC}"
echo -e "To view dashboard: Open ${YELLOW}nova-dashboard.html${NC} in your browser."
echo -e "${BLUE}=====================================================================${NC}"
