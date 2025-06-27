#!/usr/bin/env python3
"""
Startup script for TDX SDR Bot
Downloads models then starts the agent
"""

import subprocess
import sys

def main():
    print("Downloading LiveKit agent models...")
    
    # Download models
    result = subprocess.run([
        sys.executable, "agent.py", "download-files"
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Model download failed: {result.stderr}")
        sys.exit(1)
    
    print("Starting TDX SDR Bot...")
    
    # Start agent
    subprocess.run([
        sys.executable, "agent.py", "start"
    ])

if __name__ == "__main__":
    main()