import json
import boto3
import os
from datetime import datetime

def lambda_handler(event, context):
    """
    定期的にRoute 53ヘルスチェックの状態を確認し、
    Email通知をSNS経由で送信する
    """
    print(f"Status check started at {datetime.utcnow()}")
    
    # AWS clients
    route53 = boto3.client('route53')
    sns = boto3.client('sns')
    
    # ヘルスチェック設定
    health_checks = [
        {
            'name': 'Server-001',
            'health_check_id': os.environ['YC2_HEALTH_CHECK_ID'],
            'domain': 'ycstg.lober-env-imp.work'
        },
        {
            'name': 'Server-002', 
            'health_check_id': os.environ['YC3_HEALTH_CHECK_ID'],
            'domain': 'yamachu.lober-env-imp.work'
        },
        {
            'name': 'Server-003',
            'health_check_id': os.environ['KEEPA_HEALTH_CHECK_ID'],
            'domain': 'ycstg.lober-env-imp.work'
        },
        {
            'name': 'Server-004',
            'health_check_id': os.environ['DBC_HEALTH_CHECK_ID'],
            'domain': 'dbc.47club.co.jp'
        },
        {
            'name': 'Server-005',
            'health_check_id': os.environ['LABOR_HACK_HEALTH_CHECK_ID'],
            'domain': 'hack-note.com'
        }
    ]
    
    sns_topic_arn = os.environ.get('SNS_TOPIC_ARN', 'arn:aws:sns:ap-northeast-1:030391133325:prod-system-alerts')
    results = []
    
    for check in health_checks:
        try:
            # Route53ヘルスチェック状態を取得
            response = route53.get_health_check_status(
                HealthCheckId=check['health_check_id']
            )
            
            status_list = response['StatusList']
            success_count = sum(1 for status in status_list if status['Status'] == 'Success')
            total_count = len(status_list)
            success_rate = (success_count / total_count) * 100 if total_count > 0 else 0
            
            print(f"{check['name']}: {success_count}/{total_count} regions successful ({success_rate:.1f}%)")
            
            # ステータス判定（80%以上で正常）
            if success_rate >= 80:
                status = "OK"
                message = f"✅ {check['name']} ({check['domain']}) is OK\n"
                message += f"Success Rate: {success_rate:.1f}% ({success_count}/{total_count} regions)\n"
                message += f"Timestamp: {datetime.utcnow().isoformat()}Z"
                
                subject = f"CloudWatch Monitoring - {check['name']} Status OK"
            else:
                status = "ALERT"
                message = f"🚨 {check['name']} ({check['domain']}) ALERT\n"
                message += f"Success Rate: {success_rate:.1f}% ({success_count}/{total_count} regions)\n"
                message += f"Threshold: 80% minimum required\n"
                message += f"Timestamp: {datetime.utcnow().isoformat()}Z"
                
                subject = f"🚨 CloudWatch Monitoring - {check['name']} ALERT"
            
            # SNS経由でEmail通知を送信
            try:
                sns_response = sns.publish(
                    TopicArn=sns_topic_arn,
                    Message=message,
                    Subject=subject,
                    MessageAttributes={
                        'server': {
                            'DataType': 'String',
                            'StringValue': check['name']
                        },
                        'status': {
                            'DataType': 'String', 
                            'StringValue': status
                        },
                        'success_rate': {
                            'DataType': 'Number',
                            'StringValue': str(success_rate)
                        }
                    }
                )
                
                notification_status = "sent"
                print(f"Email notification sent successfully for {check['name']}")
                
            except Exception as e:
                notification_status = "failed"
                print(f"Failed to send email notification for {check['name']}: {str(e)}")
            
            results.append({
                'server': check['name'],
                'domain': check['domain'],
                'status': status,
                'success_regions': success_count,
                'total_regions': total_count,
                'success_rate': success_rate,
                'notification': notification_status
            })
            
        except Exception as e:
            print(f"Error checking {check['name']}: {str(e)}")
            results.append({
                'server': check['name'],
                'domain': check.get('domain', 'unknown'),
                'status': 'ERROR',
                'success_regions': 0,
                'total_regions': 0,
                'success_rate': 0,
                'notification': 'failed',
                'error': str(e)
            })
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Status check completed with email notifications',
            'timestamp': datetime.utcnow().isoformat(),
            'notification_method': 'email',
            'sns_topic': sns_topic_arn,
            'results': results
        })
    }
