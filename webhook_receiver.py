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

# Importar función de creación de llamadas (LiveKit - original)
from create_outbound_call import create_outbound_call_from_webhook
from microsoft_graph_client import graph_client

# Importar nueva integración con Telnyx
from telnyx_client import get_telnyx_client
from telnyx_webhook_handler import handle_telnyx_webhook
from telnyx_functions import handle_transfer_function, handle_schedule_function, handle_collect_email_function

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

# Feature flag para usar Telnyx en lugar de LiveKit
USE_TELNYX = os.getenv("USE_TELNYX_INSTEAD_OF_LIVEKIT", "false").lower() == "true"
logger.info(f"Telnyx integration enabled: {USE_TELNYX}")

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
        
        # Crear llamada saliente - elegir sistema basado en feature flag
        if USE_TELNYX:
            logger.info("Using Telnyx for outbound call")
            asyncio.create_task(create_telnyx_outbound_call(contact_data))
        else:
            logger.info("Using LiveKit for outbound call (legacy)")
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

async def create_telnyx_outbound_call(contact_data: Dict[str, Any]):
    """
    Crear llamada saliente usando Telnyx
    Nueva función que reemplaza la funcionalidad de LiveKit
    """
    try:
        telnyx_client = get_telnyx_client()
        
        # Preparar client_state con información del contacto
        client_state = {
            "chatwoot_contact_id": contact_data.get("id"),
            "webhook_data": contact_data,
            "source": "chatwoot_webhook",
            "created_at": datetime.now().isoformat()
        }
        
        # Obtener número de origen desde configuración
        from_number = os.getenv("TELNYX_OUTBOUND_NUMBER", "+13052131234")
        
        # Crear llamada con Telnyx
        result = await telnyx_client.create_outbound_call_with_assistant(
            to=contact_data.get("phone"),
            from_number=from_number,
            client_state=client_state
        )
        
        if result:
            call_control_id = result["data"]["call_control_id"]
            logger.info(f"Telnyx call created successfully: {call_control_id}")
        else:
            logger.error("Failed to create Telnyx call")
            
    except Exception as e:
        logger.error(f"Error creating Telnyx outbound call: {str(e)}")

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

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    logger.info("🔄 Shutting down webhook receiver...")
    try:
        await graph_client.close()
        logger.info("✅ Resources cleaned up successfully")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

# ============================================================================
# WHATSAPP BOT ENDPOINTS - AGREGADOS SIN MODIFICAR CODIGO EXISTENTE
# ============================================================================

# Importar handlers de WhatsApp
try:
    from whatsapp_webhook import whatsapp_webhook_handler
    from whatsapp_metrics import whatsapp_metrics
    WHATSAPP_ENABLED = os.getenv('WHATSAPP_BOT_ENABLED', 'false').lower() == 'true'
    logger.info(f"WhatsApp bot enabled: {WHATSAPP_ENABLED}")
except ImportError as e:
    logger.warning(f"WhatsApp modules not available: {e}")
    WHATSAPP_ENABLED = False

@app.route('/webhooks/whatsapp/<token>', methods=['POST'])
async def whatsapp_webhook_endpoint(token: str, request: Request):
    """Endpoint WhatsApp - completamente separado del voice system"""
    
    if not WHATSAPP_ENABLED:
        raise HTTPException(status_code=503, detail="WhatsApp bot service not enabled")
    
    try:
        # Procesar con handler completo
        result = await whatsapp_webhook_handler.handle_webhook(request)
        return result
    except Exception as e:
        logger.error(f"WhatsApp webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/health/whatsapp')
async def whatsapp_health_check():
    """Health check específico para WhatsApp bot"""
    
    if not WHATSAPP_ENABLED:
        return {
            'status': 'disabled',
            'service': 'whatsapp_bot',
            'message': 'WhatsApp bot service is not enabled'
        }
    
    try:
        # Obtener stats del handler
        handler_stats = await whatsapp_webhook_handler.get_handler_stats()
        daily_summary = await whatsapp_metrics.get_daily_summary()
        
        return {
            'status': 'healthy',
            'service': 'whatsapp_bot',
            'timestamp': datetime.now().isoformat(),
            'handler_stats': handler_stats,
            'daily_summary': daily_summary
        }
    except Exception as e:
        logger.error(f"WhatsApp health check error: {e}")
        return {
            'status': 'error',
            'service': 'whatsapp_bot',
            'error': str(e)
        }

@app.get('/admin/whatsapp/metrics')
async def get_whatsapp_metrics():
    """Endpoint para obtener métricas de WhatsApp"""
    
    if not WHATSAPP_ENABLED:
        raise HTTPException(status_code=503, detail="WhatsApp bot service not enabled")
    
    try:
        return {
            'daily_summary': await whatsapp_metrics.get_daily_summary(),
            'conversation_analytics': await whatsapp_metrics.get_conversation_analytics(),
            'performance_metrics': await whatsapp_metrics.get_performance_metrics()
        }
    except Exception as e:
        logger.error(f"Error getting WhatsApp metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/admin/whatsapp/cleanup')
async def cleanup_whatsapp_bots():
    """Endpoint para limpiar bots inactivos"""
    
    if not WHATSAPP_ENABLED:
        raise HTTPException(status_code=503, detail="WhatsApp bot service not enabled")
    
    try:
        cleaned_count = await whatsapp_webhook_handler.cleanup_inactive_bots()
        await whatsapp_metrics.cleanup_old_metrics()
        
        return {
            'status': 'success',
            'cleaned_bots': cleaned_count,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error cleaning up WhatsApp bots: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/admin/whatsapp/conversations/{conversation_id}')
async def get_whatsapp_conversation_status(conversation_id: int):
    """Obtener estado de una conversación específica"""
    
    if not WHATSAPP_ENABLED:
        raise HTTPException(status_code=503, detail="WhatsApp bot service not enabled")
    
    try:
        status = await whatsapp_webhook_handler.get_conversation_status(conversation_id)
        return status
    except Exception as e:
        logger.error(f"Error getting conversation status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# TELNYX INTEGRATION ENDPOINTS
# ============================================================================

@app.post("/webhooks/telnyx")
async def telnyx_webhook_endpoint(request: Request):
    """
    Endpoint principal para webhooks de Telnyx Voice API
    Maneja eventos del ciclo de vida de las llamadas y conversaciones
    """
    if not USE_TELNYX:
        raise HTTPException(status_code=503, detail="Telnyx integration not enabled")
    
    try:
        return await handle_telnyx_webhook(request)
    except Exception as e:
        logger.error(f"Telnyx webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhooks/telnyx/failover")
async def telnyx_webhook_failover(request: Request):
    """
    Endpoint de respaldo para webhooks de Telnyx
    """
    if not USE_TELNYX:
        raise HTTPException(status_code=503, detail="Telnyx integration not enabled")
    
    try:
        logger.info("Processing Telnyx webhook via failover endpoint")
        return await handle_telnyx_webhook(request)
    except Exception as e:
        logger.error(f"Telnyx failover webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Telnyx AI Assistant Custom Function Endpoints

@app.post("/telnyx/functions/transfer")
async def telnyx_transfer_function(request: Request):
    """
    Función personalizada para transferencias de llamada
    Llamada por el AI Assistant de Telnyx
    """
    if not USE_TELNYX:
        raise HTTPException(status_code=503, detail="Telnyx integration not enabled")
    
    try:
        return await handle_transfer_function(request)
    except Exception as e:
        logger.error(f"Telnyx transfer function error: {e}")
        return {
            "success": False,
            "message": "Error técnico en la transferencia. Te conectaré con nuestro equipo principal.",
            "action": "transfer_to_default"
        }

@app.post("/telnyx/functions/schedule")
async def telnyx_schedule_function(request: Request):
    """
    Función personalizada para programar reuniones
    Llamada por el AI Assistant de Telnyx
    """
    if not USE_TELNYX:
        raise HTTPException(status_code=503, detail="Telnyx integration not enabled")
    
    try:
        return await handle_schedule_function(request)
    except Exception as e:
        logger.error(f"Telnyx schedule function error: {e}")
        return {
            "success": False,
            "message": "Tengo un problema técnico para programar la reunión. ¿Te parece si te transfiero con nuestro equipo?",
            "action": "offer_transfer_on_error"
        }

@app.post("/telnyx/functions/collect_email")
async def telnyx_collect_email_function(request: Request):
    """
    Función personalizada para recolectar y validar emails
    Llamada por el AI Assistant de Telnyx
    """
    if not USE_TELNYX:
        raise HTTPException(status_code=503, detail="Telnyx integration not enabled")
    
    try:
        return await handle_collect_email_function(request)
    except Exception as e:
        logger.error(f"Telnyx collect email function error: {e}")
        return {
            "success": False,
            "message": "Tengo un problema técnico. ¿Podrías repetirme tu email?",
            "action": "technical_error"
        }

@app.get("/health/telnyx")
async def telnyx_health_check():
    """Health check específico para integración Telnyx"""
    
    if not USE_TELNYX:
        return {
            'status': 'disabled',
            'service': 'telnyx_integration',
            'message': 'Telnyx integration is not enabled'
        }
    
    try:
        # Verificar configuración de Telnyx
        telnyx_client = get_telnyx_client()
        
        return {
            'status': 'healthy',
            'service': 'telnyx_integration',
            'timestamp': datetime.now().isoformat(),
            'configuration': {
                'api_key_configured': bool(os.getenv('TELNYX_API_KEY')),
                'connection_id_configured': bool(os.getenv('TELNYX_CONNECTION_ID')),
                'assistant_id_configured': bool(os.getenv('TELNYX_ASSISTANT_ID')),
                'outbound_number_configured': bool(os.getenv('TELNYX_OUTBOUND_NUMBER'))
            }
        }
    except Exception as e:
        logger.error(f"Telnyx health check error: {e}")
        return {
            'status': 'error',
            'service': 'telnyx_integration',
            'error': str(e)
        }