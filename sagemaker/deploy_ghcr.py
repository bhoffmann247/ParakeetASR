"""
Deploy to SageMaker using GitHub Container Registry (GHCR)

This script deploys a custom Docker container from GHCR to SageMaker.
"""

import argparse
import boto3
import sagemaker
from datetime import datetime
import time


def deploy_from_ghcr(
    image_uri,
    role_arn,
    instance_type='ml.g5.2xlarge',
    endpoint_name=None,
    initial_instance_count=1
):
    """
    Deploy a model from GHCR to SageMaker
    
    Args:
        image_uri: Full GHCR image URI (e.g., ghcr.io/username/repo:tag)
        role_arn: IAM role ARN with SageMaker permissions
        instance_type: EC2 instance type
        endpoint_name: Name for the endpoint
        initial_instance_count: Number of instances
    """
    
    session = sagemaker.Session()
    
    # Generate endpoint name if not provided
    if endpoint_name is None:
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        endpoint_name = f'parakeet-ghcr-{timestamp}'
    
    print(f"✓ Using role ARN: {role_arn}")
    print(f"✓ Using image: {image_uri}")
    print(f"\nDeploying model to endpoint: {endpoint_name}")
    print(f"Instance type: {instance_type}")
    print(f"Instance count: {initial_instance_count}")
    
    # Create model
    model_name = f'parakeet-model-{datetime.now().strftime("%Y%m%d%H%M%S")}'
    
    sm_client = boto3.client('sagemaker')
    
    print("\nCreating model...")
    sm_client.create_model(
        ModelName=model_name,
        PrimaryContainer={
            'Image': image_uri,
            'Mode': 'SingleModel'
        },
        ExecutionRoleArn=role_arn
    )
    
    print(f"✓ Model created: {model_name}")
    
    # Create endpoint config
    endpoint_config_name = f'parakeet-config-{datetime.now().strftime("%Y%m%d%H%M%S")}'
    
    print("\nCreating endpoint configuration...")
    sm_client.create_endpoint_config(
        EndpointConfigName=endpoint_config_name,
        ProductionVariants=[{
            'VariantName': 'AllTraffic',
            'ModelName': model_name,
            'InstanceType': instance_type,
            'InitialInstanceCount': initial_instance_count
        }]
    )
    
    print(f"✓ Endpoint config created: {endpoint_config_name}")
    
    # Create or update endpoint
    print("\nDeploying endpoint (this may take 5-10 minutes)...")
    
    try:
        # Try to update existing endpoint
        sm_client.describe_endpoint(EndpointName=endpoint_name)
        print(f"Updating existing endpoint: {endpoint_name}")
        
        sm_client.update_endpoint(
            EndpointName=endpoint_name,
            EndpointConfigName=endpoint_config_name
        )
    except sm_client.exceptions.ClientError:
        # Endpoint doesn't exist, create new one
        print(f"Creating new endpoint: {endpoint_name}")
        
        sm_client.create_endpoint(
            EndpointName=endpoint_name,
            EndpointConfigName=endpoint_config_name
        )
    
    # Wait for endpoint to be in service
    print("\nWaiting for endpoint to be ready...")
    waiter = sm_client.get_waiter('endpoint_in_service')
    
    try:
        waiter.wait(
            EndpointName=endpoint_name,
            WaiterConfig={'Delay': 30, 'MaxAttempts': 60}
        )
    except Exception as e:
        print(f"\n⚠ Waiter timed out, but endpoint may still be deploying: {e}")
        print("Check status with: aws sagemaker describe-endpoint --endpoint-name", endpoint_name)
    
    # Get endpoint details
    endpoint_desc = sm_client.describe_endpoint(EndpointName=endpoint_name)
    
    print(f"\n✓ Deployment successful!")
    print(f"Endpoint name: {endpoint_name}")
    print(f"Endpoint status: {endpoint_desc['EndpointStatus']}")
    print(f"Endpoint ARN: {endpoint_desc['EndpointArn']}")
    
    return endpoint_name


def main():
    parser = argparse.ArgumentParser(description='Deploy Parakeet from GHCR to SageMaker')
    
    parser.add_argument(
        '--image',
        required=True,
        help='GHCR image URI (e.g., ghcr.io/username/parakeet-transcription:latest)'
    )
    
    parser.add_argument(
        '--role',
        required=True,
        help='IAM role ARN or name'
    )
    
    parser.add_argument(
        '--instance-type',
        default='ml.g5.2xlarge',
        help='SageMaker instance type (default: ml.g5.2xlarge)'
    )
    
    parser.add_argument(
        '--endpoint-name',
        help='Custom endpoint name (auto-generated if not provided)'
    )
    
    parser.add_argument(
        '--instance-count',
        type=int,
        default=1,
        help='Number of instances (default: 1)'
    )
    
    args = parser.parse_args()
    
    # Get role ARN
    if args.role.startswith('arn:aws:iam::'):
        role_arn = args.role
    else:
        # Construct ARN from role name
        sts = boto3.client('sts')
        account_id = sts.get_caller_identity()['Account']
        
        # Try with and without service-role prefix
        if 'service-role' in args.role:
            role_arn = f"arn:aws:iam::{account_id}:role/{args.role}"
        else:
            role_arn = f"arn:aws:iam::{account_id}:role/service-role/{args.role}"
    
    # Deploy
    endpoint_name = deploy_from_ghcr(
        image_uri=args.image,
        role_arn=role_arn,
        instance_type=args.instance_type,
        endpoint_name=args.endpoint_name,
        initial_instance_count=args.instance_count
    )
    
    print("\n" + "="*60)
    print("DEPLOYMENT COMPLETE")
    print("="*60)
    print(f"\nEndpoint Name: {endpoint_name}")
    print(f"\nTo test the endpoint:")
    print(f"python test_endpoint.py --endpoint {endpoint_name} --audio ../tests/Input/ContactCenter/103046_1000780789-21-00-01.wav")
    print(f"\nTo delete the endpoint:")
    print(f"aws sagemaker delete-endpoint --endpoint-name {endpoint_name}")


if __name__ == '__main__':
    main()
