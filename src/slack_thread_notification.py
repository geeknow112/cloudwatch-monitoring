import json
import boto3
import requests
import logging
from datetime import datetime

# ログ設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWSクライアント
route53 = boto3.client('route53')
ssm = boto3.client('ssm')

# 監視対象サーバー設定
SERVERS = {
    'YC2': '620d951e-2165-4837-ac91-c8bb9e60fc56',
    'YC3': '9c1ce382-e78f-4800-b7a7-3e980c01116a',
    'Keepa': '36386003-6fec-4620-ad6a-110a7f5d73c2',
    'DBC': 'bbba7796-c7ab-4c47-b213-f97361e41b50',
    'Labor-Hack': '73e41f90-4e4d-4bc6-a7e7-d92d2328262f'
}

def get_slack_config():
    """Slack設定をSSMパラメータから取得"""
    try:
        # Slack Webhook URLを取得
        webhook_response = ssm.get_parameter(
            Name='/slack/webhook/url',
            WithDecryption=True
        )
        webhook_url = webhook_response['Parameter']['Value']
        
        # Slack Bot Tokenを取得（スレッド機能用）
        token_response = ssm.get_parameter(
            Name='/slack/bot/token',
            WithDecryption=True
        )
        bot_token = token_response['Parameter']['Value']
        
        # チャンネルID
        channel_response = ssm.get_parameter(
            Name='/slack/channel/id'
        )
        channel_id = channel_response['Parameter']['Value']
        
        return {
            'webhook_url': webhook_url,
            'bot_token': bot_token,
            'channel_id': channel_id
        }
    except Exception as e:
        logger.error(f"Slack設定取得エラー: {str(e)}")
        return None

def get_thread_ts():
    """定期レポート用のスレッドタイムスタンプを取得/作成"""
    try:
        # 今日の日付でスレッドを管理
        today = datetime.now().strftime('%Y-%m-%d')
        thread_key = f'/slack/thread/{today}'
        
        try:
            response = ssm.get_parameter(Name=thread_key)
            return response['Parameter']['Value']
        except ssm.exceptions.ParameterNotFound:
            # 新しい日付の場合、新しいスレッドを作成
            return None
            
    except Exception as e:
        logger.error(f"スレッドTS取得エラー: {str(e)}")
        return None

def create_main_thread(slack_config):
    """メインスレッドを作成"""
    try:
        today = datetime.now().strftime('%Y年%m月%d日')
        
        payload = {
            'channel': slack_config['channel_id'],
            'text': f'📊 {today} サーバー監視レポート',
            'attachments': [
                {
                    'color': 'good',
                    'text': 'このスレッドで本日の定期レポートをお知らせします'
                }
            ]
        }
        
        headers = {
            'Authorization': f'Bearer {slack_config["bot_token"]}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            'https://slack.com/api/chat.postMessage',
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                thread_ts = result['ts']
                
                # スレッドタイムスタンプを保存
                today = datetime.now().strftime('%Y-%m-%d')
                ssm.put_parameter(
                    Name=f'/slack/thread/{today}',
                    Value=thread_ts,
                    Type='String',
                    Overwrite=True
                )
                
                return thread_ts
        
        logger.error(f"メインスレッド作成失敗: {response.text}")
        return None
        
    except Exception as e:
        logger.error(f"メインスレッド作成エラー: {str(e)}")
        return None

def send_thread_message(slack_config, thread_ts, message):
    """スレッドにメッセージを送信"""
    try:
        payload = {
            'channel': slack_config['channel_id'],
            'text': message,
            'thread_ts': thread_ts
        }
        
        headers = {
            'Authorization': f'Bearer {slack_config["bot_token"]}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            'https://slack.com/api/chat.postMessage',
            headers=headers,
            json=payload
        )
        
        return response.status_code == 200 and response.json().get('ok')
        
    except Exception as e:
        logger.error(f"スレッドメッセージ送信エラー: {str(e)}")
        return False

def lambda_handler(event, context):
    """
    スレッド対応の定期サーバー状況レポート
    """
    try:
        logger.info("スレッド対応定期レポート開始")
        
        # Slack設定を取得
        slack_config = get_slack_config()
        if not slack_config:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Slack設定取得失敗'})
            }
        
        # 全サーバーの状況を確認
        server_status = {}
        all_healthy = True
        
        for server_name, health_check_id in SERVERS.items():
            try:
                response = route53.get_health_check_status(HealthCheckId=health_check_id)
                observations = response['HealthCheckObservations']
                
                if observations:
                    status = observations[0]['StatusReport']['Status']
                    if 'Success' in status and '200' in status:
                        server_status[server_name] = {'status': '正常', 'icon': '✅'}
                    else:
                        server_status[server_name] = {'status': '障害', 'icon': '❌'}
                        all_healthy = False
                else:
                    server_status[server_name] = {'status': '不明', 'icon': '⚠️'}
                    all_healthy = False
                    
            except Exception as e:
                logger.error(f"{server_name}の状況確認エラー: {str(e)}")
                server_status[server_name] = {'status': 'エラー', 'icon': '❌'}
                all_healthy = False
        
        # スレッドタイムスタンプを取得
        thread_ts = get_thread_ts()
        
        # 新しい日の場合、メインスレッドを作成
        if not thread_ts:
            thread_ts = create_main_thread(slack_config)
            if not thread_ts:
                logger.error("メインスレッド作成失敗")
                return {
                    'statusCode': 500,
                    'body': json.dumps({'error': 'メインスレッド作成失敗'})
                }
        
        # レポートメッセージを作成
        current_time = datetime.now().strftime('%H:%M')
        status_lines = []
        
        for server_name, status_info in server_status.items():
            status_lines.append(f"{status_info['icon']} {server_name}: {status_info['status']}")
        
        message = f"⏰ {current_time} 定期レポート\n" + "\n".join(status_lines)
        
        # スレッドにメッセージを送信
        success = send_thread_message(slack_config, thread_ts, message)
        
        if success:
            logger.info(f"スレッドレポート送信完了: {current_time}")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'スレッドレポート送信完了',
                    'servers': server_status,
                    'all_healthy': all_healthy,
                    'timestamp': current_time
                }, ensure_ascii=False)
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'スレッドメッセージ送信失敗'})
            }
        
    except Exception as e:
        logger.error(f"スレッドレポート生成エラー: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
