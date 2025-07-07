#!/usr/bin/env python3
"""
Script para ejecutar webhook receiver y agente en paralelo
"""

import os
import asyncio
import logging
import multiprocessing
import uvicorn
from webhook_receiver import app

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("combined_startup")

def start_webhook():
    """Iniciar webhook receiver"""
    port = int(os.getenv("PORT", "8000"))
    logger.info(f"🔗 Starting Webhook Receiver on port {port}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )

def start_agent():
    """Iniciar agente de voz"""
    logger.info(f"🤖 Starting Voice Agent")
    os.system("python agent.py")

if __name__ == "__main__":
    logger.info("🚀 Starting Combined Services")
    
    # Ejecutar webhook en proceso principal (Render necesita esto)
    # El agente se ejecutará cuando haya dispatch
    start_webhook()