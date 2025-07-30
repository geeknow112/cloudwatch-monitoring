#!/bin/bash

# Configuration Setup Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}CloudWatch Monitoring Configuration Setup${NC}"
echo "============================================="

# Check if template files exist
if [ ! -f "config/servers.json.template" ]; then
    echo -e "${RED}Error: config/servers.json.template not found${NC}"
    exit 1
fi

if [ ! -f "infrastructure/parameters.json.template" ]; then
    echo -e "${RED}Error: infrastructure/parameters.json.template not found${NC}"
    exit 1
fi

# Copy template files if actual config files don't exist
if [ ! -f "config/servers.json" ]; then
    echo -e "${YELLOW}Creating config/servers.json from template...${NC}"
    cp config/servers.json.template config/servers.json
    echo -e "${GREEN}Created config/servers.json${NC}"
    echo -e "${YELLOW}Please edit config/servers.json with your actual server URLs and Slack webhooks${NC}"
else
    echo -e "${YELLOW}config/servers.json already exists${NC}"
fi

if [ ! -f "infrastructure/parameters.json" ]; then
    echo -e "${YELLOW}Creating infrastructure/parameters.json from template...${NC}"
    cp infrastructure/parameters.json.template infrastructure/parameters.json
    echo -e "${GREEN}Created infrastructure/parameters.json${NC}"
    echo -e "${YELLOW}Please edit infrastructure/parameters.json with your actual Slack webhooks${NC}"
else
    echo -e "${YELLOW}infrastructure/parameters.json already exists${NC}"
fi

echo -e "${GREEN}Configuration setup completed!${NC}"
echo
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Edit config/servers.json with your actual server URLs"
echo "2. Edit infrastructure/parameters.json with your Slack webhook URLs"
echo "3. Update infrastructure/template.yaml with your actual domain names"
echo "4. Run ./scripts/deploy.sh to deploy the pipeline"
echo
echo -e "${RED}IMPORTANT: Never commit the actual config files to Git!${NC}"
echo "The .gitignore file will prevent this, but please double-check."
