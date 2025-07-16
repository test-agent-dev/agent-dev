#!/usr/bin/env python3
"""
Web server launcher for TESTIA AI Agent
"""
import os
import sys
import uvicorn

# Add src to Python path
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/src')

# Import the app
from src.web.app import app

def run_web_server(host: str = "0.0.0.0", port: int = 8080):
    """Run the web server"""
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    run_web_server()
