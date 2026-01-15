# AWS Deployment Guide

## Prerequisites

- Docker image built: `docker build -t parakeet-api .`
- AWS CLI configured
- At least 8GB RAM, 4 vCPU recommended

---

## Option 1: AWS ECS (Recommended)

### 1. Push to ECR

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Create repository
aws ecr create-repository --repository-name parakeet-api --region us-east-1

# Tag and push
docker tag parakeet-api:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/parakeet-api:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/parakeet-api:latest
```

### 2. Create Task Definition

Save as `ecs-task.json`:

```json
{
  "family": "parakeet-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "4096",
  "memory": "8192",
  "containerDefinitions": [{
    "name": "parakeet-api",
    "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/parakeet-api:latest",
    "portMappings": [{"containerPort": 8000, "protocol": "tcp"}],
    "healthCheck": {
      "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
      "interval": 30,
      "timeout": 10,
      "retries": 3,
      "startPeriod": 60
    }
  }]
}
```

Register it:
```bash
aws ecs register-task-definition --cli-input-json file://ecs-task.json
```

### 3. Create Service

```bash
aws ecs create-service \
  --cluster your-cluster \
  --service-name parakeet-api \
  --task-definition parakeet-api \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

---

## Option 2: AWS EC2

### 1. Launch Instance

- Instance type: t3.xlarge or larger (4 vCPU, 16GB RAM)
- Security group: Allow port 8000
- Install Docker

### 2. Deploy

```bash
# SSH to instance
ssh -i key.pem ec2-user@instance-ip

# Install Docker
sudo yum update -y
sudo yum install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user

# Run container
docker run -d -p 8000:8000 --name parakeet-api \
  --memory=8g --cpus=4 \
  <account-id>.dkr.ecr.us-east-1.amazonaws.com/parakeet-api:latest
```

---

## Option 3: AWS App Runner (Simplest)

```bash
aws apprunner create-service \
  --service-name parakeet-api \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/parakeet-api:latest",
      "ImageRepositoryType": "ECR",
      "ImageConfiguration": {"Port": "8000"}
    }
  }' \
  --instance-configuration '{"Cpu": "4 vCPU", "Memory": "8 GB"}'
```

---

## Performance

### CPU vs GPU

Current setup uses CPU. For production:
- Use GPU instances (g4dn.xlarge+) for 50-100x faster processing
- Requires CUDA-enabled Docker image

### Scaling

- **Horizontal**: Multiple containers behind load balancer
- **Vertical**: Increase CPU/memory
- **Auto-scaling**: Based on CPU/memory metrics

---

## Monitoring

### Health Check
```bash
curl http://your-endpoint:8000/health
```

### Logs
```bash
# ECS
aws logs tail /ecs/parakeet-api --follow

# EC2
docker logs -f parakeet-api
```

### Key Metrics
- Request latency
- Error rates
- CPU/Memory usage
- Queue depth

---

## Security

- Use IAM roles (no hardcoded credentials)
- Run in private subnets with VPC
- Use AWS Secrets Manager for sensitive config
- Enable encryption at rest and in transit
- Regular security updates

---

## Troubleshooting

### Container won't start
```bash
docker logs parakeet-api
```

Common issues:
- Insufficient memory (needs 8GB)
- Port conflict
- Model download failure

### Slow performance
- Increase CPU allocation
- Use GPU instance
- Check memory swapping

### Health check failing
- Wait 2-3 minutes for model loading
- Check port 8000 accessibility
- Review application logs
