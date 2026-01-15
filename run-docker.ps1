#!/usr/bin/env pwsh
# Quick start script for Parakeet API Docker container

param(
    [switch]$Stop,
    [switch]$Restart,
    [switch]$Logs,
    [switch]$Status,
    [switch]$Build
)

$ContainerName = "parakeet-api"
$ImageName = "parakeet-api"
$Port = "8000"

function Write-Info {
    param([string]$Text, [string]$Color = "Cyan")
    Write-Host $Text -ForegroundColor $Color
}

# Handle different commands
if ($Stop) {
    Write-Info "Stopping container..." "Yellow"
    docker stop $ContainerName 2>$null
    docker rm $ContainerName 2>$null
    Write-Info "[OK] Container stopped and removed" "Green"
    exit 0
}

if ($Logs) {
    Write-Info "Showing container logs (Ctrl+C to exit)..." "Yellow"
    docker logs -f $ContainerName
    exit 0
}

if ($Status) {
    Write-Info "Container Status:" "Yellow"
    docker ps -a --filter "name=$ContainerName" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    Write-Info "`nContainer Stats:" "Yellow"
    docker stats $ContainerName --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>$null
    
    Write-Info "`nHealth Check:" "Yellow"
    try {
        $health = Invoke-RestMethod -Uri "http://localhost:$Port/health" -UseBasicParsing -TimeoutSec 5
        Write-Info "Status: $($health.status)" "Green"
        Write-Info "Model: $($health.model_id)" "Green"
        Write-Info "Model Loaded: $($health.model_loaded)" "Green"
    } catch {
        Write-Info "Server not responding" "Red"
    }
    exit 0
}

if ($Build) {
    Write-Info "Building Docker image..." "Yellow"
    docker build -t $ImageName .
    if ($LASTEXITCODE -eq 0) {
        Write-Info "[OK] Build successful" "Green"
    } else {
        Write-Info "[ERROR] Build failed" "Red"
        exit 1
    }
    exit 0
}

if ($Restart) {
    Write-Info "Restarting container..." "Yellow"
    docker stop $ContainerName 2>$null
    docker rm $ContainerName 2>$null
}

# Default: Start container
Write-Info "Starting Parakeet API Docker Container" "Cyan"
Write-Info "==================================================" "Cyan"

# Check if container already exists
$existing = docker ps -a --filter "name=$ContainerName" --format "{{.Names}}" 2>$null

if ($existing -and -not $Restart) {
    $running = docker ps --filter "name=$ContainerName" --format "{{.Names}}" 2>$null
    
    if ($running) {
        Write-Info "[OK] Container is already running" "Green"
        Write-Info ""
        Write-Info "API URL: http://localhost:$Port" "Yellow"
        Write-Info "API Docs: http://localhost:$Port/docs" "Yellow"
        Write-Info "Health: http://localhost:$Port/health" "Yellow"
        Write-Info ""
        Write-Info "Commands:" "Yellow"
        Write-Info "  View logs:    .\run-docker.ps1 -Logs"
        Write-Info "  Check status: .\run-docker.ps1 -Status"
        Write-Info "  Restart:      .\run-docker.ps1 -Restart"
        Write-Info "  Stop:         .\run-docker.ps1 -Stop"
        exit 0
    } else {
        Write-Info "Starting existing container..." "Yellow"
        docker start $ContainerName
        Write-Info "[OK] Container started" "Green"
        exit 0
    }
}

# Check if image exists
$imageExists = docker images -q $ImageName 2>$null

if (-not $imageExists) {
    Write-Info "Image not found. Building..." "Yellow"
    docker build -t $ImageName .
    if ($LASTEXITCODE -ne 0) {
        Write-Info "[ERROR] Build failed" "Red"
        exit 1
    }
}

# Run container
Write-Info "Starting new container..." "Yellow"
docker run -d --name $ContainerName -p "${Port}:8000" $ImageName

if ($LASTEXITCODE -eq 0) {
    Write-Info "[OK] Container started successfully" "Green"
    Write-Info ""
    Write-Info "Waiting for server to be ready (2-3 minutes)..." "Yellow"
    Write-Info "The model needs to download and load on first run"
    Write-Info ""
    
    # Wait for health check
    $maxAttempts = 36
    $attempt = 0
    
    while ($attempt -lt $maxAttempts) {
        Start-Sleep -Seconds 5
        $attempt++
        
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$Port/health" -UseBasicParsing -TimeoutSec 3 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Info "[OK] Server is ready!" "Green"
                break
            }
        } catch {
            Write-Host "." -NoNewline
        }
        
        if ($attempt -eq $maxAttempts) {
            Write-Host ""
            Write-Info "[WARNING] Server is taking longer than expected" "Yellow"
            Write-Info "Check logs with: .\run-docker.ps1 -Logs" "Yellow"
        }
    }
    
    Write-Info ""
    Write-Info "==================================================" "Cyan"
    Write-Info "Parakeet API is running!" "Green"
    Write-Info "==================================================" "Cyan"
    Write-Info ""
    Write-Info "API URL: http://localhost:$Port" "Yellow"
    Write-Info "API Docs: http://localhost:$Port/docs" "Yellow"
    Write-Info "Health: http://localhost:$Port/health" "Yellow"
    Write-Info ""
    Write-Info "Quick Test:" "Yellow"
    Write-Info '  curl.exe -X POST http://localhost:8000/v1/audio/transcriptions \'
    Write-Info '    -F "file=@tests/Input/ContactCenter/103046_1000780789-21-00-01.wav" \'
    Write-Info '    -F "model=parakeet-tdt-0.6b-v2" \'
    Write-Info '    -F "response_format=json"'
    Write-Info ""
    Write-Info "Commands:" "Yellow"
    Write-Info "  View logs:    .\run-docker.ps1 -Logs"
    Write-Info "  Check status: .\run-docker.ps1 -Status"
    Write-Info "  Restart:      .\run-docker.ps1 -Restart"
    Write-Info "  Stop:         .\run-docker.ps1 -Stop"
    Write-Info ""
    Write-Info "Run full test suite: .\test-api.ps1 -SkipBuild -SkipStartup" "Yellow"
    Write-Info ""
} else {
    Write-Info "[ERROR] Failed to start container" "Red"
    exit 1
}
