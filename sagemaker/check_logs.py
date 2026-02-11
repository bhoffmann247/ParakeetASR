"""
Check SageMaker endpoint logs from CloudWatch
"""

import boto3
import sys
from datetime import datetime, timedelta


def get_logs(endpoint_name, region='ca-central-1', lines=100):
    """Fetch recent logs from CloudWatch"""
    
    logs_client = boto3.client('logs', region_name=region)
    log_group = f'/aws/sagemaker/Endpoints/{endpoint_name}'
    
    print(f"Fetching logs from: {log_group}")
    print("=" * 80)
    
    try:
        # Get log streams
        response = logs_client.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=10
        )
        
        if not response['logStreams']:
            print("No log streams found yet. The endpoint might still be initializing.")
            return
        
        # Get events from all streams and look for errors
        all_messages = []
        
        for stream in response['logStreams']:
            stream_name = stream['logStreamName']
            
            try:
                events_response = logs_client.get_log_events(
                    logGroupName=log_group,
                    logStreamName=stream_name,
                    limit=200,
                    startFromHead=False
                )
                
                events = events_response['events']
                
                for event in events:
                    timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                    message = event['message'].strip()
                    all_messages.append((timestamp, stream_name, message))
                    
            except Exception as e:
                print(f"Error reading stream {stream_name}: {e}")
        
        # Sort by timestamp and show recent messages
        all_messages.sort(key=lambda x: x[0])
        
        print(f"\nShowing last {lines} log entries:\n")
        for timestamp, stream, message in all_messages[-lines:]:
            # Highlight errors
            if any(keyword in message.lower() for keyword in ['error', 'exception', 'traceback', 'failed']):
                print(f"🔴 [{timestamp}] {message}")
            else:
                print(f"[{timestamp}] {message}")
        
    except Exception as e:
        print(f"Error fetching logs: {e}")
        print("\nTry checking the AWS Console:")
        print(f"https://ca-central-1.console.aws.amazon.com/cloudwatch/home?region=ca-central-1#logEventViewer:group=/aws/sagemaker/Endpoints/{endpoint_name}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python check_logs.py <endpoint-name> [region] [lines]")
        print("\nExample:")
        print("  python check_logs.py parakeet-transcription-v2")
        print("  python check_logs.py parakeet-transcription-v2 ca-central-1 100")
        sys.exit(1)
    
    endpoint_name = sys.argv[1]
    region = sys.argv[2] if len(sys.argv) > 2 else 'ca-central-1'
    lines = int(sys.argv[3]) if len(sys.argv) > 3 else 100
    
    get_logs(endpoint_name, region, lines)
