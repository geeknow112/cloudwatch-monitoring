# セットアップ手順

## 前提条件

- AWS CLI がインストール・設定済み
- SAM CLI がインストール済み
- GitHub Personal Access Token（repo, admin:repo_hook権限）

## 1. 設定ファイルの生成

```bash
# テンプレートから設定ファイルを生成
./scripts/setup-config.sh
```

## 2. 設定ファイルの編集

### config/servers.json
監視対象サーバーのURLとSlack Webhook URLを設定してください：

```json
{
  "servers": {
    "server-001": {
      "url": "https://your-actual-server-001-domain.com",
      "path": "/",
      "port": 80,
      "slack": "https://hooks.slack.com/services/YOUR/YC2/WEBHOOK"
    }
    // 他のサーバーも同様に設定
  }
}
```

### infrastructure/parameters.json
Slack Webhook URLを設定してください：

```json
{
  "Parameters": {
    "Environment": "prod",
    "DefaultSlackWebhook": "https://hooks.slack.com/services/YOUR/DEFAULT/WEBHOOK",
    "YC2SlackWebhook": "https://hooks.slack.com/services/YOUR/YC2/WEBHOOK"
    // 他のサーバー用Webhookも設定
  }
}
```

### infrastructure/template.yaml
監視対象サーバーのドメイン名を実際のものに変更してください：

```yaml
YC2HealthCheck:
  Type: AWS::Route53::HealthCheck
  Properties:
    FullyQualifiedDomainName: your-actual-server-001-domain.com  # ここを変更
```

## 3. デプロイ

```bash
# CodePipelineをデプロイ
./scripts/deploy.sh
```

## 4. 初回実行

1. 設定ファイルを編集後、GitHubにpush
2. CodePipelineが自動実行される
3. AWS Consoleでパイプラインの実行状況を確認

## セキュリティ注意事項

### 機密情報の保護

- `config/servers.json` と `infrastructure/parameters.json` は `.gitignore` で除外されています
- これらのファイルは **絶対にGitHubにpushしないでください**
- 代わりに `.template` ファイルがリポジトリに含まれています

### 設定ファイルの管理

```bash
# 設定ファイルがGitで追跡されていないことを確認
git status

# .gitignoreが正しく動作していることを確認
git check-ignore config/servers.json infrastructure/parameters.json
```

### AWS Secrets Managerの使用（推奨）

本番環境では、Slack Webhook URLをAWS Secrets Managerに保存することを推奨します：

```bash
# Slack WebhookをSecrets Managerに保存
aws secretsmanager create-secret \
    --name "cloudwatch-monitoring/slack-webhooks" \
    --description "Slack webhook URLs for server monitoring" \
    --secret-string '{"default":"https://hooks.slack.com/services/..."}'
```

## 動作確認

- Route 53 Health Checksが作成されていることを確認
- CloudWatch Alarmsが設定されていることを確認
- テスト用にサーバーを一時停止してSlack通知が来ることを確認

## トラブルシューティング

### よくある問題

1. **設定ファイルが見つからない**
   - `./scripts/setup-config.sh` を実行してテンプレートから生成

2. **GitHub Token権限不足**
   - repo, admin:repo_hook権限が必要

3. **ドメイン名設定ミス**
   - template.yamlのFullyQualifiedDomainNameを確認

4. **Slack Webhook URL設定ミス**
   - parameters.jsonの設定を確認

### ログ確認

```bash
# Lambda関数のログ確認
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/prod-slack-notification"

# CodeBuildのログ確認
aws logs describe-log-groups --log-group-name-prefix "/aws/codebuild/"
```

## コスト最適化

- 開発環境では監視間隔を長くする（60秒→300秒）
- 不要なアラームは削除する
- CloudWatch Logsの保持期間を短くする

## 監視項目の追加

新しいサーバーを追加する場合：

1. config/servers.jsonに追加
2. infrastructure/template.yamlにHealth CheckとAlarmを追加
3. parameters.jsonにSlack Webhook URLを追加
4. GitHubにpush（設定ファイルは除外される）
