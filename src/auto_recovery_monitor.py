import json
import boto3
import os
import urllib3
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo

def lambda_handler(event, context):
    """
    サーバー監視 + 自動復旧機能
    curl -I でエラー時にApache/Bitnami再起動
    """
    
    # 監視対象サーバー
    servers = {
        'YC2': {
            'url': 'https://<server-001-domain>',
            'restart_command': 'sudo /opt/bitnami/ctlscript.sh restart apache'
        },
        'YC3': {
            'url': 'https://<server-002-domain>',
            'restart_command': 'sudo systemctl restart apache2'
        },
        'Keepa': {
            'url': 'https://<server-003-domain>',
            'restart_command': 'sudo /opt/bitnami/ctlscript.sh restart apache'
        },
        'DBC': {
            'url': 'https://<server-004-domain>/wp-login.php',
            'restart_command': 'sudo systemctl restart apache2'
        },
        'Labor-Hack': {
            'url': 'https://<server-005-domain>',
            'restart_command': 'sudo /opt/bitnami/ctlscript.sh restart apache'
        }
    }
    
    # 現在時刻（JST）
    jst_now = datetime.now(ZoneInfo('Asia/Tokyo'))
    current_time = jst_now.strftime('%Y-%m-%d %H:%M')
    timestamp = jst_now.strftime('%Y%m%d-%H%M%S')
    
    # 監視結果
    results = []
    recovery_actions = []
    
    # 各サーバーをチェック
    for server_name, config in servers.items():
        try:
            # curl -I 相当のHTTP HEAD リクエスト
            http = urllib3.PoolManager()
            response = http.request('HEAD', config['url'], timeout=10)
            
            if response.status == 200:
                results.append(f"[O] {server_name}: 正常 (HTTP {response.status})")
            else:
                results.append(f"[!] {server_name}: 異常 (HTTP {response.status})")
                recovery_actions.append({
                    'server': server_name,
                    'status': response.status,
                    'action': 'restart_attempted'
                })
                
                # 自動復旧実行（実際の環境では適切な権限とSSH接続が必要）
                restart_result = attempt_restart(server_name, config['restart_command'])
                recovery_actions[-1]['restart_result'] = restart_result
                
        except Exception as e:
            results.append(f"[X] {server_name}: エラー ({str(e)[:50]})")
            recovery_actions.append({
                'server': server_name,
                'error': str(e),
                'action': 'restart_attempted'
            })
            
            # 接続エラー時も再起動試行
            restart_result = attempt_restart(server_name, config['restart_command'])
            recovery_actions[-1]['restart_result'] = restart_result
    
    # レポート作成
    report_text = f"[*] 監視レポート + 自動復旧 ({current_time} JST)\n"
    report_text += "\n".join(results)
    
    if recovery_actions:
        report_text += f"\n\n[🔧] 自動復旧実行: {len(recovery_actions)}件"
        for action in recovery_actions:
            report_text += f"\n- {action['server']}: {action.get('restart_result', 'failed')}"
    
    # CloudWatch Alarm作成・通知
    alarm_name = f'prod-monitor-recovery-{timestamp}'
    cloudwatch = boto3.client('cloudwatch', region_name='us-east-2')
    
    try:
        cloudwatch.put_metric_alarm(
            AlarmName=alarm_name,
            AlarmDescription=report_text,
            MetricName='ServerHealth',
            Namespace='Custom/Monitoring',
            Statistic='Average',
            Period=300,
            EvaluationPeriods=1,
            Threshold=1,
            ComparisonOperator='LessThanThreshold',
            AlarmActions=[
                os.environ.get('SNS_TOPIC_ARN', 'arn:aws:sns:us-east-2:030391133325:prod-system-alerts-us-east-2')
            ]
        )
        
        # アラーム状態変更
        state_value = 'ALARM' if recovery_actions else 'OK'
        state_reason = f"[MONITOR-{timestamp}] {len(recovery_actions)}件の復旧実行" if recovery_actions else f"[MONITOR-{timestamp}] 全サーバー正常"
        
        cloudwatch.set_alarm_state(
            AlarmName=alarm_name,
            StateValue=state_value,
            StateReason=state_reason
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': '監視+自動復旧完了',
                'timestamp': current_time,
                'servers_checked': len(servers),
                'recovery_actions': len(recovery_actions),
                'actions': recovery_actions
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def attempt_restart(server_name, restart_command):
    """
    サーバー再起動を試行
    実際の環境では適切なSSH接続とsudo権限が必要
    """
    try:
        # 注意: 実際の実装では以下が必要:
        # 1. SSH接続設定
        # 2. 適切な認証（キーペア等）
        # 3. sudo権限
        # 4. セキュリティグループ設定
        
        # 疑似実装（実際にはSSH経由で実行）
        print(f"[RESTART] {server_name}: {restart_command}")
        
        # 実際の実装例:
        # import paramiko
        # ssh = paramiko.SSHClient()
        # ssh.connect(hostname, username='bitnami', key_filename='/path/to/key.pem')
        # stdin, stdout, stderr = ssh.exec_command(restart_command)
        # result = stdout.read().decode()
        # ssh.close()
        
        return "success_simulated"
        
    except Exception as e:
        return f"failed: {str(e)}"
