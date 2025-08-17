# CodePipeline Deploy Stage Issue

## 🚨 問題概要
CodePipelineのDeployステージが継続的に失敗している。ただし、実際のCloudFormationスタックは正常に更新されており、システム自体は完全に稼働中。

## 📊 現在の状況

### ✅ 正常動作中
- **CloudWatch監視システム**: 完全稼働
- **Lambda関数**: `prod-status-checker`, `prod-notification-handler` 正常動作
- **Route53ヘルスチェック**: 全サーバー監視中（16リージョン）
- **CloudWatchアラーム**: 正常設定
- **SNS通知**: 正常動作
- **Slack通知**: 新しいWebhook URLで復旧済み
- **手動SAMデプロイ**: 正常動作

### ❌ 問題箇所
- **CodePipeline Deployステージ**: 継続的に失敗
- **影響**: なし（システム稼働中、手動デプロイ可能）

## 🔍 技術詳細

### CodePipeline構成
```yaml
Pipeline: cwm-pipeline-v2-pipeline
Stages:
  - Source: ✅ 成功 (GitHub連携)
  - Build: ✅ 成功 (SAM CLI)
  - Deploy: ❌ 失敗 (CloudFormationアクション)
```

### CloudFormationアクション設定
```yaml
ActionMode: CREATE_UPDATE
StackName: cloudwatch-monitoring
TemplatePath: BuildOutput::packaged-template.yaml
Capabilities: CAPABILITY_IAM,CAPABILITY_NAMED_IAM
RoleArn: !GetAtt CloudFormationServiceRole.Arn
```

### 確認済み項目
- ✅ CloudFormationServiceRole権限: PowerUserAccess + 包括的権限
- ✅ S3アーティファクトバケット: 正常動作
- ✅ buildspec.yml: 正常設定
- ✅ パラメータ設定: 正常
- ✅ 実際のCloudFormationスタック: UPDATE_COMPLETE

## 🔧 調査が必要な項目

### 1. CodePipelineログ分析
- CloudFormationアクションの詳細エラーログ
- CodePipelineとCloudFormationの連携問題

### 2. 権限設定の詳細確認
- CloudFormationServiceRoleの実際の権限
- CodePipelineServiceRoleとの権限分離

### 3. アクション設定の見直し
- ParameterOverridesの形式
- Capabilitiesの設定
- RoleArnの参照方法

## 📋 再現手順

1. GitHubにコードをプッシュ
2. CodePipelineが自動実行開始
3. Sourceステージ: 成功
4. Buildステージ: 成功
5. Deployステージ: 失敗（CloudFormationは実際には成功）

## 🎯 期待する結果
CodePipelineのDeployステージが成功し、完全な自動CI/CDが動作する。

## 📊 優先度
**低** - システム本体は完全稼働中、手動デプロイで運用可能

## 🔗 関連ファイル
- `pipeline/codepipeline-template.yaml`
- `buildspec.yml`
- `infrastructure/template.yaml`

## 📝 追加情報

### 監視対象サーバー
- **YC2**: <server-001-domain>
- **YC3**: <server-002-domain>
- **Keepa**: <server-003-domain>
- **DBC**: <server-004-domain>/wp-login.php
- **Labor-Hack**: <server-005-domain>

### 新しいSlack Webhook URL
- YC2: `AvMXC0txHi1tQooMBPAi53YC`
- YC3: `sLl6rPWgg8HZNgUrM1VUtUlR`
- Keepa: `Ek07tOtFbX18K76t1Rr46Iu8`
- DBC: `47oWeSu38MSqDurewNlYY89V`
- Labor-Hack: `I3TIuva6mu9xXcTmwUVRVxSz`

---

**注意**: このIssueはCI/CDの自動化に関する問題であり、監視システム自体の動作には影響しません。
