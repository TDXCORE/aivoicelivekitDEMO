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
# from create_outbound_call import create_outbound_call_from_webhook
from src.integrations.microsoft.microsoft_graph_client import graph_client

# Importar nueva integración con Telnyx
# from telnyx_client import get_telnyx_client
# from telnyx_webhook_handler import handle_telnyx_webhook
# from telnyx_functions import handle_transfer_function, handle_schedule_function, handle_collect_email_function

# Cargar variables de entorno
load_dotenv(dotenv_path=".env.local")

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chatwoot_webhook")

# Feature flag para crear conversaciones automáticas en Chatwoot
CREATE_WEBHOOK_CONVERSATIONS = os.getenv("CREATE_WEBHOOK_CONVERSATIONS_ENABLED", "true").lower() == "true"
logger.info(f"Webhook conversations creation enabled: {CREATE_WEBHOOK_CONVERSATIONS}")

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

# Feature flags para fallback inteligente
WHATSAPP_FALLBACK_ENABLED = os.getenv("WHATSAPP_FALLBACK_ENABLED", "true").lower() == "true"
CALL_TIMEOUT_SECONDS = int(os.getenv("TELNYX_CALL_TIMEOUT_SECONDS", "30"))
logger.info(f"WhatsApp fallback enabled: {WHATSAPP_FALLBACK_ENABLED}")
logger.info(f"Call timeout for fallback: {CALL_TIMEOUT_SECONDS}s")

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
    """Endpoint de health check con información de fallback"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "integrations": {
            "telnyx_enabled": USE_TELNYX,
            "whatsapp_enabled": WHATSAPP_ENABLED,
            "whatsapp_fallback_enabled": WHATSAPP_FALLBACK_ENABLED,
            "webhook_conversations_enabled": CREATE_WEBHOOK_CONVERSATIONS,
            "call_timeout_seconds": CALL_TIMEOUT_SECONDS
        },
        "environment_config": {
            "chatwoot_account_id": os.getenv('VITE_CHATWOOT_ACCOUNT_ID', 'NOT_SET'),
            "chatwoot_api_token": bool(os.getenv('VITE_CHATWOOT_API_TOKEN')),
            "whatsapp_inbox_id": os.getenv('CHATWOOT_WHATSAPP_INBOX_ID', 'NOT_SET'),
            "webhook_inbox_id": os.getenv('CHATWOOT_WEBHOOK_INBOX_ID', 'NOT_SET'),
            "whatsapp_bot_enabled": os.getenv('WHATSAPP_BOT_ENABLED', 'NOT_SET'),
            "bot_agent_id": os.getenv('CHATWOOT_BOT_AGENT_ID', 'NOT_SET'),
            "telnyx_outbound_number": bool(os.getenv('TELNYX_OUTBOUND_NUMBER'))
        },
        "fallback_config": {
            "chatwoot_account_id": bool(os.getenv('VITE_CHATWOOT_ACCOUNT_ID')),
            "chatwoot_api_token": bool(os.getenv('VITE_CHATWOOT_API_TOKEN')),
            "whatsapp_inbox_id": bool(os.getenv('CHATWOOT_WHATSAPP_INBOX_ID')),
            "telnyx_outbound_number": bool(os.getenv('TELNYX_OUTBOUND_NUMBER'))
        }
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
        logger.info(f"🔍 WEBHOOK DEBUG - Received webhook: {payload.get('event', 'unknown_event')}")
        logger.info(f"🔍 WEBHOOK DEBUG - Full payload keys: {list(payload.keys())}")
        
        # Validar que sea evento contact_created
        if payload.get("event") != "contact_created":
            logger.info(f"❌ Ignoring non-contact_created event: {payload.get('event')}")
            return {"status": "ignored", "reason": "not contact_created event"}
        
        # Extraer datos del contacto
        contact_data = extract_contact_data(payload)
        logger.info(f"🔍 CONTACT DEBUG - Extracted contact_data: {contact_data}")
        
        # Validar que venga de landing_page
        if not is_from_landing_page(contact_data):
            logger.info(f"❌ Ignoring contact not from landing_page. Source: '{contact_data.get('source')}', Custom attributes: {contact_data.get('custom_attributes')}")
            return {"status": "ignored", "reason": "not from landing_page"}
        
        # Validar que tenga teléfono
        if not contact_data.get("phone"):
            logger.error(f"Contact {contact_data.get('id')} has no phone number")
            return {"status": "error", "reason": "no phone number provided"}
        
        # Log de datos recibidos
        logger.info(f"Processing contact: {contact_data.get('name')} ({contact_data.get('phone')})")
        logger.info(f"Has email: {contact_data.get('has_email')}")
        
        # 🚀 NUEVA FUNCIONALIDAD: Enviar mensaje proactivo de WhatsApp INMEDIATAMENTE
        # Se ejecuta en paralelo con la llamada de voz para máxima eficiencia
        proactive_whatsapp_task = None
        logger.info(f"🔍 WHATSAPP DEBUG - WHATSAPP_ENABLED: {WHATSAPP_ENABLED}")
        if WHATSAPP_ENABLED:
            logger.info("🚀 Initiating proactive WhatsApp message...")
            logger.info(f"🚀 Contact data for WhatsApp: Phone={contact_data.get('phone')}, Name={contact_data.get('name')}")
            try:
                # Ejecutar mensaje proactivo de forma asíncrona (no bloqueante)
                proactive_whatsapp_task = asyncio.create_task(
                    send_proactive_whatsapp_message(contact_data)
                )
                logger.info("✅ Proactive WhatsApp message task created successfully")
            except Exception as e:
                logger.error(f"❌ Error creating proactive WhatsApp task: {e}")
                import traceback
                logger.error(f"❌ Traceback: {traceback.format_exc()}")
        else:
            logger.warning("⚠️ WhatsApp proactive messaging is DISABLED - check WHATSAPP_BOT_ENABLED environment variable")
        
        # 🆕 NUEVA FUNCIONALIDAD: Crear conversación automática en Chatwoot
        webhook_conversation_task = None
        if CREATE_WEBHOOK_CONVERSATIONS:
            logger.info("🆕 Iniciando creación de conversación automática en Chatwoot...")
            try:
                webhook_conversation_task = asyncio.create_task(
                    create_chatwoot_conversation_for_webhook(contact_data)
                )
                logger.info("✅ Tarea de conversación Chatwoot creada exitosamente")
            except Exception as e:
                logger.error(f"❌ Error creando tarea de conversación Chatwoot: {e}")
                import traceback
                logger.error(f"❌ Traceback: {traceback.format_exc()}")
        else:
            logger.info("⚠️ Creación de conversaciones Chatwoot está DESHABILITADA")

        # Crear llamada saliente - elegir sistema basado en feature flag
        if USE_TELNYX:
            logger.info("Using Telnyx for outbound call")
            asyncio.create_task(create_telnyx_outbound_call(contact_data))
        else:
            logger.info("Using LiveKit for outbound call (legacy)")
            asyncio.create_task(create_outbound_call_from_webhook(contact_data))
        
        # Esperar resultado del mensaje proactivo de WhatsApp si está habilitado
        proactive_whatsapp_result = None
        if proactive_whatsapp_task:
            try:
                # Esperar máximo 5 segundos por el resultado del mensaje proactivo
                proactive_whatsapp_result = await asyncio.wait_for(
                    proactive_whatsapp_task, timeout=5.0
                )
                logger.info(f"📱 Proactive WhatsApp result: {proactive_whatsapp_result.get('status')}")
            except asyncio.TimeoutError:
                logger.warning("⏰ Proactive WhatsApp message timeout (5s) - continuing with call")
                proactive_whatsapp_result = {"status": "timeout"}
            except Exception as e:
                logger.error(f"❌ Error waiting for proactive WhatsApp result: {e}")
                proactive_whatsapp_result = {"status": "error", "error": str(e)}
        
        # Esperar resultado de la conversación Chatwoot si está habilitada
        webhook_conversation_result = None
        if webhook_conversation_task:
            try:
                # Esperar máximo 3 segundos por el resultado de la conversación
                webhook_conversation_result = await asyncio.wait_for(
                    webhook_conversation_task, timeout=3.0
                )
                logger.info(f"🆕 Chatwoot conversation result: {webhook_conversation_result.get('success')}")
            except asyncio.TimeoutError:
                logger.warning("⏰ Chatwoot conversation timeout (3s) - continuing")
                webhook_conversation_result = {"success": False, "error": "timeout"}
            except Exception as e:
                logger.error(f"❌ Error waiting for Chatwoot conversation result: {e}")
                webhook_conversation_result = {"success": False, "error": str(e)}
        
        return {
            "status": "call_queued",
            "contact_id": contact_data.get("id"),
            "contact_name": contact_data.get("name"),
            "phone": contact_data.get("phone"),
            "has_email": contact_data.get("has_email"),
            "proactive_whatsapp": proactive_whatsapp_result,
            "chatwoot_conversation": webhook_conversation_result,
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
        "company_name": custom_attributes.get("company_name", ""),
        "account_id": payload.get("account", {}).get("id") if payload.get("account") else None
    }
    
    return contact_data

def is_from_landing_page(contact_data: Dict[str, Any]) -> bool:
    """Verificar si el contacto viene de la landing page"""
    return contact_data.get("source") == "landing_page"

async def create_telnyx_outbound_call(contact_data: Dict[str, Any]):
    """
    Crear llamada saliente usando Telnyx CON FALLBACK AUTOMÁTICO A WHATSAPP
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
            
            # NUEVO: Programar fallback automático a WhatsApp después de 30 segundos
            asyncio.create_task(schedule_whatsapp_fallback(contact_data, call_control_id))
            
            return {
                "status": "call_initiated",
                "call_control_id": call_control_id,
                "fallback_scheduled": True
            }
        else:
            logger.error("Failed to create Telnyx call - Triggering immediate WhatsApp fallback")
            # Si falla la llamada inmediatamente, activar WhatsApp fallback
            await trigger_whatsapp_fallback(contact_data, "call_creation_failed")
            return {
                "status": "call_failed_whatsapp_triggered",
                "fallback_reason": "call_creation_failed"
            }
            
    except Exception as e:
        logger.error(f"Error creating Telnyx outbound call: {str(e)}")
        # En caso de error, activar WhatsApp fallback
        await trigger_whatsapp_fallback(contact_data, f"call_error: {str(e)}")
        return {
            "status": "call_error_whatsapp_triggered",
            "error": str(e)
        }

async def schedule_whatsapp_fallback(contact_data: Dict[str, Any], call_control_id: str):
    """
    Programar fallback automático a WhatsApp después de timeout de llamada
    """
    try:
        # Timeout configurable para llamada (default 30 segundos)
        call_timeout = int(os.getenv("TELNYX_CALL_TIMEOUT_SECONDS", "30"))
        
        logger.info(f"Scheduling WhatsApp fallback for call {call_control_id} in {call_timeout}s")
        
        # Esperar timeout
        await asyncio.sleep(call_timeout)
        
        # Verificar si la llamada fue contestada (esto requeriría estado de llamada)
        # Por simplificación, asumimos que si llegamos aquí, la llamada no fue contestada
        
        logger.info(f"Call timeout reached for {call_control_id} - Triggering WhatsApp fallback")
        await trigger_whatsapp_fallback(contact_data, "call_timeout")
        
    except Exception as e:
        logger.error(f"Error in WhatsApp fallback scheduling: {e}")

async def send_proactive_whatsapp_message(contact_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    NUEVA FUNCIÓN: Enviar mensaje proactivo de WhatsApp inmediatamente cuando se recibe contact_created
    Esta función se ejecuta en paralelo con la llamada de voz
    """
    logger.info(f"🔍 PROACTIVE DEBUG - Function called with contact_data: {contact_data}")
    
    if not WHATSAPP_ENABLED:
        logger.warning("❌ WhatsApp proactive messaging not available - service disabled")
        return {"status": "whatsapp_disabled"}
    
    try:
        phone = contact_data.get("phone")
        contact_name = contact_data.get("name", "")
        
        logger.info(f"🔍 PROACTIVE DEBUG - Phone: {phone}, Name: {contact_name}")
        
        if not phone:
            logger.warning("❌ No phone number available for proactive WhatsApp message")
            return {"status": "no_phone_number"}
        
        logger.info(f"🚀 Sending proactive WhatsApp message to {contact_name} ({phone})")
        
        # Importar WhatsApp client
        from src.integrations.whatsapp_client import ChatwootWhatsAppClient
        whatsapp_client = ChatwootWhatsAppClient()
        
        # Enviar mensaje proactivo personalizado
        success = await whatsapp_client.send_proactive_greeting_message(
            phone_number=phone,
            contact_name=contact_name,
            contact_data=contact_data
        )
        
        if success:
            logger.info(f"✅ Proactive WhatsApp message sent successfully to {phone}")
            return {
                "status": "proactive_message_sent",
                "phone": phone,
                "contact_name": contact_name,
                "source": contact_data.get("source", "manual")
            }
        else:
            logger.error(f"❌ Failed to send proactive WhatsApp message to {phone}")
            return {
                "status": "proactive_message_failed",
                "phone": phone,
                "error": "Message sending failed"
            }
            
    except Exception as e:
        logger.error(f"❌ Error sending proactive WhatsApp message: {e}")
        return {
            "status": "proactive_message_error",
            "error": str(e)
        }

async def trigger_whatsapp_fallback(contact_data: Dict[str, Any], reason: str):
    """
    Activar fallback a WhatsApp via Chatwoot cuando la llamada falla
    """
    if not WHATSAPP_ENABLED:
        logger.warning("WhatsApp fallback not available - service disabled")
        return {"status": "fallback_unavailable"}
    
    try:
        phone = contact_data.get("phone")
        contact_name = contact_data.get("name", "")
        
        if not phone:
            logger.error("No phone number for WhatsApp fallback")
            return {"status": "no_phone_number"}
        
        logger.info(f"🚨 Triggering WhatsApp fallback for {contact_name} ({phone}) - Reason: {reason}")
        
        # Mensaje inicial personalizado según razón del fallback
        if reason == "call_timeout":
            initial_message = f"""¡Hola {contact_name}! 👋

Te llamé hace un momento pero no pude contactarte. Soy Mati, asistente virtual de TDX.

Vi que te registraste mostrando interés en nuestras soluciones de IA 🚀

¿Prefieres que conversemos por aquí sobre tu proyecto de transformación digital?

¿Qué desafío tecnológico específico tienes en tu empresa? 💡"""
        
        elif reason == "call_creation_failed":
            initial_message = f"""¡Hola {contact_name}! 👋

Soy Mati, asistente virtual de TDX. Intenté llamarte pero hubo un problema técnico.

Vi tu interés en nuestras soluciones de IA y quería contactarte inmediatamente 🚀

¿Qué desafío tecnológico específico tiene tu empresa que te llevó a consultar sobre IA? 💡"""
        
        else:
            initial_message = f"""¡Hola {contact_name}! 👋

Soy Mati, asistente virtual de TDX. Vi que te registraste mostrando interés en nuestras soluciones de IA.

¿Qué desafío tecnológico específico tiene tu empresa? 🚀"""
        
        # USAR CHATWOOT API PARA CREAR CONVERSACIÓN Y ENVIAR MENSAJE
        # Esto usa la integración existente de Chatwoot sin crear nueva conexión WhatsApp
        
        result = await create_chatwoot_whatsapp_conversation(phone, contact_data, initial_message)
        
        if result.get("success"):
            logger.info(f"✅ WhatsApp fallback triggered successfully for {phone}")
            return {
                "status": "whatsapp_fallback_triggered",
                "phone": phone,
                "conversation_id": result.get("conversation_id"),
                "reason": reason
            }
        else:
            logger.error(f"❌ WhatsApp fallback failed for {phone}")
            return {
                "status": "whatsapp_fallback_failed",
                "error": result.get("error", "unknown_error")
            }
        
    except Exception as e:
        logger.error(f"Error triggering WhatsApp fallback: {e}")
        return {"status": "fallback_error", "error": str(e)}

async def create_chatwoot_conversation_for_webhook(contact_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    🆕 NUEVA FUNCIÓN: Crear conversación automática en Chatwoot para contacto de webhook
    """
    try:
        logger.info(f"🆕 Creando conversación automática para contacto: {contact_data.get('name')} (ID: {contact_data.get('id')})")
        
        # Importar y usar la integración mejorada de Chatwoot
        from src.integrations.chatwoot.chatwoot_summary_integration import ChatwootSummaryIntegration
        
        # Obtener inbox ID específico para webhooks (watdxv3)
        webhook_inbox_id = os.getenv('CHATWOOT_WEBHOOK_INBOX_ID')
        if not webhook_inbox_id:
            logger.warning("CHATWOOT_WEBHOOK_INBOX_ID no configurado, usando inbox por defecto")
            webhook_inbox_id = None
        
        # Crear instancia de integración con inbox específico
        chatwoot_integration = ChatwootSummaryIntegration(inbox_id=webhook_inbox_id)
        
        # Crear conversación con reintentos automáticos
        result = chatwoot_integration.create_webhook_conversation_with_retry(contact_data)
        
        if result.get("success"):
            logger.info(f"✅ Conversación automática creada: ID {result.get('conversation_id')}")
            return {
                "success": True,
                "conversation_id": result.get("conversation_id"),
                "inbox_id": result.get("inbox_id"),
                "contact_id": result.get("contact_id"),
                "source": "webhook_automation"
            }
        else:
            logger.error(f"❌ Error creando conversación automática: {result.get('error')}")
            return {
                "success": False,
                "error": result.get("error"),
                "details": result.get("details", "Unknown error")
            }
            
    except Exception as e:
        logger.error(f"❌ Error en create_chatwoot_conversation_for_webhook: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "error": str(e),
            "source": "webhook_automation_exception"
        }

async def create_chatwoot_whatsapp_conversation(phone: str, contact_data: Dict[str, Any], message: str):
    """
    Crear conversación en Chatwoot WhatsApp inbox y enviar mensaje inicial
    Usa la integración existente de Chatwoot
    """
    try:
        import requests
        
        # Usar las credenciales existentes de Chatwoot
        account_id = os.getenv('VITE_CHATWOOT_ACCOUNT_ID')
        api_token = os.getenv('VITE_CHATWOOT_API_TOKEN')
        whatsapp_inbox_id = os.getenv('CHATWOOT_WHATSAPP_INBOX_ID')
        
        if not all([account_id, api_token, whatsapp_inbox_id]):
            logger.error("Missing Chatwoot configuration for WhatsApp fallback")
            return {"success": False, "error": "missing_config"}
        
        headers = {
            'Content-Type': 'application/json',
            'api_access_token': api_token
        }
        
        # Crear contacto en Chatwoot si no existe
        contact_payload = {
            "name": contact_data.get("name", "WhatsApp Contact"),
            "phone_number": phone,
            "email": contact_data.get("email"),
            "custom_attributes": {
                "source": "whatsapp_fallback",
                "original_source": contact_data.get("source", "webhook"),
                "fallback_reason": "voice_call_failed",
                "company_name": contact_data.get("company_name", ""),
                "created_via": "telnyx_fallback"
            }
        }
        
        # Crear conversación en WhatsApp inbox
        conversation_payload = {
            "source_id": phone,
            "inbox_id": whatsapp_inbox_id,
            "contact": contact_payload,
            "message": {
                "content": message,
                "message_type": "outgoing"
            }
        }
        
        # Llamada a API de Chatwoot
        response = requests.post(
            f"https://app.chatwoot.com/api/v1/accounts/{account_id}/conversations",
            headers=headers,
            json=conversation_payload,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            conversation_data = response.json()
            conversation_id = conversation_data.get("id")
            
            logger.info(f"✅ Chatwoot WhatsApp conversation created: {conversation_id}")
            return {
                "success": True,
                "conversation_id": conversation_id,
                "contact_id": conversation_data.get("meta", {}).get("contact", {}).get("id")
            }
        else:
            logger.error(f"❌ Chatwoot API error: {response.status_code} - {response.text}")
            return {"success": False, "error": f"api_error_{response.status_code}"}
        
    except Exception as e:
        logger.error(f"Error creating Chatwoot WhatsApp conversation: {e}")
        return {"success": False, "error": str(e)}

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
    from src.webhooks.whatsapp_handler import whatsapp_webhook_handler
    # from whatsapp_metrics import whatsapp_metrics
    WHATSAPP_ENABLED = os.getenv('WHATSAPP_BOT_ENABLED', 'false').lower() == 'true'
    logger.info(f"WhatsApp bot enabled: {WHATSAPP_ENABLED}")
except ImportError as e:
    logger.warning(f"WhatsApp modules not available: {e}")
    WHATSAPP_ENABLED = False

@app.post('/webhooks/whatsapp/{token}')
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

# ============================================================================
# SERVIDOR PRINCIPAL
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Configuración del servidor
    port = int(os.getenv("WEBHOOK_PORT", 8000))
    host = os.getenv("WEBHOOK_HOST", "0.0.0.0")
    
    logger.info(f"🚀 Starting TDX AI Voice + WhatsApp Bot Service on {host}:{port}")
    logger.info(f"📱 WhatsApp webhook: http://{host}:{port}/webhooks/whatsapp/<token>")
    logger.info(f"📞 Voice webhook: http://{host}:{port}/webhooks/chatwoot/<token>")
    logger.info(f"💚 Health check: http://{host}:{port}/health")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )