import json
import boto3
import logging
from datetime import datetime, timezone, timedelta

# ログ設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 日本時間のタイムゾーン
JST = timezone(timedelta(hours=9))

# AWSクライアント
route53 = boto3.client('route53')
cloudwatch = boto3.client('cloudwatch')

# 監視対象サーバー設定
SERVERS = {
    'YC2': '620d951e-2165-4837-ac91-c8bb9e60fc56',
    'YC3': '9c1ce382-e78f-4800-b7a7-3e980c01116a',
    'Keepa': '36386003-6fec-4620-ad6a-110a7f5d73c2',
    'DBC': 'bbba7796-c7ab-4c47-b213-f97361e41b50',
    'Labor-Hack': '73e41f90-4e4d-4bc6-a7e7-d92d2328262f'
}

def lambda_handler(event, context):
    """
    定期的なサーバー状況レポートを生成してSlackに通知（日本時間対応）
    """
    try:
        logger.info("定期サーバー状況レポート開始")
        
        # 日本時間を取得
        jst_now = datetime.now(JST)
        current_time = jst_now.strftime('%Y-%m-%d %H:%M')
        current_hour = jst_now.strftime('%H:%M')
        
        # 全サーバーの状況を確認
        server_status = {}
        all_healthy = True
        
        for server_name, health_check_id in SERVERS.items():
            try:
                # Route53ヘルスチェック状況を取得
                response = route53.get_health_check_status(HealthCheckId=health_check_id)
                observations = response['HealthCheckObservations']
                
                if observations:
                    status = observations[0]['StatusReport']['Status']
                    if 'Success' in status and '200' in status:
                        server_status[server_name] = {'status': '正常', 'icon': '✅', 'detail': 'HTTP 200'}
                    else:
                        server_status[server_name] = {'status': '障害', 'icon': '❌', 'detail': status}
                        all_healthy = False
                else:
                    server_status[server_name] = {'status': '不明', 'icon': '⚠️', 'detail': 'データなし'}
                    all_healthy = False
                    
            except Exception as e:
                logger.error(f"{server_name}の状況確認エラー: {str(e)}")
                server_status[server_name] = {'status': 'エラー', 'icon': '❌', 'detail': str(e)}
                all_healthy = False
        
        # 定期レポート用のアラーム説明文を作成（[O]=OK、[X]=NG表現）
        report_lines = [f"[*] 定期レポート ({current_hour} JST)"]
        for server_name, status_info in server_status.items():
            # [O]=OK、[X]=NGで状態を表現
            if status_info['status'] == '正常':
                symbol = "[O]"
            elif status_info['status'] == '障害':
                symbol = "[X]"
            elif status_info['status'] == '不明':
                symbol = "[?]"
            else:
                symbol = "[!]"
            
            report_lines.append(f"{symbol} {server_name}: {status_info['status']} ({status_info['detail']})")
        
        alarm_description = '\n'.join(report_lines)
        
        # CloudWatchアラームを更新
        cloudwatch.put_metric_alarm(
            AlarmName='prod-server-001-health-check-failed',
            AlarmDescription=alarm_description,
            MetricName='HealthCheckStatus',
            Namespace='AWS/Route53',
            Statistic='Minimum',
            Period=60,
            EvaluationPeriods=1,
            Threshold=1.0,
            ComparisonOperator='LessThanThreshold',
            Dimensions=[
                {
                    'Name': 'HealthCheckId',
                    'Value': SERVERS['YC2']
                }
            ],
            AlarmActions=[
                'arn:aws:sns:ap-northeast-1:030391133325:prod-system-alerts'
            ],
            OKActions=[
                'arn:aws:sns:ap-northeast-1:030391133325:prod-system-alerts'
            ]
        )
        
        # アラーム状態を変更して通知をトリガー（[O]/[X]表現）
        if all_healthy:
            state_reason = f"[O] 定期レポート ({current_time} JST) - 全サーバー正常稼働中"
            state_value = 'OK'
        else:
            state_reason = f"[X] 定期レポート ({current_time} JST) - 一部サーバーに問題あり"
            state_value = 'ALARM'
        
        cloudwatch.set_alarm_state(
            AlarmName='prod-server-001-health-check-failed',
            StateValue=state_value,
            StateReason=state_reason
        )
        
        logger.info(f"定期レポート送信完了: {state_reason}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': '定期レポート送信完了',
                'servers': server_status,
                'all_healthy': all_healthy,
                'timestamp': current_time,
                'timezone': 'JST'
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        logger.error(f"定期レポート生成エラー: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            }, ensure_ascii=False)
        }
