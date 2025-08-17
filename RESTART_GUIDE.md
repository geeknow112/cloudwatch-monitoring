# 次回再開用ガイド

## 🚀 プロジェクト再開時の確認事項

### 📊 現在のシステム状況
- **ステータス**: 本番稼働中 ✅
- **最終更新**: 2025-07-30
- **監視対象**: 5サーバー
- **通知方法**: Email (<admin-email>)

### 🔧 主要AWSリソース

#### CloudFormationスタック
```bash
# メインスタック
aws cloudformation describe-stacks --stack-name cloudwatch-monitoring --profile your-aws-profile --region ap-northeast-1

# パイプラインスタック  
aws cloudformation describe-stacks --stack-name cwm-pipeline-v2 --profile your-aws-profile --region ap-northeast-1
```

#### Lambda関数
```bash
# ステータスチェック関数
aws lambda get-function --function-name prod-status-checker --profile your-aws-profile --region ap-northeast-1

# 通知ハンドラー関数
aws lambda get-function --function-name prod-notification-handler --profile your-aws-profile --region ap-northeast-1
```

#### SNSトピック
```bash
# 監視アラート用トピック
aws sns get-topic-attributes --topic-arn arn:aws:sns:ap-northeast-1:<ACCOUNT_ID>:prod-system-alerts --profile your-aws-profile --region ap-northeast-1

# サブスクリプション確認
aws sns list-subscriptions-by-topic --topic-arn arn:aws:sns:ap-northeast-1:<ACCOUNT_ID>:prod-system-alerts --profile your-aws-profile --region ap-northeast-1
```

#### Route53ヘルスチェック
```bash
# 全ヘルスチェック一覧
aws route53 list-health-checks --profile your-aws-profile --region ap-northeast-1

# 使用中のヘルスチェックID
YC2_HEALTH_CHECK_ID=620d951e-2165-4837-ac91-c8bb9e60fc56
YC3_HEALTH_CHECK_ID=9c1ce382-e78f-4800-b7a7-3e980c01116a  
KEEPA_HEALTH_CHECK_ID=36386003-6fec-4620-ad6a-110a7f5d73c2
DBC_HEALTH_CHECK_ID=bbba7796-c7ab-4c47-b213-f97361e41b50
LABOR_HACK_HEALTH_CHECK_ID=73e41f90-4e4d-4bc6-a7e7-d92d2328262f
```

### 📧 Email通知設定
- **受信アドレス**: <admin-email>
- **サブスクリプション**: 確認済み
- **通知状況**: 4/5サーバーから受信確認済み

### 💰 コスト情報
- **月額運用コスト**: $4.52
- **主要コスト**: Route53ヘルスチェック ($2.50/月)

## 🔍 システム動作確認コマンド

### 1. 全体ステータス確認
```bash
# Lambda関数実行テスト
aws lambda invoke --function-name prod-status-checker --profile your-aws-profile --region ap-northeast-1 --payload '{}' /tmp/status-test.json && cat /tmp/status-test.json

# CloudWatchアラーム状態確認
aws cloudwatch describe-alarms --profile your-aws-profile --region ap-northeast-1 --query 'MetricAlarms[?contains(AlarmName, `prod`)].{AlarmName:AlarmName,StateValue:StateValue}' --output table
```

### 2. 通知テスト
```bash
# SNS直接通知テスト
aws sns publish --topic-arn arn:aws:sns:ap-northeast-1:<ACCOUNT_ID>:prod-system-alerts --message "Test notification from CloudWatch Monitoring" --subject "Test Alert" --profile your-aws-profile --region ap-northeast-1
```

### 3. ヘルスチェック状態確認
```bash
# 個別ヘルスチェック状態確認
aws route53 get-health-check-status --health-check-id 620d951e-2165-4837-ac91-c8bb9e60fc56 --profile your-aws-profile --region ap-northeast-1
```

## 📂 重要ファイル

### ソースコード
- `src/status_checker.py`: メインの監視ロジック
- `src/slack_notification.py`: 通知ハンドラー
- `infrastructure/template.yaml`: CloudFormationテンプレート
- `pipeline/codepipeline-template.yaml`: CI/CDパイプライン設定

### 設定ファイル
- `buildspec.yml`: CodeBuild設定
- `samconfig.toml`: SAM設定

### ドキュメント
- `PROJECT_COMPLETION_SUMMARY.md`: プロジェクト完了報告
- `REMAINING_ISSUES.md`: 残課題一覧
- `CODEPIPELINE_ISSUE.md`: CodePipeline問題詳細

## 🔧 トラブルシューティング

### よくある問題と解決法

#### 1. Lambda関数が動作しない
```bash
# ログ確認
aws logs describe-log-streams --log-group-name "/aws/lambda/prod-status-checker" --profile your-aws-profile --region ap-northeast-1 --order-by LastEventTime --descending --max-items 1

# 環境変数確認
aws lambda get-function-configuration --function-name prod-status-checker --profile your-aws-profile --region ap-northeast-1 --query 'Environment.Variables'
```

#### 2. Email通知が届かない
```bash
# サブスクリプション状態確認
aws sns list-subscriptions-by-topic --topic-arn arn:aws:sns:ap-northeast-1:<ACCOUNT_ID>:prod-system-alerts --profile your-aws-profile --region ap-northeast-1

# SNSメトリクス確認
aws cloudwatch get-metric-statistics --namespace AWS/SNS --metric-name NumberOfMessagesPublished --dimensions Name=TopicName,Value=prod-system-alerts --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%S) --end-time $(date -u +%Y-%m-%dT%H:%M:%S) --period 300 --statistics Sum --profile your-aws-profile --region ap-northeast-1
```

#### 3. CodePipelineが失敗する
```bash
# パイプライン状態確認
aws codepipeline get-pipeline-state --name cwm-pipeline-v2-pipeline --profile your-aws-profile --region ap-northeast-1

# 手動デプロイで回避
cd /path/to/cloudwatch-monitoring && sam deploy --guided
```

## 📞 緊急時の対応

### システム停止時
1. CloudWatchアラームの確認
2. Lambda関数ログの確認
3. Route53ヘルスチェック状態の確認
4. 必要に応じて手動でのサーバー確認

### 通知停止時
1. SNSサブスクリプション状態の確認
2. Email受信設定の確認
3. 代替通知手段の検討

---

**作成日**: 2025-07-30  
**対象環境**: AWS ap-northeast-1  
**プロファイル**: your-aws-profile
