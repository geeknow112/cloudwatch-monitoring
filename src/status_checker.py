import json
import boto3
import urllib3
import os
from datetime import datetime

def lambda_handler(event, context):
    """
    定期的にRoute 53ヘルスチェックの状態を確認し、
    正常時のOK通知をSlackに送信する
    """
    print(f"Status check started at {datetime.utcnow()}")
    
    # AWS clients
    route53 = boto3.client('route53')
    
    # ヘルスチェック設定
    health_checks = [
        {
            'name': 'Server-001',
            'health_check_id': os.environ.get('YC2_HEALTH_CHECK_ID'),
            'webhook': os.environ.get('YC2_SLACK_WEBHOOK')
        },
        {
            'name': 'Server-002', 
            'health_check_id': os.environ.get('YC3_HEALTH_CHECK_ID'),
            'webhook': os.environ.get('YC3_SLACK_WEBHOOK')
        },
        {
            'name': 'Server-003',
            'health_check_id': os.environ.get('KEEPA_HEALTH_CHECK_ID'),
            'webhook': os.environ.get('KEEPA_SLACK_WEBHOOK')
        },
        {
            'name': 'Server-004',
            'health_check_id': os.environ.get('DBC_HEALTH_CHECK_ID'),
            'webhook': os.environ.get('DBC_SLACK_WEBHOOK')
        },
        {
            'name': 'Server-005',
            'health_check_id': os.environ.get('LABOR_HACK_HEALTH_CHECK_ID'),
            'webhook': os.environ.get('LABOR_HACK_SLACK_WEBHOOK')
        }
    ]
    
    results = []
    
    for check in health_checks:
        try:
            # ヘルスチェック状態を取得
            response = route53.get_health_check_status(
                HealthCheckId=check['health_check_id']
            )
            
            # HealthCheckObservationsから最新のステータスを確認
            observations = response.get('HealthCheckObservations', [])
            if not observations:
                print(f"No observation data for {check['name']}")
                continue
                
            # 最新の観測結果を取得（複数リージョンからの結果）
            success_count = 0
            total_count = len(observations)
            
            for obs in observations:
                status_report = obs.get('StatusReport', {})
                status = status_report.get('Status', '')
                if 'Success' in status:
                    success_count += 1
            
            # 過半数が成功していればOKとする
            is_healthy = success_count > (total_count / 2)
            
            print(f"{check['name']}: {success_count}/{total_count} regions successful")
            
            # 正常時のみSlack通知を送信
            if is_healthy:
                send_ok_notification(check['name'], check['webhook'])
                results.append({
                    'server': check['name'],
                    'status': 'OK',
                    'success_regions': success_count,
                    'total_regions': total_count,
                    'notification': 'sent'
                })
            else:
                results.append({
                    'server': check['name'],
                    'status': 'UNHEALTHY',
                    'success_regions': success_count,
                    'total_regions': total_count,
                    'notification': 'skipped'
                })
                
        except Exception as e:
            print(f"Error checking {check['name']}: {str(e)}")
            results.append({
                'server': check['name'],
                'status': 'error',
                'error': str(e),
                'notification': 'failed'
            })
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Status check completed',
            'timestamp': datetime.utcnow().isoformat(),
            'results': results
        })
    }

def send_ok_notification(server_name, webhook_url):
    """
    正常時のSlack通知を送信
    """
    if not webhook_url:
        print(f"No webhook URL for {server_name}")
        return
        
    current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    
    slack_message = {
        'attachments': [{
            'color': 'good',
            'title': f':white_check_mark: {server_name} - 正常稼働中',
            'fields': [
                {
                    'title': 'ステータス',
                    'value': '正常',
                    'short': True
                },
                {
                    'title': 'チェック時刻',
                    'value': current_time,
                    'short': True
                },
                {
                    'title': '監視間隔',
                    'value': '20分毎の定期チェック',
                    'short': False
                }
            ],
            'footer': 'AWS Route 53 Health Check',
            'ts': int(datetime.utcnow().timestamp())
        }]
    }
    
    try:
        http = urllib3.PoolManager()
        response = http.request(
            'POST',
            webhook_url,
            body=json.dumps(slack_message),
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status == 200:
            print(f"OK notification sent successfully for {server_name}")
        else:
            print(f"Failed to send OK notification for {server_name}: {response.status}")
            
    except Exception as e:
        print(f"Error sending OK notification for {server_name}: {str(e)}")
