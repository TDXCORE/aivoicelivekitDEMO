#!/usr/bin/env python3
"""
Startup script for TDX SDR Bot
Starts the webhook receiver to handle Chatwoot integrations
"""

import os
import logging
import uvicorn
from webhook_receiver import app

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("startup")

def main():
    print("🚀 Starting TDX SDR Bot Webhook Receiver...")
    
    # Configuración para Render
    port = int(os.getenv("PORT", "8000"))  # Render usa la variable PORT
    host = "0.0.0.0"
    
    logger.info(f"🔗 Starting Chatwoot Webhook Receiver on {host}:{port}")
    logger.info(f"📋 Environment: {os.getenv('RENDER', 'development')}")
    logger.info(f"🔑 Token configured: {'Yes' if os.getenv('CHATWOOT_WEBHOOK_TOKEN') else 'No'}")
    
    # Ejecutar webhook receiver con uvicorn
    # El agente se iniciará automáticamente cuando haya dispatch de LiveKit
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()