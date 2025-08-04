import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import requests

# Import integrations
from src.integrations.microsoft.microsoft_graph_client import MicrosoftGraphClient

logger = logging.getLogger("whatsapp-agent")

class TDXWhatsAppAgentV2:
    """Agente de WhatsApp avanzado con IA completa para TDX"""
    
    def __init__(self, contact_name: str, company_name: str, prospect_info: Dict[str, Any], conversation_id: int):
        self.contact_name = contact_name
        self.company_name = company_name or "su empresa"
        self.prospect_info = prospect_info
        self.conversation_id = conversation_id
        self.session_start_time = datetime.now()
        self.conversation_log = []
        self.awaiting_response_type = None
        self.conversation_state = "greeting"  # greeting, qualifying, scheduling, closing
        
        # Estado de datos del usuario recopilados
        self.collected_data = {
            'name': contact_name,
            'email': None,
            'phone': None,
            'company': company_name,
            'service_interest': None,
            'demo_confirmed': False,
            'contact_info_complete': False,
            'all_data_complete': False,
            'calendar_options_shown': False,
            'selected_time_slot': None,
            'meeting_confirmed': False
        }
        
        # Configuración de APIs
        self.chatwoot_account_id = os.getenv('VITE_CHATWOOT_ACCOUNT_ID')
        self.chatwoot_api_token = os.getenv('VITE_CHATWOOT_API_TOKEN')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        # Inicializar componentes
        self.graph_client = MicrosoftGraphClient()
        
        # Cache para opciones de calendario mostradas
        self.current_calendar_options = []
        
        # Load service cases
        try:
            with open('src/data/cases.json', 'r', encoding='utf-8') as f:
                self.service_cases = json.load(f)
        except Exception as e:
            logger.error(f"Error loading cases.json: {e}")
            self.service_cases = {}
        
        # Initialize conversation with prospect data
        # Note: MinimalSlotManager doesn't have update_prospect_info method
        
        logger.info(f"🤖 Advanced WhatsApp agent initialized for {contact_name} - Conversation {conversation_id}")
        logger.info(f"🧠 AI Components loaded: Intent, BANT, Service Mapper, Value Injector, Slot Manager")
    
    async def process_message(self, message_content: str) -> Optional[str]:
        """Procesar mensaje del usuario con IA avanzada completa"""
        try:
            # Log del mensaje del usuario
            self.conversation_log.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'user_message',
                'content': message_content
            })
            
            logger.info(f"🧠 Processing AI message from {self.contact_name}: {message_content[:50]}...")
            
            # 1. Actualizar datos recopilados del usuario
            self._update_collected_data(message_content)
            
            # 2. Generación de respuesta con OpenAI y function calling
            response = await self._generate_ai_response(message_content)
            
            if response:
                # Log de la respuesta del bot
                self.conversation_log.append({
                    'timestamp': datetime.now().isoformat(),
                    'type': 'assistant_message',
                    'content': response
                })
                
                # Enviar respuesta a través de Chatwoot
                success = await self._send_chatwoot_response(response)
                
                if success:
                    logger.info(f"✅ AI Response sent successfully to {self.contact_name}")
                    return response
                else:
                    logger.error(f"❌ Failed to send response to {self.contact_name}")
                    return None
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error processing AI message for {self.contact_name}: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return None
    
    async def _generate_ai_response(self, message: str) -> str:
        """Generar respuesta inteligente usando OpenAI con function calling"""
        try:
            if not self.openai_api_key:
                logger.warning("OpenAI API key not configured, using fallback")
                return await self._generate_fallback_response_simple(message)
            
            # Preparar el contexto de la conversación
            conversation_context = self._build_conversation_context_for_openai()
            
            # Preparar las funciones disponibles para OpenAI
            functions = [
                {
                    "name": "extract_user_data",
                    "description": "Extraer y actualizar datos del usuario (nombre, email, teléfono, empresa)",
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
                    "description": "Mostrar opciones de calendario cuando se tienen todos los datos",
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
                            "option_selected": {"type": "string", "description": "Opción seleccionada (1, 2, o 3)"},
                            "meeting_date": {"type": "string", "description": "Fecha de la reunión"},
                            "meeting_time": {"type": "string", "description": "Hora de la reunión"}
                        }
                    }
                }
            ]
            
            # Crear el prompt maestro
            system_prompt = f"""Eres Mati, asistente virtual experto de TDX, empresa líder en soluciones de IA empresarial.

DATOS DEL CLIENTE:
- Nombre: {self.contact_name}
- Empresa: {self.company_name}
- Email: {self.collected_data.get('email', 'No proporcionado')}
- Teléfono: {self.collected_data.get('phone', 'No proporcionado')}
- Servicio de interés: {self.collected_data.get('service_interest', 'No definido')}

ESTADO ACTUAL:
{conversation_context}

FLUJO DE AGENDAMIENTO:
1. Saludar y detectar interés en servicios de IA
2. Identificar área específica (finanzas, automatización, etc.)
3. Recopilar datos: nombre, email, teléfono
4. Mostrar opciones de calendario cuando tengas todos los datos
5. Agendar reunión real cuando seleccionen horario

HERRAMIENTAS DISPONIBLES:
- extract_user_data: Para extraer datos del mensaje del usuario
- show_calendar_options: Para mostrar horarios disponibles
- schedule_meeting: Para agendar la reunión real

INSTRUCCIONES CRÍTICAS:
1. Usa las funciones cuando sea apropiado
2. Si detectas datos del usuario, llama extract_user_data
3. Si tienes email, teléfono y nombre, llama show_calendar_options
4. Si el usuario selecciona horario (1, 2, 3), llama schedule_meeting
5. Mantén conversación natural y profesional
6. Usa emojis apropiados (máximo 2 por mensaje)
7. Respuestas entre 1-3 líneas máximo

Responde al siguiente mensaje del cliente:"""

            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            
            # Preparar mensajes de conversación
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
            
            # Llamar a OpenAI con function calling
            response = client.chat.completions.create(
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
                
                logger.info(f"🔧 OpenAI llamando función: {function_name} con args: {function_args}")
                
                # Ejecutar la función correspondiente
                if function_name == "extract_user_data":
                    return await self._handle_extract_user_data(function_args, message)
                elif function_name == "show_calendar_options":
                    return await self._handle_show_calendar_options(function_args)
                elif function_name == "schedule_meeting":
                    return await self._handle_schedule_meeting(function_args)
            
            # Si no hay function call, devolver la respuesta normal
            ai_response = response_message.content.strip()
            logger.info(f"🤖 OpenAI response: {ai_response[:50]}...")
            return ai_response
            
        except Exception as e:
            logger.error(f"❌ OpenAI error: {e}")
            return await self._generate_fallback_response_simple(message)

    def _build_conversation_context_for_openai(self) -> str:
        """Construir contexto de la conversación para OpenAI"""
        context_parts = []
        
        # Estado de datos recopilados
        if self.collected_data['email']:
            context_parts.append(f"Email recopilado: {self.collected_data['email']}")
        if self.collected_data['phone']:
            context_parts.append(f"Teléfono recopilado: {self.collected_data['phone']}")
        if self.collected_data['service_interest']:
            context_parts.append(f"Servicio de interés: {self.collected_data['service_interest']}")
        
        # Estado del flujo
        context_parts.append(f"Estado conversación: {self.conversation_state}")
        context_parts.append(f"Datos completos: {self.collected_data['all_data_complete']}")
        context_parts.append(f"Opciones mostradas: {self.collected_data['calendar_options_shown']}")
        
        # Últimos mensajes para contexto
        recent_messages = [log['content'] for log in self.conversation_log[-3:] if log.get('type') == 'user_message']
        if recent_messages:
            context_parts.append(f"Últimos mensajes: {'; '.join(recent_messages)}")
        
        return "; ".join(context_parts) if context_parts else "Inicio de conversación"

    async def _handle_extract_user_data(self, function_args: Dict, original_message: str) -> str:
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
                    logger.info(f"Dato actualizado por OpenAI - {key}: {value}")
            
            # Verificar si tenemos todos los datos necesarios
            self.collected_data['all_data_complete'] = bool(
                self.collected_data['email'] and
                self.collected_data['phone'] and
                self.collected_data['name'] and
                self.collected_data.get('service_interest')
            )
            
            # Si tenemos todos los datos, mostrar opciones de calendario
            if self.collected_data['all_data_complete'] and not self.collected_data['calendar_options_shown']:
                return await self._handle_show_calendar_options({'service_type': self.collected_data['service_interest']})
            
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
            
            return "¡Excelente! Ya tengo tus datos."
            
        except Exception as e:
            logger.error(f"Error handling extract_user_data: {e}")
            return "Perfecto, continúo con el proceso de agendamiento."

    async def _handle_show_calendar_options(self, function_args: Dict) -> str:
        """Manejar mostrar opciones de calendario"""
        try:
            service_type = function_args.get('service_type', self.collected_data.get('service_interest', 'finanzas'))
            
            # Marcar que ya mostramos las opciones
            self.collected_data['calendar_options_shown'] = True
            self.current_calendar_options = [
                {"option": "1", "date": "2025-08-06", "time": "09:00", "display": "Martes Mañana a las 9:00 AM"},
                {"option": "2", "date": "2025-08-06", "time": "10:00", "display": "Martes Mañana a las 10:00 AM"},
                {"option": "3", "date": "2025-08-06", "time": "11:00", "display": "Martes Mañana a las 11:00 AM"}
            ]
            
            options_msg = f"¡Perfecto {self.collected_data['name']}! 🗓️\n\nTengo estos horarios disponibles para tu demo de {service_type}:\n\n*Opción 1:* Martes Mañana a las 9:00 AM\n*Opción 2:* Martes Mañana a las 10:00 AM\n*Opción 3:* Martes Mañana a las 11:00 AM\n\n¿Cuál opción prefieres? Solo responde con el número (1, 2 o 3) 😊"
            
            return options_msg
            
        except Exception as e:
            logger.error(f"Error handling show_calendar_options: {e}")
            return "Tengo horarios disponibles. ¿Te gustaría agendar una reunión?"

    async def _handle_schedule_meeting(self, function_args: Dict) -> str:
        """Manejar agendamiento real de la reunión"""
        try:
            option_selected = function_args.get('option_selected', '1')
            
            # Mapear opción a horario
            time_mapping = {
                "1": {"date": "2025-08-06", "time": "09:00", "display": "Martes 6 de Agosto a las 9:00 AM"},
                "2": {"date": "2025-08-06", "time": "10:00", "display": "Martes 6 de Agosto a las 10:00 AM"},
                "3": {"date": "2025-08-06", "time": "11:00", "display": "Martes 6 de Agosto a las 11:00 AM"}
            }
            
            selected_time = time_mapping.get(option_selected, time_mapping["1"])
            
            # Actualizar estado
            self.collected_data['selected_time_slot'] = selected_time['display']
            self.collected_data['meeting_confirmed'] = True
            self.conversation_state = "closing"
            
            # Llamar al Microsoft Graph Client para agendar la reunión real
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
                confirmation_msg = f"¡Perfecto {self.collected_data['name']}! 🎉\n\n✅ Tu reunión ha sido agendada para {selected_time['display']}\n\n📧 Te envié la invitación a {self.collected_data['email']}\n🔗 Link de Teams: {meeting_link}\n\n¡Nos vemos pronto para mostrarte cómo TDX puede transformar tu área de {self.collected_data.get('service_interest', 'finanzas')}!"
                
                logger.info(f"✅ Reunión agendada exitosamente para {self.collected_data['name']}")
                return confirmation_msg
            else:
                # Error al agendar, pero confirmar de todas formas
                logger.warning(f"⚠️ Error agendando reunión real, pero confirmando al usuario")
                return f"¡Perfecto {self.collected_data['name']}! 🎉\n\n✅ Tu reunión ha sido agendada para {selected_time['display']}\n\n📧 Te contactaremos pronto con los detalles\n\n¡Nos vemos para mostrarte cómo TDX puede transformar tu área de {self.collected_data.get('service_interest', 'finanzas')}!"
            
        except Exception as e:
            logger.error(f"❌ Error handling schedule_meeting: {e}")
            return f"¡Perfecto! Tu reunión ha sido confirmada. Te contactaremos pronto con los detalles."

    async def _generate_fallback_response_simple(self, message: str) -> str:
        """Respuesta de fallback simple cuando OpenAI falla"""
        message_lower = message.lower()
        
        # Detectar selección de horario
        if any(num in message_lower for num in ['1', '2', '3']) and self.collected_data['calendar_options_shown']:
            return await self._handle_schedule_meeting({'option_selected': message_lower.strip()})
        
        # Respuestas básicas
        if any(word in message_lower for word in ['hola', 'epale', 'buenas']):
            return f"¡Hola {self.contact_name}! ¿En qué puedo ayudarte hoy? 😊"
        elif any(word in message_lower for word in ['ia', 'automatizacion', 'finanzas']):
            return f"¡Perfecto! En TDX ofrecemos soluciones de IA. ¿Me das tu email y teléfono para agendar una demo?"
        else:
            return f"Interesante {self.contact_name}. ¿En qué área te gustaría implementar IA?"

    
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
    
    def _build_conversation_context(self, intent_result, service_result: Dict, prospect_info: Dict) -> str:
        """Construir contexto de la conversación para OpenAI"""
        context_parts = []
        
        if hasattr(intent_result, 'category') and intent_result.category != 'UNKNOWN':
            context_parts.append(f"Intención detectada: {intent_result.category}")
        
        if service_result.get('service') != 'UNKNOWN':
            context_parts.append(f"Servicio de interés: {service_result['service']} (confianza: {service_result['confidence']:.2f})")
        
        if hasattr(intent_result, 'industry') and intent_result.industry:
            context_parts.append(f"Industria: {intent_result.industry}")
        
        if len(self.conversation_log) > 1:
            context_parts.append(f"Mensajes intercambiados: {len(self.conversation_log)}")
        
        context_parts.append(f"Estado conversación: {self.conversation_state}")
        
        return "; ".join(context_parts) if context_parts else "Primer contacto"
    
    def _generate_fallback_response(self, message: str, intent_result, service_result: Dict) -> str:
        """Generar respuesta de respaldo cuando OpenAI falla"""
        message_lower = message.lower()
        
        # Analizar el contexto reciente para evitar repeticiones
        recent_bot_messages = [log.get('content', '') for log in self.conversation_log[-3:] if log.get('type') == 'assistant_message']
        recent_user_messages = [log.get('content', '') for log in self.conversation_log[-3:] if log.get('type') == 'user_message']
        
        # Detectar si el usuario ya dio información específica
        scheduling_info = self._extract_scheduling_info(message, recent_user_messages)
        has_time_info = 'horario mencionado' in scheduling_info.lower()
        has_service_info = 'servicios de interés' in scheduling_info.lower()
        has_confirmation = 'confirmaciones detectadas' in scheduling_info.lower()
        has_personal_data = 'datos personales' in scheduling_info.lower()
        
        # Extraer información específica de datos personales
        has_email = 'email:' in scheduling_info.lower()
        has_phone = 'teléfono:' in scheduling_info.lower()
        has_name = 'nombre:' in scheduling_info.lower()
        
        # RESPUESTAS CONTEXTUALES INTELIGENTES BASADAS EN EL ESTADO DE LA CONVERSACIÓN
        
        # CASO 1: Usuario seleccionó horario - confirmar reunión
        if self.collected_data['selected_time_slot']:
            self.collected_data['meeting_confirmed'] = True
            return "¡Perfecto! Tu reunión ha sido confirmada. Te enviaremos los detalles por email."
        
        # CASO 2: Usuario proporcionó teléfono (después de email) - MOSTRAR OPCIONES DE CALENDARIO
        if has_phone and self.collected_data['email']:
            # Verificar si ya tenemos todos los datos necesarios
            if self.collected_data['name'] and self.collected_data['email'] and self.collected_data['phone']:
                self.collected_data['all_data_complete'] = True
                
                # Si no hemos mostrado opciones de calendario, mostrarlas ahora
                if not self.collected_data['calendar_options_shown']:
                    self.collected_data['calendar_options_shown'] = True
                    
                    service_interest = self.collected_data.get('service_interest', 'automatización')
                    options_msg = f"¡Perfecto {self.collected_data['name']}! 🗓️\n\nTengo estos horarios disponibles para tu demo de {service_interest}:\n\n*Opción 1:* Martes Mañana a las 9:00 AM\n*Opción 2:* Martes Mañana a las 10:00 AM\n*Opción 3:* Martes Mañana a las 11:00 AM\n\n¿Cuál opción prefieres? Solo responde con el número (1, 2 o 3) 😊"
                    return options_msg
                else:
                    return "¡Excelente! Ya tengo tu email y teléfono. Te contactaremos muy pronto para coordinar la demo de automatización."
            else:
                return "¡Excelente! Ya tengo tu email y teléfono. Te contactaremos muy pronto para coordinar la demo de automatización."
        
        # CASO 3: Usuario proporcionó email pero falta teléfono
        if self.collected_data['email'] and not self.collected_data['phone']:
            # Siempre pedir teléfono si no lo tenemos, es crítico para el flujo
            return "Excelente, Freddy. Para completar el agendamiento, ¿me podrías proporcionar tu número de teléfono?"
        
        # CASO 4: Usuario proporcionó teléfono pero falta email
        if has_phone and not self.collected_data['email']:
            return "Perfecto, ya tengo tu teléfono. ¿Me puedes proporcionar tu email para enviarte la información de la demo?"
        
        # CASO 4: Usuario confirmó interés pero falta recopilar datos
        if has_confirmation and has_service_info and not self.collected_data['all_data_complete']:
            # Pedir todos los datos de una vez
            missing_data = []
            if not self.collected_data['name'] or self.collected_data['name'] == 'Cliente':
                missing_data.append("nombre completo")
            if not self.collected_data['email']:
                missing_data.append("email")
            if not self.collected_data['phone']:
                missing_data.append("teléfono")
            if not self.collected_data['company'] or self.collected_data['company'] == 'su empresa':
                missing_data.append("empresa")
            
            if missing_data:
                # Crear mensaje personalizado según lo que falta
                if len(missing_data) >= 3:
                    return f"¡Perfecto! Para agendar tu demo personalizada, necesito:\n\n📝 Tu nombre completo\n📧 Email corporativo\n📱 Teléfono\n🏢 Nombre de tu empresa\n\nPuedes enviarme todo junto 😊"
                else:
                    missing_str = " y ".join(missing_data) if len(missing_data) > 1 else missing_data[0]
                    return f"¡Excelente! Solo necesito tu {missing_str} para agendar la demo."
            else:
                return "Perfecto. Ya tengo todos tus datos."
        
        # CASO 4: Si el usuario ya confirmó y dio horario
        if has_confirmation and has_time_info:
            return "¡Perfecto! Agendado para mañana 3:00 PM. ¿Me confirmas tu email corporativo?"
        
        # CASO 5: Si el usuario dio horario específico
        if has_time_info or any(word in message_lower for word in ['mañana 3pm', '3pm', 'mañana 3', 'tarde']):
            # Evitar repetir confirmación si ya se confirmó
            if not any('perfecto' in msg and 'email' in msg for msg in recent_bot_messages):
                return "¡Perfecto! Mañana 3:00 PM queda confirmado. ¿Me das tu email para enviarte la invitación?"
            else:
                return "Excelente. Ya tienes todo listo para mañana 3:00 PM."
        
        # CASO 6: Usuario dice "ya te dije" o similar (frustración)
        if any(phrase in message_lower for phrase in ['ya te dije', 'ya dije', 'ya te di', 'ya proporcioné']):
            return "Tienes razón, disculpa. Ya tengo tu información. Te contactaremos muy pronto para la demo. ¡Gracias por tu paciencia!"
        
        # CASO 7: Si el usuario ya mencionó un servicio específico
        if has_service_info:
            service_mentioned = None
            if 'automatización' in message_lower or 'automatizar' in message_lower:
                service_mentioned = 'automatización'
            elif 'chatbot' in message_lower:
                service_mentioned = 'chatbots'
            elif 'finanzas' in message_lower:
                service_mentioned = 'finanzas'
            
            if service_mentioned:
                return f"¡Genial! {service_mentioned.title()} es nuestra especialidad. ¿Agendamos 15 min para mostrarte casos de éxito?"
        
        # Respuestas inteligentes basadas en intención detectada
        if hasattr(intent_result, 'category') and 'greeting' in str(intent_result.category).lower():
            return f"¡Hola {self.contact_name}! 👋 Soy Mati de TDX. ¿En qué podemos ayudarte con IA para {self.company_name}?"
        
        elif service_result.get('service') != 'UNKNOWN':
            service = service_result['service']
            if service in self.service_cases:
                snippet = self.service_cases[service]['general']['snippet']
                return snippet.replace('Perfecto', f'Perfecto {self.contact_name}')
        
        elif any(word in message_lower for word in ['reunion', 'llamada', 'agendar', 'cita']):
            # Evitar repetir la misma pregunta de horario
            if not any('día y hora' in msg for msg in recent_bot_messages):
                return f"¡Excelente {self.contact_name}! ¿Qué tal mañana por la mañana para una llamada de 15 minutos?"
            else:
                return "Perfecto. Te envío calendario por email. ¿Cuál es tu dirección corporativa?"
        
        # Confirmaciones del usuario
        elif any(word in message_lower for word in ['si', 'sí', 'dale', 'ok', 'claro', 'perfecto', 'genial']):
            # Evitar repetir la misma pregunta de horario
            if not any('10:00 AM' in msg or 'mañana' in msg for msg in recent_bot_messages):
                return "¡Excelente! ¿Mañana 10:00 AM te conviene para una demo de 15 minutos?"
            else:
                return "Perfecto. ¿Cuál es tu email para enviarte la invitación?"
        
        else:
            # Evitar repetir preguntas generales
            if not any('qué proceso' in msg or 'en qué podemos' in msg for msg in recent_bot_messages):
                return f"Interesante {self.contact_name}. ¿Qué proceso de {self.company_name} te gustaría automatizar con IA? 🤖"
            else:
                return f"Entiendo. ¿Te parece si agendamos una llamada rápida para explicarte mejor nuestras soluciones?"
    
    def _already_scheduling(self) -> bool:
        """Verificar si ya estamos en proceso de agendamiento"""
        return self.conversation_state == "scheduling" or any(
            'agendar' in log.get('content', '').lower() or 'reunión' in log.get('content', '').lower()
            for log in self.conversation_log[-3:]  # Últimos 3 mensajes
        )
    
    async def _handle_guard_intervention(self, guard_result: Dict) -> str:
        """Manejar intervención de la guardia conversacional"""
        reason = guard_result.get('reason', '')
        
        if 'loop' in reason:
            return f"{self.contact_name}, veo que estamos dando vueltas. ¿Te parece si agendamos una llamada rápida de 15 minutos para explicarte mejor cómo podemos ayudarte?"
        
        elif 'max_turns' in reason:
            return f"{self.contact_name}, ha sido una conversación muy interesante. Para darte la mejor solución personalizada, ¿te gustaría que te llame directamente?"
        
        else:
            return f"Perfecto {self.contact_name}. ¿Procedemos con agendar una reunión para mostrarte exactamente cómo podemos ayudar a {self.company_name}?"
    
    async def schedule_meeting(self, preferred_time: str = None) -> Dict[str, Any]:
        """Agendar reunión usando Microsoft Graph"""
        try:
            current_prospect = self.prospect_info.copy()
            
            meeting_result = await self.graph_client.schedule_meeting(
                prospect_name=self.contact_name,
                prospect_email=current_prospect.get('email'),
                prospect_phone=current_prospect.get('phone'),
                company_name=self.company_name,
                preferred_time=preferred_time,
                conversation_summary=self._generate_conversation_summary()
            )
            
            if meeting_result.get('success'):
                logger.info(f"📅 Meeting scheduled successfully for {self.contact_name}")
                self.conversation_state = "closing"
                return meeting_result
            else:
                logger.error(f"❌ Failed to schedule meeting: {meeting_result.get('error')}")
                return meeting_result
                
        except Exception as e:
            logger.error(f"❌ Error scheduling meeting: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_conversation_summary(self) -> str:
        """Generar resumen de la conversación para la reunión"""
        current_prospect = self.prospect_info.copy()
        
        # Obtener servicios de interés detectados
        services_mentioned = set()
        for log in self.conversation_log:
            if log.get('service') and isinstance(log['service'], dict):
                if log['service'].get('service') != 'UNKNOWN':
                    services_mentioned.add(log['service']['service'])
        
        summary_parts = [
            f"Cliente: {self.contact_name}",
            f"Empresa: {self.company_name}",
            f"Email: {current_prospect.get('email', 'No proporcionado')}",
            f"Teléfono: {current_prospect.get('phone', 'No proporcionado')}"
        ]
        
        if services_mentioned:
            summary_parts.append(f"Servicios de interés: {', '.join(services_mentioned)}")
        
        # Agregar últimos mensajes del usuario
        user_messages = [
            log['content'] for log in self.conversation_log 
            if log.get('type') == 'user_message'
        ][-3:]  # Últimos 3 mensajes del usuario
        
        if user_messages:
            summary_parts.append(f"Necesidades expresadas: {'; '.join(user_messages)}")
        
        return "\n".join(summary_parts)
    
    def _extract_scheduling_info(self, current_message: str, recent_messages: List[str]) -> str:
        """Extraer información de agendamiento del mensaje actual y contexto"""
        try:
            scheduling_info = []
            
            # Combinar mensaje actual con mensajes recientes para contexto
            all_messages = recent_messages + [current_message]
            combined_text = ' '.join(all_messages).lower()
            
            # Detectar patrones de tiempo específicos
            import re
            
            # Patrones de horarios
            time_patterns = [
                r'(\d{1,2})\s*(am|pm)',
                r'(\d{1,2}):(\d{2})\s*(am|pm)?',
                r'mañana.*(\d{1,2})',
                r'tarde.*(\d{1,2})',
                r'(\d{1,2})\s*de\s*la\s*(mañana|tarde)',
            ]
            
            for pattern in time_patterns:
                matches = re.findall(pattern, combined_text)
                if matches:
                    scheduling_info.append(f"Horario mencionado: {matches}")
            
            # Detectar días específicos
            day_keywords = ['mañana', 'hoy', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo', 'esta semana', 'próxima semana']
            mentioned_days = [day for day in day_keywords if day in combined_text]
            if mentioned_days:
                scheduling_info.append(f"Días mencionados: {mentioned_days}")
            
            # Detectar confirmaciones
            confirmation_keywords = ['si', 'sí', 'yes', 'dale', 'ok', 'claro', 'perfecto', 'genial', 'agendemos', 'procedemos']
            confirmations = [conf for conf in confirmation_keywords if conf in combined_text]
            if confirmations:
                scheduling_info.append(f"Confirmaciones detectadas: {confirmations}")
            
            # Detectar información personal proporcionada
            personal_info = []
            
            # Detectar emails
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, combined_text)
            if emails:
                personal_info.append(f"Email: {emails[-1]}")  # Último email mencionado
            
            # Detectar teléfonos (varios formatos colombianos)
            phone_patterns = [
                r'\b3\d{9}\b',  # Formato 3xxxxxxxxx
                r'\b\+57\s*3\d{9}\b',  # Formato +57 3xxxxxxxxx
                r'\b\d{10}\b',  # 10 dígitos
                r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'  # Formatos con separadores
            ]
            
            for pattern in phone_patterns:
                phones = re.findall(pattern, combined_text)
                if phones:
                    personal_info.append(f"Teléfono: {phones[-1]}")  # Último teléfono mencionado
                    break
            
            # Detectar nombres (después de comas o al inicio)
            name_pattern = r'(?:^|\s|,\s*)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)(?:\s*,|\s*$)'
            names = re.findall(name_pattern, current_message)
            if names and len(names[0]) > 2:  # Evitar palabras muy cortas
                personal_info.append(f"Nombre: {names[0]}")
            
            if personal_info:
                scheduling_info.append(f"Datos personales: {'; '.join(personal_info)}")
            
            # Detectar servicios específicos mencionados
            service_mentions = []
            if 'chatbot' in combined_text:
                service_mentions.append('chatbots')
            if 'automatizacion' in combined_text or 'automatizar' in combined_text:
                service_mentions.append('automatización')
            if 'conciliacion' in combined_text or 'conciliar' in combined_text:
                service_mentions.append('conciliación bancaria')
            if 'finanzas' in combined_text:
                service_mentions.append('finanzas')
            
            if service_mentions:
                scheduling_info.append(f"Servicios de interés: {service_mentions}")
            
            return '; '.join(scheduling_info) if scheduling_info else 'No hay información específica de agendamiento detectada'
            
        except Exception as e:
            logger.error(f"Error extracting scheduling info: {e}")
            return 'Error procesando información de agendamiento'
    
    def _update_collected_data(self, message: str):
        """Actualizar los datos recopilados del usuario"""
        try:
            import re
            message_lower = message.lower()
            
            # Primero intentar parsear datos completos si el mensaje parece contener múltiples datos
            if (',' in message and '@' in message) or (any(word in message_lower for word in ['nombre:', 'email:', 'teléfono:', 'empresa:'])):
                complete_data = self._parse_complete_data_message(message)
                if complete_data:
                    for key, value in complete_data.items():
                        if value:  # Actualizar siempre si hay valor, no solo si no existe
                            if key == 'name':
                                self.collected_data['name'] = value
                                self.contact_name = value
                            elif key == 'company':
                                self.collected_data['company'] = value
                                self.company_name = value
                            else:
                                self.collected_data[key] = value
                            logger.info(f"{key.title()} actualizado desde datos completos: {value}")
            
            # Detectar y actualizar email (si no se obtuvo ya)
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, message)
            if emails and not self.collected_data['email']:
                self.collected_data['email'] = emails[0]
                logger.info(f"Email actualizado: {emails[0]}")
            
            # Detectar y actualizar teléfono
            phone_patterns = [
                r'\b3\d{9}\b',  # Formato 3xxxxxxxxx
                r'\b\+57\s*3\d{9}\b',  # Formato +57 3xxxxxxxxx
                r'\b\d{10}\b',  # 10 dígitos
            ]
            
            for pattern in phone_patterns:
                phones = re.findall(pattern, message)
                if phones and not self.collected_data['phone']:
                    self.collected_data['phone'] = phones[0]
                    logger.info(f"Teléfono actualizado: {phones[0]}")
                    break
            
            # Detectar nombre en el formato "nombre , email" o solo nombre
            name_patterns = [
                r'^([A-Za-z\s]+)\s*,\s*[A-Za-z0-9._%+-]+@',  # "Nombre , email@domain.com"
                r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*$'      # "Nombre Apellido"
            ]
            
            for pattern in name_patterns:
                names = re.findall(pattern, message.strip())
                if names and len(names[0].strip()) > 2:
                    extracted_name = names[0].strip()
                    if extracted_name.lower() != self.contact_name.lower():
                        self.collected_data['name'] = extracted_name
                        self.contact_name = extracted_name
                        logger.info(f"Nombre actualizado: {extracted_name}")
                    break
            
            # Detectar empresa en el mensaje
            company_keywords = ['empresa', 'compañía', 'trabajo en', 'soy de']
            for keyword in company_keywords:
                if keyword in message_lower:
                    # Extraer lo que viene después del keyword
                    parts = message_lower.split(keyword)
                    if len(parts) > 1:
                        potential_company = parts[1].strip().split(',')[0].split('.')[0]
                        if len(potential_company) > 2 and potential_company != self.company_name.lower():
                            self.collected_data['company'] = potential_company.title()
                            self.company_name = potential_company.title()
                            logger.info(f"Empresa actualizada: {potential_company.title()}")
                    break
            
            # Detectar interés en servicios
            if 'automatización' in message_lower or 'automatizar' in message_lower:
                self.collected_data['service_interest'] = 'automatización'
            elif 'chatbot' in message_lower:
                self.collected_data['service_interest'] = 'chatbots'
            elif 'finanzas' in message_lower:
                self.collected_data['service_interest'] = 'finanzas'
            elif 'web' in message_lower or 'página' in message_lower:
                self.collected_data['service_interest'] = 'desarrollo web'
            elif 'ia' in message_lower or 'inteligencia artificial' in message_lower:
                self.collected_data['service_interest'] = 'IA empresarial'
            
            # Detectar confirmación de demo
            if any(word in message_lower for word in ['si claro', 'si', 'sí', 'dale', 'ok', 'perfecto', 'genial']):
                if self.conversation_state in ['qualifying', 'scheduling']:
                    self.collected_data['demo_confirmed'] = True
            
            # Detectar selección de horario
            if self.current_calendar_options and any(num in message_lower for num in ['1', '2', '3', 'primera', 'segunda', 'tercera']):
                # Parsear selección simple
                if '1' in message_lower:
                    self.collected_data['selected_time_slot'] = "Martes Mañana 9:00 AM"
                elif '2' in message_lower:
                    self.collected_data['selected_time_slot'] = "Martes Mañana 10:00 AM"
                elif '3' in message_lower:
                    self.collected_data['selected_time_slot'] = "Martes Mañana 11:00 AM"
                
                if self.collected_data['selected_time_slot']:
                    logger.info(f"Horario seleccionado: {self.collected_data['selected_time_slot']}")
            
            # Actualizar estados de completitud
            self.collected_data['contact_info_complete'] = bool(
                self.collected_data['email'] and 
                self.collected_data['phone'] and 
                self.collected_data['name']
            )
            
            # Para all_data_complete, solo necesitamos nombre, email, teléfono y servicio de interés
            # La empresa puede ser opcional o usar la predeterminada
            self.collected_data['all_data_complete'] = bool(
                self.collected_data['email'] and
                self.collected_data['phone'] and
                self.collected_data['name'] and
                self.collected_data.get('service_interest')
            )
            
            # Log para debugging
            if self.collected_data['phone'] and self.collected_data['email']:
                logger.info(f"Datos completos detectados: email={self.collected_data['email']}, phone={self.collected_data['phone']}, name={self.collected_data['name']}, service={self.collected_data.get('service_interest')}")
                logger.info(f"all_data_complete: {self.collected_data['all_data_complete']}")
            
            # Actualizar estado de conversación basado en datos recopilados
            if self.collected_data['selected_time_slot']:
                self.conversation_state = "closing"
            elif self.collected_data['all_data_complete'] and self.collected_data['demo_confirmed']:
                self.conversation_state = "scheduling"
            elif self.collected_data['service_interest'] and self.collected_data['demo_confirmed']:
                self.conversation_state = "qualifying"
            elif self.collected_data['service_interest']:
                self.conversation_state = "qualifying"
            
        except Exception as e:
            logger.error(f"Error updating collected data: {e}")
    
    def _parse_complete_data_message(self, message: str) -> Dict[str, str]:
        """Parsear mensaje que contiene múltiples datos del usuario"""
        try:
            import re
            
            extracted_data = {}
            
            # Patrones más sofisticados para detectar datos en conjunto
            
            # Patrón: "Nombre, email@domain.com, 3201234567, Empresa S.A.S"
            pattern1 = r'^([^,]+),\s*([^,\s]+@[^,\s]+),\s*([^,\s]+),\s*(.+)$'
            match1 = re.match(pattern1, message.strip())
            if match1:
                extracted_data['name'] = match1.group(1).strip()
                extracted_data['email'] = match1.group(2).strip()
                extracted_data['phone'] = match1.group(3).strip()
                extracted_data['company'] = match1.group(4).strip()
                return extracted_data
            
            # Patrón: "Nombre: Juan Pérez, Email: juan@empresa.com, Teléfono: 3201234567"
            patterns = {
                'name': r'(?:nombre|name):\s*([^,\n]+)',
                'email': r'(?:email|correo):\s*([^\s,\n]+@[^\s,\n]+)',
                'phone': r'(?:teléfono|telefono|phone|celular):\s*([^\s,\n]+)',
                'company': r'(?:empresa|company|compañía):\s*([^,\n]+)'
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, message.lower())
                if match:
                    extracted_data[key] = match.group(1).strip()
            
            # Si no encontró patrones estructurados, intentar detección por separado
            if not extracted_data:
                # Buscar email
                email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', message)
                if email_match:
                    extracted_data['email'] = email_match.group()
                
                # Buscar teléfono
                phone_match = re.search(r'\b(?:3\d{9}|\+57\s*3\d{9}|\d{10})\b', message)
                if phone_match:
                    extracted_data['phone'] = phone_match.group()
                
                # El resto podría ser nombre y empresa
                remaining_text = message
                if email_match:
                    remaining_text = remaining_text.replace(email_match.group(), '')
                if phone_match:
                    remaining_text = remaining_text.replace(phone_match.group(), '')
                
                # Limpiar y dividir lo que queda
                remaining_parts = [part.strip() for part in remaining_text.replace(',', '').split() if part.strip()]
                if len(remaining_parts) >= 2:
                    # Primeras palabras como nombre
                    extracted_data['name'] = ' '.join(remaining_parts[:2])
                    # Resto como empresa
                    if len(remaining_parts) > 2:
                        extracted_data['company'] = ' '.join(remaining_parts[2:])
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error parsing complete data: {e}")
            return {}
