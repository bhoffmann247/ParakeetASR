# Deployment Guide

This guide covers building, testing, and deploying the Parakeet Transcription API using Docker.

## Prerequisites

- Docker Desktop installed and running (Windows/Mac) or Docker Engine (Linux)
- At least 8GB RAM available for the container
- 4 CPU cores recommended for optimal performance

## Local Docker Deployment

### 1. Build the Docker Image

```bash
docker build -t parakeet-api .
```

This creates a multi-stage Docker image with:
- Python 3.10 slim base
- All required dependencies (ffmpeg, libsndfile1)
- NeMo ASR and diarization models
- FastAPI application

Build time: ~5-10 minutes (depending on internet speed for downloading dependencies)

### 2. Run with Docker Compose (Recommended)

```bash
docker-compose up -d
```

This starts the container with:
- Port 8000 exposed to localhost
- Model cache volume for persistence
- Output directory mounted to `./Output`
- Health checks enabled
- Resource limits configured

### 3. Run with Docker CLI (Alternative)

```bash
docker run -d \
  --name parakeet-api \
  -p 8000:8000 \
  -v parakeet-models:/root/.cache \
  -v ./Output:/app/Output \
  parakeet-api
```

### 4. Verify the Container is Running

Check container status:
```bash
docker ps
```

Check logs:
```bash
docker logs parakeet-api
```

Follow logs in real-time:
```bash
docker logs -f parakeet-api
```

### 5. Test the API

Health check:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy"}
```

List available models:
```bash
curl http://localhost:8000/v1/models
```

Test transcription with diarization:
```bash
curl -X POST http://localhost:8000/v1/audio/transcriptions \
  -F "file=@tests/Input/ContactCenter/103046_1000780789-21-00-01.wav" \
  -F "model=parakeet-tdt-0.6b-v2" \
  -F "response_format=json" \
  -F "enable_diarization=true"
```

### 6. Stop the Container

With Docker Compose:
```bash
docker-compose down
```

With Docker CLI:
```bash
docker stop parakeet-api
docker rm parakeet-api
```

## Container Management

### View Container Logs
```bash
docker logs parakeet-api
```

### Access Container Shell
```bash
docker exec -it parakeet-api /bin/bash
```

### Restart Container
```bash
docker restart parakeet-api
```

### Remove Container and Image
```bash
docker stop parakeet-api
docker rm parakeet-api
docker rmi parakeet-api
```

## AWS Deployment

### Option 1: Amazon ECS (Elastic Container Service)

1. **Push Image to Amazon ECR**

```bash
# Authenticate Docker to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Create ECR repository
aws ecr create-repository --repository-name parakeet-api --region us-east-1

# Tag image
docker tag parakeet-api:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/parakeet-api:latest

# Push image
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/parakeet-api:latest
```

2. **Create ECS Task Definition**

Create a file `ecs-task-definition.json`:

```json
{
  "family": "parakeet-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "4096",
  "memory": "8192",
  "containerDefinitions": [
    {
      "name": "parakeet-api",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/parakeet-api:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "PYTHONUNBUFFERED",
          "value": "1"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/parakeet-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "python -c \"import requests; requests.get('http://localhost:8000/health')\" || exit 1"],
        "interval": 30,
        "timeout": 10,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

Register the task definition:
```bash
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json
```

3. **Create ECS Service**

```bash
aws ecs create-service \
  --cluster your-cluster-name \
  --service-name parakeet-api \
  --task-definition parakeet-api \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

4. **Set up Application Load Balancer (Optional)**

For production, add an ALB in front of the ECS service for:
- SSL/TLS termination
- Health checks
- Auto-scaling
- Multiple availability zones

### Option 2: Amazon EC2

1. **Launch EC2 Instance**
   - Choose instance type: t3.xlarge or larger (4 vCPU, 16GB RAM)
   - Configure security group to allow port 8000
   - Install Docker on the instance

2. **Deploy Container**

```bash
# SSH into EC2 instance
ssh -i your-key.pem ec2-user@your-instance-ip

# Install Docker
sudo yum update -y
sudo yum install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user

# Pull and run your image
docker pull <account-id>.dkr.ecr.us-east-1.amazonaws.com/parakeet-api:latest
docker run -d -p 8000:8000 --name parakeet-api <account-id>.dkr.ecr.us-east-1.amazonaws.com/parakeet-api:latest
```

### Option 3: AWS App Runner

Simplest option for containerized applications:

```bash
aws apprunner create-service \
  --service-name parakeet-api \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/parakeet-api:latest",
      "ImageRepositoryType": "ECR",
      "ImageConfiguration": {
        "Port": "8000"
      }
    },
    "AutoDeploymentsEnabled": true
  }' \
  --instance-configuration '{
    "Cpu": "4 vCPU",
    "Memory": "8 GB"
  }'
```

## Performance Considerations

### CPU vs GPU

Current setup uses CPU inference. For production with high throughput:

1. **GPU Support**: Create `Dockerfile.gpu` with CUDA support
2. **Use GPU-enabled EC2 instances**: g4dn.xlarge or larger
3. **Update NeMo models**: Use GPU-optimized model variants

### Scaling

- **Horizontal scaling**: Run multiple containers behind a load balancer
- **Vertical scaling**: Increase CPU/memory allocation
- **Model caching**: Use persistent volumes to avoid re-downloading models

### Cost Optimization

- **ECS Fargate Spot**: Save up to 70% on compute costs
- **Reserved Instances**: For predictable workloads
- **Auto-scaling**: Scale down during low-traffic periods

## Monitoring

### CloudWatch Logs

All container logs are sent to CloudWatch for:
- Error tracking
- Performance monitoring
- Debugging

### Health Checks

The `/health` endpoint provides basic health status. Consider adding:
- Model loading status
- Memory usage
- Request queue depth

### Metrics

Track key metrics:
- Request latency
- Transcription accuracy
- Error rates
- Resource utilization

## Security

### Best Practices

1. **Use IAM roles**: Don't hardcode AWS credentials
2. **Enable VPC**: Run containers in private subnets
3. **Use secrets manager**: For sensitive configuration
4. **Enable encryption**: For data at rest and in transit
5. **Regular updates**: Keep base images and dependencies updated

### Network Security

- Use security groups to restrict access
- Enable AWS WAF for API protection
- Use API Gateway for rate limiting and authentication

## Troubleshooting

### Container Won't Start

Check logs:
```bash
docker logs parakeet-api
```

Common issues:
- Insufficient memory (needs 4GB minimum)
- Port 8000 already in use
- Missing dependencies

### Model Download Fails

- Check internet connectivity
- Verify NGC/HuggingFace access
- Check disk space for model cache

### Slow Performance

- Increase CPU allocation
- Consider GPU instance
- Check for memory swapping
- Optimize chunk size in config

### Health Check Failing

- Verify port 8000 is accessible
- Check if models loaded successfully
- Review application logs for errors

## Support

For issues or questions:
- Check logs: `docker logs parakeet-api`
- Review documentation in `docs/`
- Check NeMo documentation: https://docs.nvidia.com/deeplearning/nemo/user-guide/docs/en/stable/

