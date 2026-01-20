#!/usr/bin/env pwsh
# Quick start script for Parakeet API Docker container

param(
    [switch]$Stop,
    [switch]$Restart,
    [switch]$Logs,
    [switch]$Status,
    [switch]$Build,
    [switch]$NoGPU  # Optional flag to disable GPU
)

$ContainerName = "parakeet-api"
$ImageName = "parakeet-api"
$Port = "90"

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
        $health = Invoke-RestMethod -Uri "http://localhost:$Port/" -UseBasicParsing -TimeoutSec 5
        Write-Info "Status: OK" "Green"
        Write-Info "Response: $health" "Green"
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

# Determine GPU usage
$useGPU = -not $NoGPU
$gpuAvailable = $false

if ($useGPU) {
    Write-Info "Checking for GPU support..." "Yellow"
    try {
        $gpuInfo = docker run --rm --gpus all nvidia/cuda:12.2.2-base-ubuntu22.04 nvidia-smi 2>&1
        if ($LASTEXITCODE -eq 0) {
            $gpuAvailable = $true
            Write-Info "[OK] GPU support detected - will use GPU acceleration" "Green"
        } else {
            Write-Info "[WARNING] GPU not available - will run on CPU (slower)" "Yellow"
            Write-Info "To suppress this check, use: .\run-docker.ps1 -NoGPU" "Yellow"
        }
    } catch {
        Write-Info "[WARNING] GPU not available - will run on CPU (slower)" "Yellow"
        Write-Info "To suppress this check, use: .\run-docker.ps1 -NoGPU" "Yellow"
    }
} else {
    Write-Info "GPU disabled by -NoGPU flag - will run on CPU" "Yellow"
}

# Run container
Write-Info "Starting new container..." "Yellow"

if ($useGPU -and $gpuAvailable) {
    Write-Info "Running with GPU acceleration (--gpus all)..." "Green"
    docker run -d --name $ContainerName --gpus all -p "${Port}:90" $ImageName
} elseif ($useGPU -and -not $gpuAvailable) {
    Write-Info "GPU requested but not available - running on CPU..." "Yellow"
    docker run -d --name $ContainerName -p "${Port}:90" $ImageName
} else {
    Write-Info "Running on CPU (GPU disabled)..." "Yellow"
    docker run -d --name $ContainerName -p "${Port}:90" $ImageName
}

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
            $response = Invoke-WebRequest -Uri "http://localhost:$Port/" -UseBasicParsing -TimeoutSec 3 -ErrorAction SilentlyContinue
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
    Write-Info ""
    if ($useGPU -and $gpuAvailable) {
        Write-Info "GPU Status: ENABLED (CUDA acceleration active)" "Green"
        Write-Info "Expected performance: 30-60s for 6-min audio" "Green"
    } else {
        Write-Info "GPU Status: DISABLED (Running on CPU)" "Yellow"
        Write-Info "Expected performance: 5-10 min for 6-min audio" "Yellow"
        Write-Info "For production use, GPU is required!" "Yellow"
    }
    Write-Info ""
    Write-Info "Quick Test:" "Yellow"
    Write-Info '  curl.exe -X POST http://localhost:90/transcriptions \'
    Write-Info '    -F "files=@tests/Input/ContactCenter/103046_1000780789-21-00-01.wav" \'
    Write-Info '    -F "batch_size=16" \'
    Write-Info '    -F "diarize=true"'
    Write-Info ""
    Write-Info "Commands:" "Yellow"
    Write-Info "  View logs:    .\run-docker.ps1 -Logs"
    Write-Info "  Check status: .\run-docker.ps1 -Status"
    Write-Info "  Restart:      .\run-docker.ps1 -Restart"
    Write-Info "  Stop:         .\run-docker.ps1 -Stop"
    Write-Info ""
    if (-not $gpuAvailable -and $useGPU) {
        Write-Info "Note: To run without GPU check, use: .\run-docker.ps1 -NoGPU" "Cyan"
    }
    Write-Info ""
} else {
    Write-Info "[ERROR] Failed to start container" "Red"
    exit 1
}
