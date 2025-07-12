"""
Telnyx Webhook Handler
Handles all webhook events from Telnyx Voice API and AI Assistants
"""
import json
import logging
import hashlib
import hmac
import base64
from typing import Dict, Any
from fastapi import Request, HTTPException
from datetime import datetime
import openai
import os

from telnyx_client import get_telnyx_client
from chatwoot_summary_integration import send_summary_to_chatwoot
# Note: WhatsApp message will be sent via Chatwoot webhook trigger
# from whatsapp_client import send_whatsapp_message

logger = logging.getLogger(__name__)

# Store processed webhook IDs to prevent duplicates
processed_webhooks = set()

async def verify_telnyx_signature(request: Request) -> bool:
    """
    Verify Telnyx webhook signature using Ed25519
    """
    try:
        signature = request.headers.get("X-Telnyx-Signature-Ed25519")
        timestamp = request.headers.get("X-Telnyx-Signature-Timestamp")
        
        if not signature or not timestamp:
            logger.warning("Missing Telnyx signature headers")
            return False
            
        # For now, return True. In production, implement proper Ed25519 verification
        # according to Telnyx documentation
        return True
        
    except Exception as e:
        logger.error(f"Error verifying Telnyx signature: {str(e)}")
        return False

async def handle_telnyx_webhook(request: Request) -> Dict[str, str]:
    """
    Main Telnyx webhook handler
    Routes different event types to appropriate handlers
    """
    # Verify signature
    if not await verify_telnyx_signature(request):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    try:
        payload = await request.json()
        
        # Prevent duplicate processing
        webhook_id = payload.get("id")
        if webhook_id in processed_webhooks:
            logger.info(f"Webhook {webhook_id} already processed, skipping")
            return {"status": "duplicate"}
        
        processed_webhooks.add(webhook_id)
        
        # Extract event details
        event_type = payload["data"]["event_type"]
        call_control_id = payload["data"]["call_control_id"]
        
        logger.info(f"Received Telnyx webhook: {event_type} for call {call_control_id}")
        
        # Route to appropriate handler
        if event_type == "call.answered":
            await handle_call_answered(payload)
        elif event_type == "call.conversation.ended":
            await handle_conversation_ended(payload)
        elif event_type == "call.hangup":
            await handle_call_hangup(payload)
        elif event_type == "call.conversation_insights.generated":
            await handle_conversation_insights(payload)
        else:
            logger.info(f"Unhandled event type: {event_type}")
        
        return {"status": "received"}
        
    except Exception as e:
        logger.error(f"Error processing Telnyx webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def handle_call_answered(payload: Dict[str, Any]):
    """
    Handle call.answered event
    Start the AI Assistant when call is answered
    """
    try:
        call_control_id = payload["data"]["call_control_id"]
        client_state_str = payload["data"].get("client_state", "{}")
        client_state = json.loads(client_state_str)
        
        logger.info(f"Call answered: {call_control_id}")
        
        # Start AI Assistant on the answered call
        telnyx_client = get_telnyx_client()
        success = await telnyx_client.start_ai_assistant_on_call(call_control_id, client_state)
        
        if success:
            logger.info(f"AI Assistant started successfully on call {call_control_id}")
        else:
            logger.error(f"Failed to start AI Assistant on call {call_control_id}")
            
    except Exception as e:
        logger.error(f"Error handling call answered: {str(e)}")

async def handle_conversation_ended(payload: Dict[str, Any]):
    """
    Handle call.conversation.ended event
    Extract transcript and send summary to Chatwoot
    """
    try:
        call_control_id = payload["data"]["call_control_id"]
        client_state_str = payload["data"].get("client_state", "{}")
        client_state = json.loads(client_state_str)
        
        # Extract conversation data
        conversation_data = payload["data"].get("conversation", {})
        transcript = conversation_data.get("transcript", "")
        duration = conversation_data.get("duration", 0)
        
        logger.info(f"Conversation ended for call {call_control_id}, duration: {duration}s")
        
        if not transcript:
            logger.warning(f"No transcript available for call {call_control_id}")
            transcript = "Conversación completada sin transcript disponible."
        
        # Generate conversation summary using OpenAI
        summary = await generate_conversation_summary(transcript, client_state)
        
        # Send summary to Chatwoot (reuse existing integration)
        chatwoot_contact_id = client_state.get("chatwoot_contact_id")
        if chatwoot_contact_id:
            await send_summary_to_chatwoot(
                contact_id=chatwoot_contact_id,
                summary=summary,
                call_duration=duration,
                outcome="completed",
                phone_number=client_state.get("webhook_data", {}).get("phone_number", ""),
                agent_name="Telnyx AI Assistant"
            )
            logger.info(f"Summary sent to Chatwoot for contact {chatwoot_contact_id}")
        else:
            logger.warning("No Chatwoot contact ID found in client state")
            
    except Exception as e:
        logger.error(f"Error handling conversation ended: {str(e)}")

async def handle_call_hangup(payload: Dict[str, Any]):
    """
    Handle call.hangup event
    Trigger WhatsApp fallback if call was not answered
    """
    try:
        call_control_id = payload["data"]["call_control_id"]
        hangup_cause = payload["data"].get("hangup_cause", "")
        client_state_str = payload["data"].get("client_state", "{}")
        client_state = json.loads(client_state_str)
        
        logger.info(f"Call hangup: {call_control_id}, cause: {hangup_cause}")
        
        # Check if call was not answered
        no_answer_causes = ["no_answer", "timeout", "busy", "call_rejected", "user_busy"]
        
        if hangup_cause in no_answer_causes:
            logger.info(f"Call not answered ({hangup_cause}), triggering WhatsApp fallback")
            await trigger_whatsapp_followup(client_state)
        else:
            logger.info(f"Call ended normally with cause: {hangup_cause}")
            
    except Exception as e:
        logger.error(f"Error handling call hangup: {str(e)}")

async def handle_conversation_insights(payload: Dict[str, Any]):
    """
    Handle call.conversation_insights.generated event
    Process any additional insights from Telnyx AI
    """
    try:
        call_control_id = payload["data"]["call_control_id"]
        insights = payload["data"].get("insights", {})
        
        logger.info(f"Conversation insights generated for call {call_control_id}")
        
        # Log insights for now, could be used for analytics
        if insights:
            logger.info(f"Insights: {json.dumps(insights, indent=2)}")
            
    except Exception as e:
        logger.error(f"Error handling conversation insights: {str(e)}")

async def generate_conversation_summary(transcript: str, client_state: dict) -> str:
    """
    Generate a conversation summary using OpenAI
    Reuses the pattern from the existing LiveKit implementation
    """
    try:
        client = openai.AsyncOpenAI()
        
        webhook_data = client_state.get("webhook_data", {})
        company_name = webhook_data.get("company_name", "la empresa")
        contact_name = webhook_data.get("contact_name", "el prospecto")
        
        prompt = f"""
Eres un asistente especializado en generar resúmenes ejecutivos de conversaciones de ventas para TDX.

TRANSCRIPT DE LA CONVERSACIÓN:
{transcript}

INFORMACIÓN DEL PROSPECTO:
- Empresa: {company_name}
- Contacto: {contact_name}
- Fuente: {webhook_data.get('source', 'desconocida')}

Genera un resumen ejecutivo profesional en español que incluya:

1. **INFORMACIÓN DEL PROSPECTO**: Empresa, cargo, industria si se mencionó
2. **NECESIDADES IDENTIFICADAS**: Qué problemas o necesidades expresó
3. **NIVEL DE INTERÉS**: Alto/Medio/Bajo con justificación
4. **PRÓXIMOS PASOS**: Qué se acordó hacer (reunión, llamada, etc.)
5. **NOTAS IMPORTANTES**: Cualquier información relevante adicional

El resumen debe ser conciso, profesional y orientado a acción comercial.
"""
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un asistente especializado en generar resúmenes ejecutivos de conversaciones de ventas."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        summary = response.choices[0].message.content
        return summary
        
    except Exception as e:
        logger.error(f"Error generating conversation summary: {str(e)}")
        return f"Conversación completada con {contact_name} de {company_name}. Transcript disponible para revisión."

async def trigger_whatsapp_followup(client_state: dict):
    """
    Trigger WhatsApp follow-up message when call is not answered
    Reuses existing WhatsApp infrastructure
    """
    try:
        chatwoot_contact_id = client_state.get("chatwoot_contact_id")
        webhook_data = client_state.get("webhook_data", {})
        contact_name = webhook_data.get("contact_name", "")
        company_name = webhook_data.get("company_name", "")
        
        if not chatwoot_contact_id:
            logger.error("No Chatwoot contact ID for WhatsApp followup")
            return
        
        # Create personalized WhatsApp message
        if contact_name and company_name:
            message = f"Hola {contact_name} 👋\n\nTratamos de contactarte por teléfono para conversar sobre las soluciones de transformación digital para {company_name}.\n\n¿Te gustaría programar una reunión para otro momento? Puedo ayudarte a encontrar el horario perfecto 📅"
        elif contact_name:
            message = f"Hola {contact_name} 👋\n\nTratamos de contactarte por teléfono. ¿Te gustaría programar una reunión para conversar sobre nuestras soluciones de transformación digital? 📞✨"
        else:
            message = "Hola 👋\n\nTratamos de contactarte por teléfono. ¿Te gustaría programar una reunión para conversar sobre nuestras soluciones de transformación digital? 📞✨"
        
        # Send WhatsApp message via Chatwoot API (will trigger existing WhatsApp bot)
        await send_whatsapp_via_chatwoot(chatwoot_contact_id, message)
        
        logger.info(f"WhatsApp followup sent to contact {chatwoot_contact_id}")
        
    except Exception as e:
        logger.error(f"Error sending WhatsApp followup: {str(e)}")

async def send_whatsapp_via_chatwoot(contact_id: int, message: str):
    """
    Send WhatsApp message via Chatwoot API
    This will trigger the existing WhatsApp bot infrastructure
    """
    try:
        import httpx
        
        # Get Chatwoot credentials
        account_id = os.getenv("CHATWOOT_ACCOUNT_ID")
        api_token = os.getenv("CHATWOOT_API_TOKEN")
        
        if not account_id or not api_token:
            logger.error("Missing Chatwoot credentials for WhatsApp followup")
            return
        
        # First, get the contact to find existing WhatsApp conversation
        headers = {"api_access_token": api_token}
        
        async with httpx.AsyncClient() as client:
            # Get contact conversations
            contact_url = f"https://app.chatwoot.com/api/v1/accounts/{account_id}/contacts/{contact_id}/conversations"
            response = await client.get(contact_url, headers=headers)
            
            if response.status_code == 200:
                conversations = response.json().get("payload", [])
                
                # Look for WhatsApp conversation or create new one
                whatsapp_conversation = None
                for conv in conversations:
                    if conv.get("channel") == "Channel::Whatsapp":
                        whatsapp_conversation = conv
                        break
                
                if whatsapp_conversation:
                    # Send message to existing conversation
                    conv_id = whatsapp_conversation["id"]
                    message_url = f"https://app.chatwoot.com/api/v1/accounts/{account_id}/conversations/{conv_id}/messages"
                    
                    message_payload = {
                        "content": message,
                        "message_type": "outgoing"
                    }
                    
                    message_response = await client.post(message_url, json=message_payload, headers=headers)
                    
                    if message_response.status_code == 200:
                        logger.info(f"WhatsApp message sent successfully to conversation {conv_id}")
                    else:
                        logger.error(f"Failed to send WhatsApp message: {message_response.status_code}")
                else:
                    logger.warning(f"No WhatsApp conversation found for contact {contact_id}")
            else:
                logger.error(f"Failed to get contact conversations: {response.status_code}")
                
    except Exception as e:
        logger.error(f"Error sending WhatsApp via Chatwoot: {str(e)}")

# Cleanup old processed webhooks periodically (keep last 1000)
def cleanup_processed_webhooks():
    """
    Clean up old processed webhook IDs to prevent memory issues
    """
    global processed_webhooks
    if len(processed_webhooks) > 1000:
        processed_webhooks = set(list(processed_webhooks)[-500:])
        logger.info("Cleaned up old processed webhook IDs")