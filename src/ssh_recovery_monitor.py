import json
import boto3
import os
import urllib3
import paramiko
from datetime import datetime
from zoneinfo import ZoneInfo

def lambda_handler(event, context):
    """
    SSH経由でのサーバー自動復旧機能
    実際のサーバーにSSH接続してApache/Bitnami再起動
    """
    
    # 監視対象サーバー（実際の設定が必要）
    servers = {
        'YC2': {
            'url': 'https://<server-001-domain>',
            'ssh_host': '<server-001-ip>',
            'ssh_user': 'bitnami',
            'ssh_key': '/tmp/server-001-key.pem',
            'restart_command': 'sudo /opt/bitnami/ctlscript.sh restart apache'
        },
        'YC3': {
            'url': 'https://<server-002-domain>',
            'ssh_host': '<server-002-ip>',
            'ssh_user': 'ubuntu',
            'ssh_key': '/tmp/server-002-key.pem',
            'restart_command': 'sudo systemctl restart apache2'
        }
        # 他のサーバーも同様に設定
    }
    
    # 現在時刻（JST）
    jst_now = datetime.now(ZoneInfo('Asia/Tokyo'))
    current_time = jst_now.strftime('%Y-%m-%d %H:%M')
    timestamp = jst_now.strftime('%Y%m%d-%H%M%S')
    
    results = []
    recovery_actions = []
    
    # 各サーバーをチェック
    for server_name, config in servers.items():
        try:
            # HTTP HEAD リクエストでヘルスチェック
            http = urllib3.PoolManager()
            response = http.request('HEAD', config['url'], timeout=10)
            
            if response.status == 200:
                results.append(f"[O] {server_name}: 正常 (HTTP {response.status})")
            else:
                results.append(f"[!] {server_name}: 異常 (HTTP {response.status}) - 復旧実行中")
                
                # SSH経由で再起動実行
                restart_result = ssh_restart_service(config)
                recovery_actions.append({
                    'server': server_name,
                    'status': response.status,
                    'restart_result': restart_result
                })
                
        except Exception as e:
            results.append(f"[X] {server_name}: 接続エラー - 復旧実行中")
            
            # 接続エラー時も再起動試行
            restart_result = ssh_restart_service(config)
            recovery_actions.append({
                'server': server_name,
                'error': str(e)[:50],
                'restart_result': restart_result
            })
    
    # 復旧後の再チェック（5分後）
    if recovery_actions:
        import time
        time.sleep(300)  # 5分待機
        
        for action in recovery_actions:
            server_name = action['server']
            config = servers[server_name]
            
            try:
                response = http.request('HEAD', config['url'], timeout=10)
                action['post_restart_status'] = response.status
                action['recovery_success'] = response.status == 200
            except:
                action['post_restart_status'] = 'still_failed'
                action['recovery_success'] = False
    
    # レポート作成
    report_text = f"[*] 自動復旧監視レポート ({current_time} JST)\n"
    report_text += "\n".join(results)
    
    if recovery_actions:
        report_text += f"\n\n[🔧] 自動復旧実行結果:"
        for action in recovery_actions:
            success = action.get('recovery_success', False)
            status_icon = "✅" if success else "❌"
            report_text += f"\n{status_icon} {action['server']}: {action['restart_result']}"
    
    # CloudWatch通知
    alarm_name = f'prod-auto-recovery-{timestamp}'
    send_cloudwatch_alert(alarm_name, report_text, recovery_actions)
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': '自動復旧監視完了',
            'timestamp': current_time,
            'servers_checked': len(servers),
            'recovery_actions': len(recovery_actions),
            'successful_recoveries': sum(1 for a in recovery_actions if a.get('recovery_success', False))
        })
    }

def ssh_restart_service(server_config):
    """
    SSH経由でサービス再起動
    """
    try:
        # SSH接続
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # 秘密鍵の取得（AWS Secrets Manager等から）
        private_key = get_ssh_private_key(server_config['ssh_key'])
        
        ssh.connect(
            hostname=server_config['ssh_host'],
            username=server_config['ssh_user'],
            pkey=private_key,
            timeout=30
        )
        
        # 再起動コマンド実行
        stdin, stdout, stderr = ssh.exec_command(server_config['restart_command'])
        
        # 結果確認
        exit_status = stdout.channel.recv_exit_status()
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        ssh.close()
        
        if exit_status == 0:
            return f"success: {output[:100]}"
        else:
            return f"failed: {error[:100]}"
            
    except Exception as e:
        return f"ssh_error: {str(e)[:100]}"

def get_ssh_private_key(key_path):
    """
    SSH秘密鍵を取得（AWS Secrets Manager等から）
    """
    try:
        # AWS Secrets Managerから秘密鍵を取得
        secrets_client = boto3.client('secretsmanager', region_name='us-east-2')
        secret_name = f"ssh-keys/{key_path.split('/')[-1]}"
        
        response = secrets_client.get_secret_value(SecretId=secret_name)
        private_key_str = response['SecretString']
        
        # paramiko用のキーオブジェクトに変換
        from io import StringIO
        private_key = paramiko.RSAKey.from_private_key(StringIO(private_key_str))
        
        return private_key
        
    except Exception as e:
        print(f"Failed to get SSH key: {e}")
        return None

def send_cloudwatch_alert(alarm_name, report_text, recovery_actions):
    """
    CloudWatch経由でSlack通知
    """
    try:
        cloudwatch = boto3.client('cloudwatch', region_name='us-east-2')
        
        cloudwatch.put_metric_alarm(
            AlarmName=alarm_name,
            AlarmDescription=report_text,
            MetricName='AutoRecovery',
            Namespace='Custom/Monitoring',
            Statistic='Sum',
            Period=300,
            EvaluationPeriods=1,
            Threshold=0,
            ComparisonOperator='GreaterThanThreshold',
            AlarmActions=[
                os.environ.get('SNS_TOPIC_ARN')
            ]
        )
        
        # アラーム状態設定
        state_value = 'ALARM' if recovery_actions else 'OK'
        cloudwatch.set_alarm_state(
            AlarmName=alarm_name,
            StateValue=state_value,
            StateReason=f"自動復旧: {len(recovery_actions)}件実行"
        )
        
    except Exception as e:
        print(f"CloudWatch alert failed: {e}")
