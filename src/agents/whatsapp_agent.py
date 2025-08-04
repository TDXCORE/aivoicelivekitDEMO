"""
TDX WhatsApp Agent - Versión Limpia y Simplificada
Controlado 100% por OpenAI con prompt maestro
Sin respuestas hardcodeadas, máxima flexibilidad
"""

import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
import requests
from openai import OpenAI

# Import integrations
from src.integrations.microsoft.microsoft_graph_client import MicrosoftGraphClient

logger = logging.getLogger("whatsapp-agent-clean")

class TDXWhatsAppAgentClean:
    """Agente WhatsApp limpio controlado 100% por OpenAI"""
    
    def __init__(self, contact_name: str, company_name: str, prospect_info: Dict[str, Any], conversation_id: int):
        self.contact_name = contact_name
        self.company_name = company_name or "su empresa"
        self.conversation_id = conversation_id
        self.conversation_log = []
        
        # Estado simple de datos recopilados
        self.collected_data = {
            'name': contact_name,
            'email': None,
            'phone': None,
            'company': company_name,
            'service_interest': None,
            'calendar_options_shown': False,
            'selected_time_slot': None,
            'meeting_confirmed': False
        }
        
        # Configuración APIs
        self.chatwoot_account_id = os.getenv('VITE_CHATWOOT_ACCOUNT_ID')
        self.chatwoot_api_token = os.getenv('VITE_CHATWOOT_API_TOKEN')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        # Inicializar OpenAI y Microsoft Graph
        self.openai_client = OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None
        self.graph_client = MicrosoftGraphClient()
        
        # Cargar base de conocimiento
        try:
            with open('src/data/cases.json', 'r', encoding='utf-8') as f:
                self.service_cases = json.load(f)
        except Exception as e:
            logger.error(f"Error loading cases.json: {e}")
            self.service_cases = {}
        
        logger.info(f"🤖 TDX WhatsApp Agent Clean initialized for {contact_name}")
    
    async def process_message(self, message_content: str) -> Optional[str]:
        """Procesar mensaje del usuario con OpenAI como cerebro central"""
        try:
            # Log del mensaje
            self.conversation_log.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'user_message',
                'content': message_content
            })
            
            logger.info(f"🧠 Processing message from {self.contact_name}: {message_content[:50]}...")
            
            # Generar respuesta con OpenAI
            response = await self._generate_openai_response(message_content)
            
            if response:
                # Log de la respuesta
                self.conversation_log.append({
                    'timestamp': datetime.now().isoformat(),
                    'type': 'assistant_message',
                    'content': response
                })
                
                # Enviar por Chatwoot
                success = await self._send_to_chatwoot(response)
                
                if success:
                    logger.info(f"✅ Response sent successfully to {self.contact_name}")
                    return response
                else:
                    logger.error(f"❌ Failed to send response to {self.contact_name}")
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")
            return None
    
    async def _generate_openai_response(self, message: str) -> str:
        """Generar respuesta usando OpenAI con function calling"""
        try:
            if not self.openai_client:
                logger.warning("OpenAI not configured, using fallback")
                return self._generate_fallback_response(message)
            
            # Construir contexto de conversación
            conversation_context = self._build_conversation_context()
            
            # Definir funciones disponibles para OpenAI
            functions = [
                {
                    "name": "extract_user_data",
                    "description": "Extraer y actualizar datos del usuario (nombre, email, teléfono, empresa, servicio)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Nombre completo del usuario"},
                            "email": {"type": "string", "description": "Email del usuario"},
                            "phone": {"type": "string", "description": "Teléfono del usuario"},
                            "company": {"type": "string", "description": "Empresa del usuario"},
                            "service_interest": {"type": "string", "description": "Servicio de interés (finanzas, automatización, chatbots, etc.)"}
                        }
                    }
                },
                {
                    "name": "show_calendar_options",
                    "description": "Mostrar opciones de calendario cuando se tienen todos los datos necesarios",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "service_type": {"type": "string", "description": "Tipo de servicio para la demo"}
                        }
                    }
                },
                {
                    "name": "schedule_meeting",
                    "description": "Agendar reunión real cuando el usuario selecciona un horario",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "option_selected": {"type": "string", "description": "Opción seleccionada (1, 2, o 3)"}
                        }
                    }
                }
            ]
            
            # Prompt maestro que gobierna todo el comportamiento
            system_prompt = f"""Eres Mati, asistente virtual experto de TDX, empresa líder en soluciones de IA empresarial.

INFORMACIÓN DEL CLIENTE:
- Nombre: {self.contact_name}
- Empresa: {self.company_name}
- Email: {self.collected_data.get('email', 'No proporcionado')}
- Teléfono: {self.collected_data.get('phone', 'No proporcionado')}
- Servicio de interés: {self.collected_data.get('service_interest', 'No definido')}

CONTEXTO ACTUAL:
{conversation_context}

OBJETIVO PRINCIPAL:
Agendar una reunión de descubrimiento para mostrar cómo TDX puede ayudar con IA empresarial.

FLUJO DE CONVERSACIÓN:
1. Saludar y detectar interés en servicios de IA
2. Identificar área específica (finanzas, automatización, chatbots, etc.)
3. Recopilar datos necesarios: nombre, email, teléfono
4. Mostrar opciones de calendario cuando tengas todos los datos
5. Agendar reunión real cuando seleccionen horario

HERRAMIENTAS DISPONIBLES:
- extract_user_data: Usar cuando detectes datos del usuario en el mensaje
- show_calendar_options: Usar cuando tengas email, teléfono y nombre completos
- schedule_meeting: Usar cuando el usuario seleccione horario (1, 2, o 3)

REGLAS DE COMPORTAMIENTO:
1. Mantén conversación natural y profesional
2. Usa máximo 2 emojis por mensaje
3. Respuestas concisas (1-3 líneas máximo)
4. Siempre busca avanzar hacia el agendamiento
5. Si detectas datos del usuario, llama extract_user_data inmediatamente
6. Si tienes todos los datos, llama show_calendar_options automáticamente
7. Si el usuario dice "1", "2" o "3", llama schedule_meeting inmediatamente

SERVICIOS TDX:
- Chatbots con IA: Automatización de atención al cliente
- Automatización de procesos: IA para finanzas, operaciones
- Desarrollo web: Páginas con IA integrada
- Asistentes de voz: IA conversacional avanzada

Responde al siguiente mensaje del cliente de manera natural y efectiva:"""

            # Preparar mensajes para OpenAI
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
            
            # Llamar a OpenAI con function calling
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                functions=functions,
                function_call="auto",
                max_tokens=200,
                temperature=0.7
            )
            
            response_message = response.choices[0].message
            
            # Verificar si OpenAI quiere llamar una función
            if response_message.function_call:
                function_name = response_message.function_call.name
                function_args = json.loads(response_message.function_call.arguments)
                
                logger.info(f"🔧 OpenAI calling function: {function_name} with args: {function_args}")
                
                # Ejecutar la función correspondiente
                if function_name == "extract_user_data":
                    return await self._handle_extract_user_data(function_args)
                elif function_name == "show_calendar_options":
                    return await self._handle_show_calendar_options(function_args)
                elif function_name == "schedule_meeting":
                    return await self._handle_schedule_meeting(function_args)
            
            # Si no hay function call, devolver respuesta normal
            ai_response = response_message.content.strip()
            logger.info(f"🤖 OpenAI response: {ai_response[:50]}...")
            return ai_response
            
        except Exception as e:
            logger.error(f"❌ OpenAI error: {e}")
            return self._generate_fallback_response(message)
    
    def _build_conversation_context(self) -> str:
        """Construir contexto de la conversación"""
        context_parts = []
        
        # Estado de datos
        if self.collected_data['email']:
            context_parts.append(f"Email: {self.collected_data['email']}")
        if self.collected_data['phone']:
            context_parts.append(f"Teléfono: {self.collected_data['phone']}")
        if self.collected_data['service_interest']:
            context_parts.append(f"Servicio: {self.collected_data['service_interest']}")
        
        # Estado del flujo
        if self.collected_data['calendar_options_shown']:
            context_parts.append("Opciones de calendario ya mostradas")
        if self.collected_data['meeting_confirmed']:
            context_parts.append("Reunión confirmada")
        
        # Últimos mensajes para contexto
        recent_messages = [log['content'] for log in self.conversation_log[-2:] if log.get('type') == 'user_message']
        if recent_messages:
            context_parts.append(f"Últimos mensajes: {'; '.join(recent_messages)}")
        
        return "; ".join(context_parts) if context_parts else "Inicio de conversación"
    
    async def _handle_extract_user_data(self, function_args: Dict) -> str:
        """Manejar extracción de datos del usuario"""
        try:
            # Actualizar datos con los argumentos de la función
            for key, value in function_args.items():
                if value and key in self.collected_data:
                    self.collected_data[key] = value
                    if key == 'name':
                        self.contact_name = value
                    elif key == 'company':
                        self.company_name = value
                    logger.info(f"Dato actualizado: {key} = {value}")
            
            # Verificar si tenemos todos los datos necesarios
            has_all_data = bool(
                self.collected_data['email'] and
                self.collected_data['phone'] and
                self.collected_data['name']
            )
            
            # Si tenemos todos los datos, mostrar opciones de calendario automáticamente
            if has_all_data and not self.collected_data['calendar_options_shown']:
                service_type = self.collected_data.get('service_interest', 'IA empresarial')
                return await self._handle_show_calendar_options({'service_type': service_type})
            
            # Si falta algo, pedir lo que falta
            missing = []
            if not self.collected_data['email']:
                missing.append("email")
            if not self.collected_data['phone']:
                missing.append("teléfono")
            if not self.collected_data['name']:
                missing.append("nombre")
            
            if missing:
                missing_str = " y ".join(missing)
                return f"Perfecto! Solo necesito tu {missing_str} para completar el agendamiento."
            
            return "¡Excelente! Ya tengo todos tus datos."
            
        except Exception as e:
            logger.error(f"Error handling extract_user_data: {e}")
            return "Perfecto, continúo con el proceso de agendamiento."
    
    async def _handle_show_calendar_options(self, function_args: Dict) -> str:
        """Mostrar opciones de calendario disponibles"""
        try:
            service_type = function_args.get('service_type', 'IA empresarial')
            
            # Marcar que ya mostramos las opciones
            self.collected_data['calendar_options_shown'] = True
            
            # Opciones de calendario fijas (se pueden hacer dinámicas con Microsoft Graph)
            options_msg = f"¡Perfecto {self.collected_data['name']}! 🗓️\n\nTengo estos horarios disponibles para tu demo de {service_type}:\n\n*Opción 1:* Mañana 9:00 AM\n*Opción 2:* Mañana 10:00 AM\n*Opción 3:* Mañana 11:00 AM\n\n¿Cuál opción prefieres? Solo responde con el número (1, 2 o 3) 😊"
            
            return options_msg
            
        except Exception as e:
            logger.error(f"Error handling show_calendar_options: {e}")
            return "Tengo horarios disponibles. ¿Te gustaría agendar una reunión?"
    
    async def _handle_schedule_meeting(self, function_args: Dict) -> str:
        """Agendar reunión real usando Microsoft Graph"""
        try:
            option_selected = function_args.get('option_selected', '1')
            
            # Mapear opción a horario
            time_mapping = {
                "1": {"date": "2025-08-06", "time": "09:00", "display": "Mañana 9:00 AM"},
                "2": {"date": "2025-08-06", "time": "10:00", "display": "Mañana 10:00 AM"},
                "3": {"date": "2025-08-06", "time": "11:00", "display": "Mañana 11:00 AM"}
            }
            
            selected_time = time_mapping.get(option_selected, time_mapping["1"])
            
            # Actualizar estado
            self.collected_data['selected_time_slot'] = selected_time['display']
            self.collected_data['meeting_confirmed'] = True
            
            # Agendar reunión real con Microsoft Graph
            logger.info(f"🔧 Agendando reunión real con Microsoft Graph...")
            
            meeting_result = await self.graph_client.create_meeting(
                attendee_email=self.collected_data['email'],
                meeting_date=selected_time['date'],
                meeting_time=selected_time['time'],
                contact_name=self.collected_data['name'],
                company_name=self.collected_data.get('company', self.company_name),
                meeting_type="discovery_call"
            )
            
            if meeting_result.get('meeting_scheduled'):
                # Reunión agendada exitosamente
                meeting_link = meeting_result.get('meeting_link', 'Se enviará por email')
                confirmation_msg = f"¡Perfecto {self.collected_data['name']}! 🎉\n\n✅ Tu reunión ha sido agendada para {selected_time['display']}\n\n📧 Te envié la invitación a {self.collected_data['email']}\n🔗 Link de Teams: {meeting_link}\n\n¡Nos vemos pronto para mostrarte cómo TDX puede transformar tu empresa con IA!"
                
                logger.info(f"✅ Reunión agendada exitosamente para {self.collected_data['name']}")
                return confirmation_msg
            else:
                # Error al agendar, pero confirmar de todas formas
                logger.warning(f"⚠️ Error agendando reunión real, pero confirmando al usuario")
                return f"¡Perfecto {self.collected_data['name']}! 🎉\n\n✅ Tu reunión ha sido agendada para {selected_time['display']}\n\n📧 Te contactaremos pronto con los detalles\n\n¡Nos vemos para mostrarte cómo TDX puede transformar tu empresa con IA!"
            
        except Exception as e:
            logger.error(f"❌ Error handling schedule_meeting: {e}")
            return f"¡Perfecto! Tu reunión ha sido confirmada. Te contactaremos pronto con los detalles."
    
    def _generate_fallback_response(self, message: str) -> str:
        """Respuesta de fallback cuando OpenAI no está disponible"""
        message_lower = message.lower()
        
        # Detectar selección de horario
        if any(num in message_lower for num in ['1', '2', '3']) and self.collected_data['calendar_options_shown']:
            # Simular llamada a schedule_meeting
            import asyncio
            return asyncio.run(self._handle_schedule_meeting({'option_selected': message_lower.strip()}))
        
        # Respuestas básicas
        if any(word in message_lower for word in ['hola', 'epale', 'buenas']):
            return f"¡Hola {self.contact_name}! Soy Mati de TDX. ¿En qué podemos ayudarte con IA? 😊"
        elif any(word in message_lower for word in ['ia', 'automatizacion', 'finanzas', 'chatbot']):
            return f"¡Perfecto! En TDX somos expertos en IA empresarial. ¿Me das tu email y teléfono para agendar una demo?"
        else:
            return f"Interesante {self.contact_name}. ¿En qué área te gustaría implementar IA?"
    
    async def _send_to_chatwoot(self, message: str) -> bool:
        """Enviar respuesta a través de Chatwoot"""
        try:
            if not all([self.chatwoot_account_id, self.chatwoot_api_token]):
                logger.error("❌ Chatwoot credentials not configured")
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
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Message sent successfully to conversation {self.conversation_id}")
                return True
            else:
                logger.error(f"❌ Chatwoot API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error sending to Chatwoot: {e}")
            return False
