#!/usr/bin/env python3
"""
Start the FastAPI server for transcription and diarization
"""

import uvicorn
from api import create_app

if __name__ == "__main__":
    print("=" * 60)
    print("Starting Parakeet Transcription API Server")
    print("=" * 60)
    print("\nServer will be available at: http://localhost:8000")
    print("API documentation: http://localhost:8000/docs")
    print("Health check: http://localhost:8000/health")
    print("\nPress Ctrl+C to stop the server\n")
    print("=" * 60)
    
    uvicorn.run(
        "api:create_app",
        factory=True,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
