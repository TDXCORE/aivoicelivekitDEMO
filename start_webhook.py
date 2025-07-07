#!/usr/bin/env python3
"""
Script de inicio para el webhook receiver en Render
"""

import os
import logging
import uvicorn
from webhook_receiver import app

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("webhook_startup")

if __name__ == "__main__":
    # Configuración para Render
    port = int(os.getenv("PORT", "8000"))  # Render usa la variable PORT
    host = "0.0.0.0"
    
    logger.info(f"🚀 Starting Chatwoot Webhook Receiver on {host}:{port}")
    logger.info(f"📋 Environment: {os.getenv('RENDER', 'development')}")
    logger.info(f"🔑 Token configured: {'Yes' if os.getenv('CHATWOOT_WEBHOOK_TOKEN') else 'No'}")
    
    # Ejecutar con uvicorn
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )