#!/usr/bin/env python3
"""
Chatwoot Webhook Receiver
Recibe webhooks de contact_created y dispara llamadas salientes automáticamente
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Importar función de creación de llamadas
from create_outbound_call import create_outbound_call_from_webhook

# Cargar variables de entorno
load_dotenv(dotenv_path=".env.local")

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chatwoot_webhook")

# Crear app FastAPI
app = FastAPI(
    title="Chatwoot Webhook Receiver",
    description="Recibe webhooks de Chatwoot y dispara llamadas salientes automáticamente",
    version="1.0.0"
)

# Token de seguridad para webhooks
WEBHOOK_TOKEN = os.getenv("CHATWOOT_WEBHOOK_TOKEN", "default-secure-token-change-me")

@app.get("/")
async def root():
    """Endpoint de salud para verificar que el servidor esté funcionando"""
    return {
        "status": "active",
        "service": "Chatwoot Webhook Receiver",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Endpoint de health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/webhooks/chatwoot/{token}")
async def chatwoot_webhook(request: Request, token: str):
    """
    Endpoint principal para recibir webhooks de Chatwoot
    Filtra eventos contact_created de landing_page y dispara llamadas
    """
    try:
        # Validación de token en URL (método recomendado por Chatwoot)
        if token != WEBHOOK_TOKEN:
            logger.warning(f"Invalid webhook token in URL: {token[:10]}...")
            raise HTTPException(status_code=401, detail="Invalid webhook token")
        
        # Validación adicional por User-Agent (Chatwoot incluye esto)
        user_agent = request.headers.get("user-agent", "")
        if not user_agent.startswith("Chatwoot"):
            logger.warning(f"Suspicious request - User-Agent: {user_agent}")
            # No bloqueamos completamente, solo loggeamos para monitoreo
        
        # Obtener payload del webhook
        payload = await request.json()
        logger.info(f"Received webhook: {payload.get('event', 'unknown_event')}")
        
        # Validar que sea evento contact_created
        if payload.get("event") != "contact_created":
            logger.info(f"Ignoring non-contact_created event: {payload.get('event')}")
            return {"status": "ignored", "reason": "not contact_created event"}
        
        # Extraer datos del contacto
        contact_data = extract_contact_data(payload)
        
        # Validar que venga de landing_page
        if not is_from_landing_page(contact_data):
            logger.info(f"Ignoring contact not from landing_page: {contact_data.get('source')}")
            return {"status": "ignored", "reason": "not from landing_page"}
        
        # Validar que tenga teléfono
        if not contact_data.get("phone"):
            logger.error(f"Contact {contact_data.get('id')} has no phone number")
            return {"status": "error", "reason": "no phone number provided"}
        
        # Log de datos recibidos
        logger.info(f"Processing contact: {contact_data.get('name')} ({contact_data.get('phone')})")
        logger.info(f"Has email: {contact_data.get('has_email')}")
        
        # Crear llamada saliente asíncrona
        asyncio.create_task(create_outbound_call_from_webhook(contact_data))
        
        return {
            "status": "call_queued",
            "contact_id": contact_data.get("id"),
            "contact_name": contact_data.get("name"),
            "phone": contact_data.get("phone"),
            "has_email": contact_data.get("has_email"),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except json.JSONDecodeError:
        logger.error("Invalid JSON payload received")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        logger.error(f"Payload: {payload if 'payload' in locals() else 'N/A'}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

def extract_contact_data(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Extraer datos del contacto del payload del webhook"""
    
    # El payload del contact_created contiene directamente los datos del contacto
    custom_attributes = payload.get("custom_attributes", {})
    
    contact_data = {
        "id": payload.get("id"),
        "name": payload.get("name"),
        "email": payload.get("email"),
        "phone": payload.get("phone_number"),
        "custom_attributes": custom_attributes,
        "has_email": bool(payload.get("email")),
        "source": custom_attributes.get("source"),
        "account_id": payload.get("account", {}).get("id") if payload.get("account") else None
    }
    
    return contact_data

def is_from_landing_page(contact_data: Dict[str, Any]) -> bool:
    """Verificar si el contacto viene de la landing page"""
    return contact_data.get("source") == "landing_page"

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Manejador personalizado para 404"""
    return JSONResponse(
        status_code=404,
        content={"status": "error", "message": "Endpoint not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Manejador personalizado para errores internos"""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    
    # Configuración para desarrollo
    port = int(os.getenv("WEBHOOK_PORT", "8000"))
    host = os.getenv("WEBHOOK_HOST", "0.0.0.0")
    
    logger.info(f"Starting Chatwoot Webhook Receiver on {host}:{port}")
    logger.info(f"Webhook endpoint: http://{host}:{port}/webhooks/chatwoot")
    
    uvicorn.run(
        "webhook_receiver:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )