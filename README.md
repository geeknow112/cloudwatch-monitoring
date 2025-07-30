# CloudWatch Server Monitoring System

既存のPHPスクリプトによるサーバー監視をCloudWatchベースの24時間監視システムに移行するプロジェクトです。

## 概要

- **監視対象**: 5つのサーバー（yc2, yc3, keepa, dbc, labor-hack）
- **監視方法**: Route 53 Health Checks + CloudWatch Alarms
- **通知**: Slack Webhook（既存の通知形式を維持）
- **デプロイ**: CodePipeline + SAM

## アーキテクチャ

```
Route 53 Health Checks → CloudWatch Alarms → SNS → Lambda → Slack
```

## ディレクトリ構成

```
cloudwatch-monitoring/
├── src/
│   └── slack-notification.py      # Slack通知Lambda関数
├── infrastructure/
│   ├── template.yaml              # SAM template
│   └── parameters.json            # パラメータファイル
├── pipeline/
│   ├── buildspec.yml              # CodeBuild設定
│   └── pipeline-template.yaml     # CodePipeline CloudFormation
├── config/
│   └── servers.json               # 監視対象サーバー設定
└── scripts/
    └── deploy.sh                  # デプロイスクリプト
```

## 月額コスト見積もり

- Route 53 Health Checks: $2.50
- CloudWatch: $2.00
- SNS: $0.001
- Lambda: $0（無料枠内）
- CodePipeline: $1.03

**合計: 約$5.53/月（約830円）**

## セットアップ手順

### Option A: CodePipeline Deployment (推奨)

```bash
# 1. GitHub personal access tokenを設定
export GITHUB_TOKEN=your_github_token_here

# 2. CodePipelineをデプロイ
./scripts/deploy-pipeline.sh

# 3. mainブランチへのpush時に自動デプロイされます
```

### Option B: 直接デプロイ

1. 設定ファイルの編集（config/servers.json）
2. SAM CLIでの直接デプロイ
3. 手動での設定更新

詳細は各ディレクトリのREADMEを参照してください。

## 🔧 Configuration Parameters

### Domain Names and Paths
All server URLs and paths are now parameterized for security:

```bash
# Example deployment with parameters
sam deploy --template-file infrastructure/template.yaml \
  --stack-name cloudwatch-monitoring \
  --parameter-overrides \
    Environment=prod \
    YC2Domain=your-yc2-domain.com \
    YC3Domain=your-yc3-domain.com \
    KeepaDomain=your-keepa-domain.com \
    DbcDomain=your-dbc-domain.com \
    LaborHackDomain=your-labor-hack-domain.com \
    YC2Path=/ \
    YC3Path=/ \
    KeepaPath=/ \
    DbcPath=/wp-login.php \
    LaborHackPath=/ \
    DefaultSlackWebhook=https://hooks.slack.com/services/YOUR/DEFAULT/WEBHOOK \
    [... other Slack webhooks ...] \
  --capabilities CAPABILITY_IAM \
  --region ap-northeast-1 \
  --profile your-aws-profile \
  --resolve-s3
```

### Security Notes
- ✅ No hardcoded URLs in CloudFormation templates
- ✅ All sensitive data passed as parameters
- ✅ Configuration files excluded from Git
- ✅ Template files contain only placeholders
