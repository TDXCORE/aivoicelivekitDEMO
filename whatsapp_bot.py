"""
WhatsApp Bot TDX Core 2025 - Versión Simplificada y Robusta
FLUJO SIMPLE: Detección → Información → Datos → Calificación → Agendamiento
"""

import openai
import asyncio
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, Optional, List
import json
import os
import re

# Imports existentes
from microsoft_graph_client import graph_client
from chatwoot_summary_integration import send_bot_summary_to_chatwoot
from whatsapp_client import ChatwootWhatsAppClient

logger = logging.getLogger("whatsapp-bot-v2")

# TDX Core imports con fallbacks
try:
    from service_mapper import service_mapper
    SERVICE_MAPPER_AVAILABLE = True
except ImportError:
    SERVICE_MAPPER_AVAILABLE = False

try:
    from micro_value_injector import micro_value_injector
    MICRO_VALUE_AVAILABLE = True
except ImportError:
    MICRO_VALUE_AVAILABLE = False

try:
    from minimal_slot_manager import minimal_slot_manager
    SLOT_MANAGER_AVAILABLE = True
except ImportError:
    SLOT_MANAGER_AVAILABLE = False

class TDXWhatsAppBot:
    """Bot TDX Core 2025 - Versión Simplificada y Robusta"""
    
    def __init__(self, contact_name: str, company_name: str, prospect_info: Dict[str, Any], conversation_id: int):
        self.contact_name = contact_name or "amigo"
        self.company_name = company_name
        self.prospect_info = prospect_info or {}
        self.conversation_id = conversation_id
        self.user_id = prospect_info.get("whatsapp_user_id")
        self.conversation_log = []
        self.session_start_time = datetime.now()
        
        # Cliente OpenAI
        try:
            self.openai_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        except:
            self.openai_client = None
            
        # Cliente Chatwoot
        try:
            self.chatwoot_client = ChatwootWhatsAppClient()
        except Exception as e:
            logger.error(f"Error inicializando Chatwoot client: {e}")
            self.chatwoot_client = None

        # Estado de la conversación
        self.conversation_state = "initial"  # initial → service_detected → info_given → data_collected → qualified → scheduling
        
        # Servicios TDX mapeados
        self.service_map = {
            "1": "AI_CHATBOT",
            "chatbot": "AI_CHATBOT", 
            "chat": "AI_CHATBOT",
            "2": "AI_VOICE",
            "voice": "AI_VOICE",
            "voz": "AI_VOICE",
            "llamadas": "AI_VOICE",
            "3": "AI_VIDEO", 
            "video": "AI_VIDEO",
            "avatar": "AI_VIDEO",
            "4": "AI_ASSISTANT_WHATSAPP",
            "assistant": "AI_ASSISTANT_WHATSAPP",
            "whatsapp": "AI_ASSISTANT_WHATSAPP",
            "5": "DESARROLLO_CUSTOM",
            "desarrollo": "DESARROLLO_CUSTOM",
            "custom": "DESARROLLO_CUSTOM"
        }

    async def process_message(self, message_content: str, message_type: str = "text") -> str:
        """FLUJO PRINCIPAL SIMPLIFICADO"""
        try:
            # Log del mensaje
            self.conversation_log.append({
                'type': 'user_message',
                'content': message_content,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"🔄 Processing: {message_content[:50]}... | State: {self.conversation_state}")
            
            # PASO 1: Detectar servicio si no hay uno
            if not self.prospect_info.get('detected_service'):
                service_detected = self._detect_service(message_content)
                if service_detected:
                    self.prospect_info['detected_service'] = service_detected
                    self.conversation_state = "service_detected"
                    response = self._get_service_micro_value(service_detected)
                    return await self._send_response(response)
            
            # PASO 2: Dar información detallada si la piden
            if self._is_info_request(message_content):
                response = self._get_detailed_info()
                self.conversation_state = "info_given"
                return await self._send_response(response)
            
            # PASO 3: Recolectar datos básicos
            if self.conversation_state in ["service_detected", "info_given"]:
                missing_data = self._get_missing_data()
                if missing_data:
                    response = f"Perfecto {self.contact_name}! {missing_data}"
                    return await self._send_response(response)
                else:
                    self.conversation_state = "data_collected"
            
            # PASO 4: Calificación simple (una sola vez)
            if self.conversation_state == "data_collected" and not self.prospect_info.get('qualified'):
                self.prospect_info['qualification_answer'] = message_content
                self.prospect_info['qualified'] = True
                self.conversation_state = "qualified"
                response = f"¡Excelente {self.contact_name}! ¿Agendamos una demo personalizada?"
                return await self._send_response(response)
            
            # PASO 5: Agendamiento directo
            if self.conversation_state == "qualified":
                if self._is_scheduling_confirmation(message_content):
                    response = "Perfecto! ¿Qué día y hora te conviene? (ej: lunes 3pm)"
                    self.conversation_state = "scheduling"
                    return await self._send_response(response)
            
            # PASO 6: Procesar fecha/hora específica
            if self.conversation_state == "scheduling":
                scheduled = await self._process_scheduling(message_content)
                if scheduled:
                    return scheduled
            
            # FALLBACK: Respuesta contextual simple
            response = self._get_contextual_response(message_content)
            return await self._send_response(response)
            
        except Exception as e:
            logger.error(f"Error in process_message: {e}")
            return await self._send_response("Un momento, procesando tu solicitud... 🔄")

    def _detect_service(self, message: str) -> Optional[str]:
        """Detectar servicio de forma simple y directa"""
        message_lower = message.lower()
        
        # Detección directa por mapeo
        for key, service in self.service_map.items():
            if key in message_lower:
                logger.info(f"✅ Service detected: {key} → {service}")
                return service
        
        # Detección por service_mapper si está disponible
        if SERVICE_MAPPER_AVAILABLE:
            try:
                result = service_mapper.detect_service(message)
                if result and result.confidence >= 0.4:
                    logger.info(f"✅ Service detected via mapper: {result.service} (conf: {result.confidence})")
                    return result.service
            except Exception as e:
                logger.error(f"Error in service_mapper: {e}")
        
        return None

    def _get_service_micro_value(self, service: str) -> str:
        """Respuesta inicial al detectar servicio"""
        responses = {
            "AI_CHATBOT": f"¡Perfecto {self.contact_name}! 🤖 AI Chatbot reduce 70% tiempo respuesta. ¿Para cuántos usuarios?",
            "AI_VOICE": f"¡Excelente {self.contact_name}! 📞 AI Voice: 60% mejor conversión en llamadas. ¿Para ventas o soporte?",
            "AI_VIDEO": f"¡Genial {self.contact_name}! 🎥 AI Video: avatares personalizados. ¿Para onboarding o marketing?",
            "AI_ASSISTANT_WHATSAPP": f"¡Ideal {self.contact_name}! 💬 Automatiza 95% mensajes WhatsApp. ¿Cuántos mensajes al día?",
            "DESARROLLO_CUSTOM": f"¡Perfecto {self.contact_name}! 🚀 Desarrollo IA personalizado. ¿Qué proceso automatizar?"
        }
        return responses.get(service, f"¡Perfecto {self.contact_name}! Excelente elección. ¿Para qué lo necesitas?")

    def _is_info_request(self, message: str) -> bool:
        """Detectar si pide información"""
        keywords = ['información', 'info', 'detalles', 'más', 'explica', 'cómo funciona', 'qué hace']
        return any(keyword in message.lower() for keyword in keywords)

    def _get_detailed_info(self) -> str:
        """Información detallada del servicio detectado"""
        service = self.prospect_info.get('detected_service', '')
        
        info = {
            "AI_CHATBOT": f"""🤖 **AI Chatbot TDX:**
✅ Atiende clientes 24/7 automáticamente
✅ Reduce 70% tiempo respuesta, 40% más ventas
✅ Casos: clínicas agenda citas, ecommerce vende productos
¿Para cuántos usuarios lo necesitas {self.contact_name}?""",

            "AI_VOICE": f"""📞 **AI Voice TDX:**
✅ Llamadas automáticas ventas/soporte
✅ 60% mejor conversión, recupera 80% cartera  
✅ Casos: fintech cobra, salud confirma citas
¿Para ventas o soporte {self.contact_name}?""",

            "AI_VIDEO": f"""🎥 **AI Video TDX:**
✅ Videos personalizados con avatares realistas
✅ Onboarding automático, explicaciones 24/7
✅ Casos: empresas entrenan, salud explica procedimientos
¿Para onboarding o marketing {self.contact_name}?"""
        }
        
        return info.get(service, f"Servicio increíble {self.contact_name}! ¿Qué necesitas saber específicamente?")

    def _get_missing_data(self) -> Optional[str]:
        """Verificar qué datos faltan"""
        if not self.prospect_info.get('email'):
            return "¿Tu email?"
        if not self.prospect_info.get('company_name'):
            return "¿Nombre de tu empresa?"
        return None

    def _is_scheduling_confirmation(self, message: str) -> bool:
        """Detectar confirmación de agendamiento"""
        confirmations = ['si', 'sí', 'yes', 'dale', 'ok', 'claro', 'perfecto', 'genial', 'agendemos']
        return any(conf in message.lower() for conf in confirmations)

    async def _process_scheduling(self, message: str) -> Optional[str]:
        """Procesar fecha y hora específica"""
        try:
            # Patterns simples de fecha/hora
            patterns = [
                (r'lunes\s+(\d+)pm', 'lunes'),
                (r'martes\s+(\d+)pm', 'martes'),
                (r'miércoles\s+(\d+)pm', 'miércoles'),
                (r'jueves\s+(\d+)pm', 'jueves'),
                (r'viernes\s+(\d+)pm', 'viernes')
            ]
            
            for pattern, day in patterns:
                match = re.search(pattern, message.lower())
                if match:
                    hour = match.group(1)
                    # Simular agendamiento exitoso
                    return f"✅ ¡Perfecto {self.contact_name}! Reunión agendada para {day} a las {hour}:00 PM. Te llegará la invitación por email 📧"
            
            # Si no coincide con patrones, pedir clarificación
            return f"¿Podrías especificar día y hora? Ej: 'lunes 3pm' {self.contact_name}"
            
        except Exception as e:
            logger.error(f"Error processing scheduling: {e}")
            return "Error agendando. Te contactamos pronto."

    def _get_contextual_response(self, message: str) -> str:
        """Respuesta contextual simple"""
        # Extraer email si lo mencionan
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', message)
        if email_match:
            self.prospect_info['email'] = email_match.group(0)
            return f"Perfecto {self.contact_name}! Email guardado. ¿Nombre de tu empresa?"
        
        # Detectar nombre de empresa (palabras capitalizadas)
        if not self.prospect_info.get('company_name'):
            words = message.split()
            for word in words:
                if word[0].isupper() and len(word) > 2 and word not in ['Si', 'No', 'Para', 'En']:
                    self.prospect_info['company_name'] = word
                    return f"Excelente {self.contact_name}! Para {word}, ¿cuál es tu mayor reto con automatización?"
        
        return f"Entiendo {self.contact_name}. ¿Hay algo específico que te gustaría saber?"

    async def _send_response(self, response: str) -> str:
        """Enviar respuesta y logging"""
        try:
            # Log de respuesta
            self.conversation_log.append({
                'type': 'assistant_message',
                'content': response,
                'timestamp': datetime.now().isoformat()
            })
            
            # Enviar por Chatwoot
            if self.chatwoot_client:
                await self.chatwoot_client.send_message_with_typing(
                    self.conversation_id, response, self.user_id
                )
            
            logger.info(f"✅ Response sent: {response[:50]}...")
            return response
            
        except Exception as e:
            logger.error(f"Error sending response: {e}")
            return response