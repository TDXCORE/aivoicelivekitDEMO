#!/bin/bash
set -e

echo "Downloading LiveKit agent models..."
python agent.py download-files

echo "Starting TDX SDR Bot..."
python agent.py start