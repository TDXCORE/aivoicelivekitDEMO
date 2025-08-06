#!/usr/bin/env python3
"""
Startup script for TDX SDR Bot
Starts both webhook receiver and voice agent in parallel
"""

import os
import logging
import threading
import subprocess
import sys
import time
import uvicorn
from src.webhooks.receiver import app

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("startup")

def start_voice_agent():
    """Iniciar el agente de voz en un hilo separado"""
    time.sleep(5)  # Esperar a que el webhook receiver esté listo
    logger.info("🤖 Starting Voice Agent...")
    
    try:
        # Note: Voice agent functionality will be implemented separately
        logger.info("Voice agent functionality placeholder - implement as needed")
    except Exception as e:
        logger.error(f"Error starting voice agent: {e}")

def start_webhook_receiver():
    """Iniciar el webhook receiver"""
    port = int(os.getenv("PORT", "8000"))
    host = "0.0.0.0"
    
    logger.info(f"🔗 Starting Chatwoot Webhook Receiver on {host}:{port}")
    logger.info(f"📋 Environment: {os.getenv('RENDER', 'production')}")
    logger.info(f"🔑 Token configured: {'Yes' if os.getenv('CHATWOOT_WEBHOOK_TOKEN') else 'No'}")
    logger.info(f"🧪 Testing system enabled: {'Yes' if os.getenv('TESTING_ENABLED', 'true').lower() == 'true' else 'No'}")
    
    # Ejecutar webhook receiver
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )

def main():
    print("🚀 Starting TDX SDR Bot - Webhook Receiver + Voice Agent...")
    
    # Iniciar agente de voz en hilo separado
    agent_thread = threading.Thread(target=start_voice_agent, daemon=True)
    agent_thread.start()
    logger.info("🎯 Voice agent thread started")
    
    # Iniciar webhook receiver en hilo principal (requerido por Render)
    start_webhook_receiver()

if __name__ == "__main__":
    main()