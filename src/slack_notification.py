import json
import urllib3
import os
from datetime import datetime
import pytz

def lambda_handler(event, context):
    """
    CloudWatch AlarmからSNS経由で呼び出されるSlack通知Lambda関数
    既存のPHPスクリプトと同様の通知形式を維持
    """
    
    # SNSメッセージの解析
    sns_message = json.loads(event['Records'][0]['Sns']['Message'])
    
    # アラーム情報の取得
    alarm_name = sns_message['AlarmName']
    new_state = sns_message['NewStateValue']
    reason = sns_message['NewStateReason']
    
    # サーバー名をアラーム名から抽出
    server_name = alarm_name.split('-')[0]  # 例: "yc2-health-check-failed" -> "yc2"
    
    # 日本時間での現在時刻
    jst = pytz.timezone('Asia/Tokyo')
    dt = datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S')
    
    # ステータスの判定
    status = "OK" if new_state == "OK" else "NG"
    
    # Slack Webhook URLを環境変数から取得
    slack_webhook_url = os.environ.get(f'{server_name.upper()}_SLACK_WEBHOOK')
    if not slack_webhook_url:
        slack_webhook_url = os.environ.get('DEFAULT_SLACK_WEBHOOK')
    
    if not slack_webhook_url:
        print(f"Slack webhook URL not found for {server_name}")
        return {
            'statusCode': 400,
            'body': json.dumps('Slack webhook URL not configured')
        }
    
    # Slackメッセージの作成（既存のPHPスクリプトと同じ形式）
    message = f"[{dt}] {server_name}: {status}."
    
    # 詳細情報を追加
    if status == "NG":
        message += f" Reason: {reason}"
    
    slack_message = {
        "text": message
    }
    
    # Slack通知の送信
    http = urllib3.PoolManager()
    
    try:
        response = http.request(
            'POST',
            slack_webhook_url,
            body=json.dumps(slack_message),
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Slack notification sent for {server_name}: {response.status}")
        
        return {
            'statusCode': 200,
            'body': json.dumps(f'Notification sent successfully for {server_name}')
        }
        
    except Exception as e:
        print(f"Error sending Slack notification: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error sending notification: {str(e)}')
        }
