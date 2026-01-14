#!/bin/bash
# Quick test script for Docker deployment

echo "=== Parakeet API Docker Test Script ==="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Build the image
echo "📦 Building Docker image..."
docker build -t parakeet-api . || exit 1
echo "✅ Image built successfully"
echo ""

# Start the container
echo "🚀 Starting container with docker-compose..."
docker-compose up -d || exit 1
echo "✅ Container started"
echo ""

# Wait for container to be healthy
echo "⏳ Waiting for API to be ready (this may take 30-60 seconds)..."
sleep 10

MAX_RETRIES=12
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ API is healthy!"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "   Attempt $RETRY_COUNT/$MAX_RETRIES..."
    sleep 5
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ API failed to become healthy. Check logs with: docker logs parakeet-api"
    exit 1
fi

echo ""
echo "=== Running API Tests ==="
echo ""

# Test 1: Health check
echo "1️⃣  Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
echo "   Response: $HEALTH_RESPONSE"
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo "   ✅ Health check passed"
else
    echo "   ❌ Health check failed"
fi
echo ""

# Test 2: Models list
echo "2️⃣  Testing models endpoint..."
MODELS_RESPONSE=$(curl -s http://localhost:8000/v1/models)
echo "   Response: $MODELS_RESPONSE"
if echo "$MODELS_RESPONSE" | grep -q "parakeet-tdt-0.6b-v2"; then
    echo "   ✅ Models endpoint passed"
else
    echo "   ❌ Models endpoint failed"
fi
echo ""

# Test 3: Transcription (if test file exists)
TEST_FILE="tests/Input/ContactCenter/103046_1000780789-21-00-01.wav"
if [ -f "$TEST_FILE" ]; then
    echo "3️⃣  Testing transcription with diarization..."
    echo "   (This will take 2-4 minutes on CPU...)"
    
    TRANSCRIPTION_RESPONSE=$(curl -s -X POST http://localhost:8000/v1/audio/transcriptions \
        -F "file=@$TEST_FILE" \
        -F "model=parakeet-tdt-0.6b-v2" \
        -F "response_format=json" \
        -F "enable_diarization=true")
    
    if echo "$TRANSCRIPTION_RESPONSE" | grep -q "text"; then
        echo "   ✅ Transcription passed"
        
        # Check for speaker labels
        if echo "$TRANSCRIPTION_RESPONSE" | grep -q "Speaker"; then
            echo "   ✅ Diarization working (speakers detected)"
        else
            echo "   ⚠️  No speaker labels found"
        fi
        
        # Save response for inspection
        echo "$TRANSCRIPTION_RESPONSE" | python -m json.tool > test-transcription-result.json 2>/dev/null
        echo "   📄 Full response saved to: test-transcription-result.json"
    else
        echo "   ❌ Transcription failed"
        echo "   Response: $TRANSCRIPTION_RESPONSE"
    fi
else
    echo "3️⃣  Skipping transcription test (test file not found: $TEST_FILE)"
fi

echo ""
echo "=== Test Complete ==="
echo ""
echo "📊 Container Status:"
docker ps --filter name=parakeet-api --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "📝 Useful Commands:"
echo "   View logs:        docker logs parakeet-api"
echo "   Follow logs:      docker logs -f parakeet-api"
echo "   Stop container:   docker-compose down"
echo "   Restart:          docker-compose restart"
echo ""
echo "🌐 API is available at: http://localhost:8000"
echo "   Health:           http://localhost:8000/health"
echo "   Models:           http://localhost:8000/v1/models"
echo "   Docs:             http://localhost:8000/docs"
echo ""
