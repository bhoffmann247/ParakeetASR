# Quick test script for Docker deployment (PowerShell)

Write-Host "=== Parakeet API Docker Test Script ===" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "[OK] Docker is running" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker is not running. Please start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}
Write-Host ""

# Build the image
Write-Host "[BUILD] Building Docker image..." -ForegroundColor Yellow
docker build -t parakeet-api .
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Build failed" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Image built successfully" -ForegroundColor Green
Write-Host ""

# Start the container
Write-Host "[START] Starting container with docker-compose..." -ForegroundColor Yellow
docker-compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to start container" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Container started" -ForegroundColor Green
Write-Host ""

# Wait for container to be healthy
Write-Host "[WAIT] Waiting for API to be ready (this may take 30-60 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

$maxRetries = 12
$retryCount = 0
$isHealthy = $false

while ($retryCount -lt $maxRetries) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Host "[OK] API is healthy!" -ForegroundColor Green
            $isHealthy = $true
            break
        }
    } catch {
        # Continue waiting
    }
    $retryCount++
    Write-Host "   Attempt $retryCount/$maxRetries..." -ForegroundColor Gray
    Start-Sleep -Seconds 5
}

if (-not $isHealthy) {
    Write-Host "[ERROR] API failed to become healthy. Check logs with: docker logs parakeet-api" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== Running API Tests ===" -ForegroundColor Cyan
Write-Host ""

# Test 1: Health check
Write-Host "[TEST 1] Testing health endpoint..." -ForegroundColor Yellow
try {
    $healthResponse = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
    Write-Host "   Response: $($healthResponse | ConvertTo-Json -Compress)" -ForegroundColor Gray
    if ($healthResponse.status -eq "healthy") {
        Write-Host "   [OK] Health check passed" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] Health check failed" -ForegroundColor Red
    }
} catch {
    Write-Host "   [FAIL] Health check failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 2: Models list
Write-Host "[TEST 2] Testing models endpoint..." -ForegroundColor Yellow
try {
    $modelsResponse = Invoke-RestMethod -Uri "http://localhost:8000/v1/models" -Method Get
    Write-Host "   Response: $($modelsResponse | ConvertTo-Json -Compress)" -ForegroundColor Gray
    if ($modelsResponse.data.id -contains "parakeet-tdt-0.6b-v2") {
        Write-Host "   [OK] Models endpoint passed" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] Models endpoint failed" -ForegroundColor Red
    }
} catch {
    Write-Host "   [FAIL] Models endpoint failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 3: Transcription (if test file exists)
$testFile = "tests/Input/ContactCenter/103046_1000780789-21-00-01.wav"
if (Test-Path $testFile) {
    Write-Host "[TEST 3] Testing transcription with diarization..." -ForegroundColor Yellow
    Write-Host "   (This will take 2-4 minutes on CPU...)" -ForegroundColor Gray
    
    try {
        # Use curl for multipart form data (simpler than PowerShell's approach)
        $curlOutput = curl.exe -s -X POST http://localhost:8000/v1/audio/transcriptions `
            -F "file=@$testFile" `
            -F "model=parakeet-tdt-0.6b-v2" `
            -F "response_format=json" `
            -F "enable_diarization=true"
        
        $transcriptionResponse = $curlOutput | ConvertFrom-Json
        
        if ($transcriptionResponse.text) {
            Write-Host "   [OK] Transcription passed" -ForegroundColor Green
            
            # Check for speaker labels
            if ($transcriptionResponse.text -match "Speaker") {
                Write-Host "   [OK] Diarization working (speakers detected)" -ForegroundColor Green
            } else {
                Write-Host "   [WARN] No speaker labels found" -ForegroundColor Yellow
            }
            
            # Save response for inspection
            $transcriptionResponse | ConvertTo-Json -Depth 10 | Out-File "test-transcription-result.json"
            Write-Host "   [INFO] Full response saved to: test-transcription-result.json" -ForegroundColor Gray
        } else {
            Write-Host "   [FAIL] Transcription failed" -ForegroundColor Red
        }
    } catch {
        Write-Host "   [FAIL] Transcription failed: $_" -ForegroundColor Red
    }
} else {
    Write-Host "[TEST 3] Skipping transcription test (test file not found: $testFile)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Test Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Container Status:" -ForegroundColor Yellow
docker ps --filter name=parakeet-api --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
Write-Host ""
Write-Host "Useful Commands:" -ForegroundColor Yellow
Write-Host "   View logs:        docker logs parakeet-api"
Write-Host "   Follow logs:      docker logs -f parakeet-api"
Write-Host "   Stop container:   docker-compose down"
Write-Host "   Restart:          docker-compose restart"
Write-Host ""
Write-Host "API is available at: http://localhost:8000" -ForegroundColor Green
Write-Host "   Health:           http://localhost:8000/health"
Write-Host "   Models:           http://localhost:8000/v1/models"
Write-Host "   Docs:             http://localhost:8000/docs"
Write-Host ""
