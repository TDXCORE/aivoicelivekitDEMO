#!/usr/bin/env python3
"""
Script para capturar y debuggear webhooks reales de Chatwoot
"""

import json
import logging
from fastapi import FastAPI, Request
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("webhook-debug")

app = FastAPI()

@app.post("/debug/{token}")
async def debug_webhook(token: str, request: Request):
    """Capturar y mostrar datos del webhook"""
    try:
        # Obtener datos del webhook
        webhook_data = await request.json()
        
        logger.info("=" * 80)
        logger.info("🔍 REAL WEBHOOK DATA RECEIVED:")
        logger.info("=" * 80)
        logger.info(f"Token: {token}")
        logger.info(f"Headers: {dict(request.headers)}")
        logger.info(f"Full JSON data:")
        logger.info(json.dumps(webhook_data, indent=2, ensure_ascii=False))
        logger.info("=" * 80)
        
        # Analizar estructura específica
        logger.info("📊 STRUCTURE ANALYSIS:")
        logger.info(f"Event: {webhook_data.get('event')}")
        
        if 'message' in webhook_data:
            message = webhook_data['message']
            logger.info(f"Message ID: {message.get('id')}")
            logger.info(f"Message Type: {message.get('message_type')}")
            logger.info(f"Content: '{message.get('content')}'")
            logger.info(f"Created At: {message.get('created_at')}")
        
        if 'conversation' in webhook_data:
            conversation = webhook_data['conversation']
            logger.info(f"Conversation ID: {conversation.get('id')}")
            logger.info(f"Status: {conversation.get('status')}")
            
            if 'meta' in conversation and 'sender' in conversation['meta']:
                sender = conversation['meta']['sender']
                logger.info(f"Sender Name: {sender.get('name')}")
                logger.info(f"Sender Phone: {sender.get('phone_number')}")
                logger.info(f"Sender ID: {sender.get('id')}")
        
        logger.info("=" * 80)
        
        return {"status": "debug_received", "data_captured": True}
        
    except Exception as e:
        logger.error(f"Error processing debug webhook: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"status": "error", "message": str(e)}

@app.get("/")
async def root():
    return {"message": "Webhook Debug Server Running"}

if __name__ == "__main__":
    logger.info("🚀 Starting Webhook Debug Server...")
    logger.info("📱 Send your webhook to: http://localhost:8001/debug/{your_token}")
    uvicorn.run(app, host="0.0.0.0", port=8001)