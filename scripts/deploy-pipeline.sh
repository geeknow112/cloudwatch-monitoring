#!/bin/bash

# CloudWatch Monitoring CodePipeline Deployment Script

set -e

# Configuration
STACK_NAME="cloudwatch-monitoring-pipeline"
TEMPLATE_FILE="pipeline/codepipeline-template.yaml"
REGION="ap-northeast-1"
PROFILE="lober-system"

# GitHub Configuration
GITHUB_OWNER="geeknow112"
GITHUB_REPO="cloudwatch-monitoring"
GITHUB_BRANCH="main"

echo "🚀 Deploying CloudWatch Monitoring CodePipeline..."
echo "Stack Name: $STACK_NAME"
echo "Region: $REGION"
echo "Profile: $PROFILE"
echo ""

# Check if GitHub token is provided
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ Error: GITHUB_TOKEN environment variable is required"
    echo "Please set your GitHub personal access token:"
    echo "export GITHUB_TOKEN=your_github_token_here"
    exit 1
fi

echo "✅ GitHub token provided"

# Validate CloudFormation template
echo "🔍 Validating CloudFormation template..."
aws cloudformation validate-template \
    --template-body file://$TEMPLATE_FILE \
    --profile $PROFILE \
    --region $REGION

echo "✅ Template validation successful"

# Deploy CodePipeline stack
echo "📦 Deploying CodePipeline stack..."
aws cloudformation deploy \
    --template-file $TEMPLATE_FILE \
    --stack-name $STACK_NAME \
    --parameter-overrides \
        GitHubOwner=$GITHUB_OWNER \
        GitHubRepo=$GITHUB_REPO \
        GitHubBranch=$GITHUB_BRANCH \
        GitHubToken=$GITHUB_TOKEN \
        Environment=prod \
    --capabilities CAPABILITY_NAMED_IAM \
    --profile $PROFILE \
    --region $REGION

if [ $? -eq 0 ]; then
    echo "✅ CodePipeline deployment successful!"
    
    # Get pipeline information
    echo ""
    echo "📊 Pipeline Information:"
    aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --profile $PROFILE \
        --region $REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`PipelineName`].OutputValue' \
        --output text
        
    echo ""
    echo "🔗 You can view the pipeline in the AWS Console:"
    echo "https://console.aws.amazon.com/codesuite/codepipeline/pipelines/$STACK_NAME-pipeline/view"
    
else
    echo "❌ CodePipeline deployment failed!"
    exit 1
fi

echo ""
echo "🎉 CodePipeline setup complete!"
echo "The pipeline will automatically trigger on pushes to the $GITHUB_BRANCH branch."
