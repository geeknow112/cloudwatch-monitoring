#!/bin/bash

# CloudWatch Monitoring System Deploy Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Load environment variables if .env file exists
if [ -f ".env" ]; then
    echo -e "${YELLOW}Loading environment variables from .env file...${NC}"
    export $(grep -v '^#' .env | xargs)
fi

# Configuration
STACK_NAME="cloudwatch-monitoring-pipeline"
REGION="${AWS_REGION:-ap-northeast-1}"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"
GITHUB_OWNER="geeknow112"
GITHUB_REPO="cloudwatch-monitoring"
GITHUB_BRANCH="main"

echo -e "${GREEN}CloudWatch Monitoring System Deployment${NC}"
echo "========================================"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    exit 1
fi

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo -e "${RED}Error: SAM CLI is not installed${NC}"
    echo "Please install SAM CLI: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html"
    exit 1
fi

# Check AWS credentials
echo -e "${YELLOW}Checking AWS credentials...${NC}"
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}Error: AWS credentials not configured${NC}"
    echo "Please run: aws configure"
    exit 1
fi

# Get GitHub token if not provided
if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${YELLOW}GitHub personal access token is required for CodePipeline${NC}"
    echo "Please create a token at: https://github.com/settings/tokens"
    echo "Required permissions: repo, admin:repo_hook"
    echo "Or set GITHUB_TOKEN environment variable in .env file"
    read -s -p "Enter GitHub token: " GITHUB_TOKEN
    echo
fi

# Deploy CodePipeline
echo -e "${YELLOW}Deploying CodePipeline...${NC}"
aws cloudformation deploy \
    --template-file pipeline/pipeline-template.yaml \
    --stack-name $STACK_NAME \
    --parameter-overrides \
        GitHubToken=$GITHUB_TOKEN \
        GitHubOwner=$GITHUB_OWNER \
        GitHubRepo=$GITHUB_REPO \
        GitHubBranch=$GITHUB_BRANCH \
    --capabilities CAPABILITY_IAM \
    --region $REGION

if [ $? -eq 0 ]; then
    echo -e "${GREEN}CodePipeline deployed successfully!${NC}"
    
    # Get pipeline URL
    PIPELINE_NAME=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --query 'Stacks[0].Outputs[?OutputKey==`PipelineName`].OutputValue' \
        --output text \
        --region $REGION)
    
    echo -e "${GREEN}Pipeline URL: https://console.aws.amazon.com/codesuite/codepipeline/pipelines/${PIPELINE_NAME}/view${NC}"
    
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Run ./scripts/setup-config.sh to create configuration files"
    echo "2. Update config/servers.json with your actual server URLs"
    echo "3. Update infrastructure/parameters.json with your Slack webhook URLs"
    echo "4. Update infrastructure/template.yaml with your actual domain names"
    echo "5. Commit and push changes to trigger the pipeline"
    echo "6. Monitor the pipeline execution in AWS Console"
else
    echo -e "${RED}Failed to deploy CodePipeline${NC}"
    exit 1
fi
