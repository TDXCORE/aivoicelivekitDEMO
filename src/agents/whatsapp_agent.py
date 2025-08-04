import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
import requests

logger = logging.getLogger("whatsapp-agent")

class TDXWhatsAppAgentV2:
    """Agente de WhatsApp simplificado para TDX"""
    
    def __init__(self, contact_name: str, company_name: str, prospect_info: Dict[str, Any], conversation_id: int):
        self.contact_name = contact_name
        self.company_name = company_name
        self.prospect_info = prospect_info
        self.conversation_id = conversation_id
        self.session_start_time = datetime.now()
        self.conversation_log = []
        self.awaiting_response_type = None
        
        # Configuración de Chatwoot
        self.chatwoot_account_id = os.getenv('VITE_CHATWOOT_ACCOUNT_ID')
        self.chatwoot_api_token = os.getenv('VITE_CHATWOOT_API_TOKEN')
        
        logger.info(f"🔍 AGENT DEBUG - Account ID: {self.chatwoot_account_id}")
        logger.info(f"🔍 AGENT DEBUG - API Token configured: {bool(self.chatwoot_api_token)}")
        
        logger.info(f"WhatsApp agent initialized for {contact_name} - Conversation {conversation_id}")
    
    async def process_message(self, message_content: str) -> Optional[str]:
        """Procesar mensaje del usuario y generar respuesta"""
        try:
            # Log del mensaje del usuario
            self.conversation_log.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'user',
                'content': message_content
            })
            
            logger.info(f"Processing message from {self.contact_name}: {message_content[:50]}...")
            
            # Generar respuesta simple basada en el mensaje
            response = await self._generate_response(message_content.lower())
            
            if response:
                # Log de la respuesta del bot
                self.conversation_log.append({
                    'timestamp': datetime.now().isoformat(),
                    'type': 'bot',
                    'content': response
                })
                
                # Enviar respuesta a través de Chatwoot
                success = await self._send_chatwoot_response(response)
                
                if success:
                    logger.info(f"Response sent successfully to {self.contact_name}")
                    return response
                else:
                    logger.error(f"Failed to send response to {self.contact_name}")
                    return None
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing message for {self.contact_name}: {e}")
            return None
    
    async def _generate_response(self, message: str) -> str:
        """Generar respuesta basada en el mensaje del usuario"""
        
        # Respuestas simples basadas en palabras clave
        if any(word in message for word in ['hola', 'hello', 'hi', 'buenos', 'buenas']):
            return f"¡Hola {self.contact_name}! 👋 Soy Mati, asistente virtual de TDX. Vi que te registraste mostrando interés en nuestras soluciones de IA. ¿En qué puedo ayudarte hoy?"
        
        elif any(word in message for word in ['ia', 'inteligencia artificial', 'ai', 'artificial intelligence']):
            return f"Perfecto {self.contact_name}! 🚀 En TDX somos especialistas en IA empresarial. ¿Qué desafío específico tiene {self.company_name} que podrías resolver con IA? Por ejemplo: automatización de procesos, análisis de datos, chatbots, etc."
        
        elif any(word in message for word in ['precio', 'costo', 'presupuesto', 'cotizar']):
            return f"Te entiendo {self.contact_name}. Los precios varían según las necesidades específicas de {self.company_name}. Para darte un presupuesto preciso, necesito conocer más sobre tu proyecto. ¿Podrías contarme qué proceso quieren automatizar o mejorar?"
        
        elif any(word in message for word in ['reunion', 'llamada', 'demo', 'presentacion']):
            return f"¡Excelente idea {self.contact_name}! Me gustaría agendar una reunión contigo para mostrarte cómo nuestras soluciones de IA pueden transformar {self.company_name}. ¿Qué día de esta semana te viene mejor? ¿Mañana por la mañana o tarde?"
        
        elif any(word in message for word in ['gracias', 'thank', 'ok', 'perfecto', 'bien']):
            return f"¡De nada {self.contact_name}! 😊 Estoy aquí para ayudarte con cualquier duda sobre IA. ¿Hay algo más específico sobre las soluciones de TDX que te gustaría conocer?"
        
        else:
            # Respuesta general
            return f"Interesante {self.contact_name}. Para poder ayudarte mejor con {self.company_name}, ¿podrías contarme más detalles sobre lo que necesitas? Estoy aquí para encontrar la mejor solución de IA para tu empresa 🤖"
    
    async def _send_chatwoot_response(self, message: str) -> bool:
        """Enviar respuesta a través de la API de Chatwoot"""
        try:
            if not all([self.chatwoot_account_id, self.chatwoot_api_token]):
                logger.error("❌ Chatwoot credentials not configured")
                logger.error(f"Account ID: {self.chatwoot_account_id}")
                logger.error(f"API Token present: {bool(self.chatwoot_api_token)}")
                return False
            
            headers = {
                'Content-Type': 'application/json',
                'api_access_token': self.chatwoot_api_token
            }
            
            payload = {
                'content': message,
                'message_type': 'outgoing',
                'private': False
            }
            
            url = f"https://app.chatwoot.com/api/v1/accounts/{self.chatwoot_account_id}/conversations/{self.conversation_id}/messages"
            
            logger.info(f"🔍 SEND DEBUG - URL: {url}")
            logger.info(f"🔍 SEND DEBUG - Payload: {payload}")
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            logger.info(f"🔍 SEND DEBUG - Response status: {response.status_code}")
            logger.info(f"🔍 SEND DEBUG - Response text: {response.text}")
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Message sent successfully to conversation {self.conversation_id}")
                return True
            else:
                logger.error(f"❌ Chatwoot API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error sending Chatwoot response: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return False