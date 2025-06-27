#!/usr/bin/env python3
"""
Startup script for TDX SDR Bot
Downloads models then starts the agent
"""

import subprocess
import sys

def main():
    print("Starting TDX SDR Bot (skipping model download for memory optimization)...")
    
    # Start agent directly without downloading models
    subprocess.run([
        sys.executable, "agent.py", "start"
    ])

if __name__ == "__main__":
    main()