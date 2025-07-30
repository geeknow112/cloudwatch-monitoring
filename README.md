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

1. 設定ファイルの編集（config/servers.json）
2. CodePipelineの作成
3. 初回デプロイの実行

詳細は各ディレクトリのREADMEを参照してください。
