# AWS Chatbot設定手順

## 🎯 目的
YC3の新しいWebhook URL (`rZgoFxt5yt7lXRgWxsYXF5eY`) を使用してAWS ChatbotでSlack通知を実装

## 📋 前提条件
- SlackワークスペースID: `T0F8CFQRY`
- SNSトピック: `arn:aws:sns:ap-northeast-1:030391133325:prod-system-alerts`
- 新しいYC3 Webhook URL: 動作確認済み ✅

## 🚀 設定手順

### 1. AWSコンソールでChatbot設定
```bash
# AWSコンソール → AWS Chatbot → Configure new client
1. Slack workspace: T0F8CFQRY を選択
2. Slackアプリの承認
3. チャンネル選択（YC3用チャンネル）
4. IAMロール設定
5. SNSトピック連携
```

### 2. Slackチャンネル情報の取得
```bash
# Slackでチャンネル情報を確認
1. 対象チャンネルを開く
2. チャンネル名をクリック
3. 「設定」→「チャンネルの詳細」
4. チャンネルIDをコピー（例: C1234567890）
```

### 3. CloudFormationでの自動設定
```bash
# パラメータを設定してデプロイ
aws cloudformation create-stack \
  --stack-name chatbot-slack-integration \
  --template-body file://infrastructure/chatbot-template.yaml \
  --parameters ParameterKey=SlackChannelId,ParameterValue=C1234567890 \
  --capabilities CAPABILITY_NAMED_IAM \
  --profile lober-system \
  --region ap-northeast-1
```

### 4. テスト実行
```bash
# SNSトピックにテストメッセージを送信
aws sns publish \
  --topic-arn arn:aws:sns:ap-northeast-1:030391133325:prod-system-alerts \
  --message "Test notification from CloudWatch Monitoring - YC3" \
  --profile lober-system \
  --region ap-northeast-1
```

## 🔧 利点
- ✅ Webhook URL不要
- ✅ OAuth認証で安全
- ✅ AWS公式統合
- ✅ 無料
- ✅ 組織制限を回避

## 📊 現在の状況
- YC3 Webhook URL: 直接テスト成功 ✅
- Lambda Webhook: 403エラー ❌
- AWS Chatbot: 設定準備完了 🔄

## 🎯 次のステップ
1. Slackチャンネル情報の取得
2. AWS Chatbot設定の実行
3. テスト通知の送信
4. 他のサーバー（YC2, Keepa, DBC, Labor-Hack）への展開
