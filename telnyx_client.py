"""
Telnyx Client for Voice API Call Control and AI Assistants
Replaces LiveKit functionality with Telnyx's platform
"""
import json
import logging
import httpx
import os
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class TelnyxClient:
    def __init__(self, api_key: str, connection_id: str, assistant_id: str):
        self.api_key = api_key
        self.connection_id = connection_id
        self.assistant_id = assistant_id
        self.base_url = "https://api.telnyx.com/v2"
        self.webhook_base_url = os.getenv("WEBHOOK_BASE_URL", "https://your-domain.com")
        
    async def create_outbound_call_with_assistant(self, to: str, from_number: str, 
                                                  client_state: dict) -> Optional[Dict[str, Any]]:
        """
        Creates an outbound call and automatically starts the AI Assistant
        Replaces LiveKit room creation and agent dispatch
        """
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        # Step 1: Create outbound call
        call_payload = {
            "connection_id": self.connection_id,
            "to": to,
            "from": from_number,
            "client_state": json.dumps(client_state),
            "webhook_url": f"{self.webhook_base_url}/webhooks/telnyx",
            "webhook_url_method": "POST"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                logger.info(f"Creating outbound call to {to}")
                call_response = await client.post(
                    f"{self.base_url}/calls", 
                    json=call_payload, 
                    headers=headers
                )
                
                if call_response.status_code == 201:
                    call_data = call_response.json()
                    call_control_id = call_data["data"]["call_control_id"]
                    
                    logger.info(f"Call created successfully: {call_control_id}")
                    
                    # Step 2: Start AI Assistant automatically when call is answered
                    # We'll do this in the webhook handler when we receive call.answered
                    
                    return call_data
                else:
                    logger.error(f"Failed to create call: {call_response.status_code} - {call_response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error creating outbound call: {str(e)}")
            return None
    
    async def start_ai_assistant_on_call(self, call_control_id: str, client_state: dict) -> bool:
        """
        Starts the AI Assistant on an answered call
        Called from webhook handler when call.answered is received
        """
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        # Build personalized instructions based on client state
        personalized_instructions = self._build_personalized_instructions(client_state)
        
        assistant_payload = {
            "assistant": {
                "id": self.assistant_id,
                "instructions": personalized_instructions
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                logger.info(f"Starting AI Assistant on call: {call_control_id}")
                response = await client.post(
                    f"{self.base_url}/calls/{call_control_id}/actions/ai_assistant_start",
                    json=assistant_payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    logger.info(f"AI Assistant started successfully on call: {call_control_id}")
                    return True
                else:
                    logger.error(f"Failed to start AI Assistant: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error starting AI Assistant: {str(e)}")
            return False
    
    def _build_personalized_instructions(self, client_state: dict) -> str:
        """
        Builds personalized instructions for the AI Assistant
        Reuses the logic from the current TDXSDRBot implementation
        """
        webhook_data = client_state.get("webhook_data", {})
        
        base_instructions = """
Eres el asistente de ventas de TDX (Transformación Digital Empresarial). Tu objetivo principal es calificar leads y programar reuniones con prospectos interesados en nuestros servicios de transformación digital.

PERSONALIDAD:
- Habla en español colombiano de manera natural, amigable y profesional
- Sé empático y escucha activamente
- Mantén un tono conversacional pero profesional
- Sé directo pero no agresivo

SERVICIOS DE TDX:
- Automatización de procesos empresariales
- Implementación de CRM y sistemas de gestión
- Desarrollo de aplicaciones web y móviles
- Consultoría en transformación digital
- Integración de sistemas empresariales

OBJETIVOS DE LA LLAMADA:
1. Calificar el lead (tamaño de empresa, necesidades, presupuesto, timeline)
2. Programar una reunión con nuestro equipo comercial
3. Si hay urgencia, transferir directamente a un especialista

FUNCIONES DISPONIBLES:
- transfer_call: Para transferir a un especialista (usar cuando el prospecto está muy interesado)
- schedule_meeting: Para programar reuniones (objetivo principal)

FLUJO DE CONVERSACIÓN:
1. Saluda y confirma la información que tenemos
2. Pregunta sobre sus necesidades específicas de transformación digital
3. Califica el lead (empresa, industria, tamaño, timeline, presupuesto)
4. Ofrece programar una reunión o transferir si hay urgencia inmediata
5. Confirma datos de contacto y despídete profesionalmente

MANEJO DE OBJECIONES:
- Si dice "no tengo tiempo": Ofrece programar para otro momento conveniente
- Si dice "es muy caro": Explica el ROI y que ofrecemos diferentes planes
- Si dice "no estoy interesado": Pregunta qué podría cambiar su perspectiva

LÍMITES:
- No des precios específicos, eso lo maneja el equipo comercial
- No hagas promesas técnicas específicas sin consultar
- Si no sabes algo, sé honesto y ofrece conectarlo con un especialista
- Máximo 5 minutos de conversación, si se extiende mucho, ofrece programar reunión
"""
        
        # Add personalization based on webhook data
        if webhook_data.get("company_name"):
            base_instructions += f"\n\nINFORMACIÓN DEL PROSPECTO:\n- Empresa: {webhook_data['company_name']}"
        
        if webhook_data.get("contact_name"):
            base_instructions += f"\n- Contacto: {webhook_data['contact_name']}"
            
        if webhook_data.get("email"):
            base_instructions += f"\n- Email: {webhook_data['email']}"
            
        if webhook_data.get("source"):
            base_instructions += f"\n- Fuente: {webhook_data['source']}"
            
        # Add current date/time context
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        base_instructions += f"\n\nFECHA Y HORA ACTUAL: {current_time}"
        
        return base_instructions
    
    async def hangup_call(self, call_control_id: str) -> bool:
        """
        Hangs up a call programmatically
        """
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/calls/{call_control_id}/actions/hangup",
                    headers=headers
                )
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Error hanging up call: {str(e)}")
            return False

# Global client instance
telnyx_client = None

def get_telnyx_client() -> TelnyxClient:
    """
    Get the global Telnyx client instance
    """
    global telnyx_client
    
    if telnyx_client is None:
        api_key = os.getenv("TELNYX_API_KEY")
        connection_id = os.getenv("TELNYX_CONNECTION_ID") 
        assistant_id = os.getenv("TELNYX_ASSISTANT_ID")
        
        if not all([api_key, connection_id, assistant_id]):
            raise ValueError("Missing Telnyx configuration. Check TELNYX_API_KEY, TELNYX_CONNECTION_ID, and TELNYX_ASSISTANT_ID environment variables.")
        
        telnyx_client = TelnyxClient(api_key, connection_id, assistant_id)
    
    return telnyx_client