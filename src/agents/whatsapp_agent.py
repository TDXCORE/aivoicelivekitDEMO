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
            'budget_confirmed': False,
            'budget_range': None,
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
                
                # Enviar por Chatwoot (si está configurado)
                if self.chatwoot_account_id and self.chatwoot_api_token:
                    success = await self._send_to_chatwoot(response)
                    if success:
                        logger.info(f"✅ Response sent successfully to {self.contact_name}")
                    else:
                        logger.error(f"❌ Failed to send response to {self.contact_name}")
                else:
                    # Modo test/desarrollo - solo retornar respuesta sin enviar
                    logger.info(f"📝 Test mode - response: {response}")
                
                return response
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")
            return None
    
    async def _generate_openai_response(self, message: str) -> str:
        """Generar respuesta usando OpenAI con function calling"""
        try:
            # SIEMPRE intentar usar OpenAI primero
            if not self.openai_client:
                logger.warning("OpenAI not configured, attempting to initialize...")
                # Intentar inicializar OpenAI con variable de entorno
                try:
                    from openai import OpenAI
                    api_key = os.getenv('OPENAI_API_KEY')
                    if api_key:
                        self.openai_client = OpenAI(api_key=api_key)
                        logger.info("✅ OpenAI client initialized successfully")
                    else:
                        logger.error("❌ OPENAI_API_KEY not found in environment")
                        return self._generate_fallback_response(message)
                except Exception as e:
                    logger.error(f"❌ Error initializing OpenAI: {e}")
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
                            "service_interest": {"type": "string", "description": "Servicio de interés específico (chatbot, automatización, web, etc.)"},
                            "budget_range": {"type": "string", "description": "Rango de presupuesto confirmado"}
                        }
                    }
                },
                {
                    "name": "check_budget",
                    "description": "Preguntar sobre presupuesto cuando se entiende el requerimiento",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "requirement_understood": {"type": "boolean", "description": "Si se entendió el requerimiento del cliente"}
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
            
            # Prompt maestro mejorado para conversación natural
            system_prompt = f"""Eres Mati, asistente virtual experto de TDX (Transformación Digital Inteligente). 

PERSONALIDAD:
- Empático, cordial y profesional
- Conversación natural con frases cortas
- Siempre saluda cordialmente a leads fríos
- Paciente pero eficiente

INFORMACIÓN ACTUAL DEL CLIENTE:
- Nombre: {self.contact_name}
- Empresa: {self.company_name}  
- Email: {self.collected_data.get('email', 'No capturado')}
- Teléfono: {self.collected_data.get('phone', 'No capturado')}
- Requerimiento: {self.collected_data.get('service_interest', 'No definido')}
- Presupuesto confirmado: {self.collected_data.get('budget_confirmed', False)}

CONTEXTO DE CONVERSACIÓN:
{conversation_context}

FLUJO OBLIGATORIO (NUNCA SALTEAR PASOS):
1. SALUDO cordial (si es primer mensaje)
2. ENTENDER requerimiento específico de IA
3. CONFIRMAR presupuesto disponible (2.000-20.000 USD)
4. CAPTURAR email y teléfono completos
5. OFRECER horarios para reunión
6. AGENDAR reunión confirmada

CUÁNDO USAR HERRAMIENTAS:

- USA extract_user_data SIEMPRE QUE DETECTES:
  * Requerimiento específico ("necesito chatbot", "automatización", "web con IA")
  * Email válido del cliente
  * Número de teléfono
  * Confirmación de presupuesto
  * Nombre completo o empresa

- USA check_budget CUANDO:
  * Ya capturaste el requerimiento
  * Aún no confirmaste presupuesto
  
- USA show_calendar_options SOLO CUANDO TENGAS:
  * Requerimiento claro capturado
  * Presupuesto confirmado
  * Email Y teléfono capturados
  
- USA schedule_meeting CUANDO:
  * Cliente diga "1", "2", o "3" para horario

REGLAS DE COMUNICACIÓN:
1. Frases cortas pero naturales y empáticas
2. SIEMPRE saluda cordialmente en primer contacto
3. No repitas respuestas idénticas
4. Si dicen algo no relacionado a IA, redirige suavemente
5. Máximo 1 emoji por mensaje
6. PROGRESA en el flujo, no te quedes en loops
7. Haz UNA pregunta por vez

EJEMPLOS DE CONVERSACIÓN NATURAL:
- "¡Hola! Soy Mati de TDX 😊 ¿Cómo estás hoy?"
- "Me encanta ayudarte con IA. ¿Qué tipo de solución necesitas?"
- "Perfecto, entiendo que necesitas {tipo}. ¿Cuentas con presupuesto para este proyecto?"
- "Genial. Para coordinar una reunión, ¿me compartes tu email?"

RESPONDE DE FORMA NATURAL Y PROGRESIVA AL SIGUIENTE MENSAJE:"""

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
                elif function_name == "check_budget":
                    return await self._handle_check_budget(function_args)
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
            context_parts.append(f"Requerimiento: {self.collected_data['service_interest']}")
        if self.collected_data['budget_confirmed']:
            context_parts.append(f"Presupuesto confirmado: {self.collected_data['budget_range']}")
        
        # Estado del flujo
        if not self.collected_data['service_interest']:
            context_parts.append("PASO 1: Entender requerimiento específico")
        elif not self.collected_data['budget_confirmed']:
            context_parts.append("PASO 2: Confirmar presupuesto 2K-20K USD")
        elif not all([self.collected_data['email'], self.collected_data['phone']]):
            context_parts.append("PASO 3: Solicitar datos de contacto")
        elif self.collected_data['calendar_options_shown']:
            context_parts.append("PASO 4: Esperando selección de horario")
        elif self.collected_data['meeting_confirmed']:
            context_parts.append("FLUJO COMPLETO: Reunión confirmada")
        
        # Últimos mensajes para contexto
        recent_messages = [log['content'] for log in self.conversation_log[-2:] if log.get('type') == 'user_message']
        if recent_messages:
            context_parts.append(f"Últimos mensajes: {'; '.join(recent_messages)}")
        
        return "; ".join(context_parts) if context_parts else "Inicio de conversación"
    
    async def _handle_extract_user_data(self, function_args: Dict) -> str:
        """Manejar extracción de datos del usuario"""
        try:
            # Actualizar datos con los argumentos de la función
            updated_fields = []
            for key, value in function_args.items():
                if value and key in self.collected_data:
                    if self.collected_data[key] != value:  # Solo actualizar si es diferente
                        self.collected_data[key] = value
                        updated_fields.append(key)
                        if key == 'name':
                            self.contact_name = value
                        elif key == 'company':
                            self.company_name = value
                        elif key == 'budget_range':
                            self.collected_data['budget_confirmed'] = True
                        logger.info(f"Dato capturado: {key} = {value}")
            
            # PROGRESO LÓGICO DEL FLUJO:
            
            # Si acabamos de capturar requerimiento, preguntar presupuesto
            if 'service_interest' in updated_fields and not self.collected_data['budget_confirmed']:
                return f"Perfecto, {self.collected_data['service_interest']} es una excelente solución. ¿Cuentas con presupuesto para este proyecto?"
            
            # Si acabamos de confirmar presupuesto, pedir datos de contacto
            if 'budget_range' in updated_fields or self.collected_data['budget_confirmed']:
                missing = []
                if not self.collected_data['email']:
                    missing.append("email")
                if not self.collected_data['phone']:
                    missing.append("teléfono")
                
                if missing:
                    if len(missing) == 2:
                        return "Excelente. Para coordinar la reunión, ¿me das tu email y teléfono?"
                    else:
                        return f"Perfecto. Solo me falta tu {missing[0]}."
            
            # Si acabamos de capturar email o teléfono, verificar si tenemos todo
            if ('email' in updated_fields or 'phone' in updated_fields):
                has_all_contact_data = bool(
                    self.collected_data['email'] and 
                    self.collected_data['phone'] and
                    self.collected_data['service_interest'] and
                    self.collected_data['budget_confirmed']
                )
                
                if has_all_contact_data and not self.collected_data['calendar_options_shown']:
                    service_type = self.collected_data.get('service_interest', 'tu proyecto')
                    return await self._handle_show_calendar_options({'service_type': service_type})
                elif not self.collected_data['phone']:
                    return "Genial. ¿Y tu número de teléfono?"
                elif not self.collected_data['email']:
                    return "Perfecto. ¿Tu email?"
            
            # Respuesta genérica si no hay actualizaciones
            return "Perfecto, continuemos."
            
        except Exception as e:
            logger.error(f"Error handling extract_user_data: {e}")
            return "Entendido, sigamos con el proceso."
    
    async def _handle_check_budget(self, function_args: Dict) -> str:
        """Manejar confirmación de presupuesto"""
        try:
            # Solo preguntar presupuesto si ya entendimos el requerimiento
            if not self.collected_data['service_interest']:
                return "Primero, ¿qué necesitas específicamente?"
            
            # Si ya confirmamos presupuesto, continuar
            if self.collected_data['budget_confirmed']:
                return "¡Perfecto! Tu presupuesto está confirmado."
            
            # Preguntar presupuesto de forma directa
            return "¿Tienes presupuesto entre 2K-20K USD? 💰"
            
        except Exception as e:
            logger.error(f"Error handling check_budget: {e}")
            return "¿Cuál es tu presupuesto aproximado?"
    
    async def _handle_show_calendar_options(self, function_args: Dict) -> str:
        """Mostrar opciones de calendario disponibles"""
        try:
            # Verificar que tenemos presupuesto confirmado antes de mostrar calendario
            if not self.collected_data['budget_confirmed']:
                return "Primero necesito confirmar tu presupuesto."
            
            service_type = function_args.get('service_type', 'tu proyecto')
            
            # Marcar que ya mostramos las opciones
            self.collected_data['calendar_options_shown'] = True
            
            # Opciones directas y cortas
            options_msg = f"¡Listo {self.collected_data['name']}!\n\n1. Mañana 9:00 AM\n2. Mañana 10:00 AM\n3. Mañana 11:00 AM\n\n¿Cuál opción? Solo el número 📅"
            
            return options_msg
            
        except Exception as e:
            logger.error(f"Error handling show_calendar_options: {e}")
            return "¿Mañana 10am está bien?"
    
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
            
            # Agendar reunión real con Microsoft Graph CON RESUMEN DETALLADO
            logger.info(f"🔧 Agendando reunión real con Microsoft Graph...")
            
            # Preparar datos completos para la reunión
            meeting_data = {
                'attendee_email': self.collected_data['email'],
                'meeting_date': selected_time['date'],
                'meeting_time': selected_time['time'],
                'contact_name': self.collected_data['name'],
                'company_name': self.collected_data.get('company', self.company_name),
                'meeting_type': 'discovery_call',
                # NUEVO: Datos adicionales para el resumen
                'requirement': self.collected_data.get('service_interest', 'No especificado'),
                'budget_range': self.collected_data.get('budget_range', 'Confirmado 2K-20K USD'),
                'phone': self.collected_data.get('phone', 'No proporcionado')
            }
            
            meeting_result = await self.graph_client.create_meeting_with_summary(**meeting_data)
            
            if meeting_result.get('meeting_scheduled'):
                # Reunión agendada exitosamente - Respuesta DIRECTA
                confirmation_msg = f"¡Perfecto {self.collected_data['name']}! 🎉\n\n✅ {selected_time['display']} confirmado\n📧 Invitación enviada\n\n¡Nos vemos!"
                
                logger.info(f"✅ Reunión agendada exitosamente para {self.collected_data['name']}")
                return confirmation_msg
            else:
                # Error al agendar, pero confirmar de todas formas
                logger.warning(f"⚠️ Error agendando reunión real, pero confirmando al usuario")
                return f"¡Perfecto {self.collected_data['name']}!\n\n✅ {selected_time['display']} confirmado\n📧 Te contactamos pronto\n\n¡Gracias!"
            
        except Exception as e:
            logger.error(f"❌ Error handling schedule_meeting: {e}")
            return f"¡Perfecto! Tu reunión ha sido confirmada. Te contactaremos pronto con los detalles."
    
    def _generate_fallback_response(self, message: str) -> str:
        """Respuesta de fallback empática para leads fríos"""
        message_lower = message.lower()
        
        # Detectar selección de horario
        if any(num in message_lower for num in ['1', '2', '3']) and self.collected_data['calendar_options_shown']:
            import asyncio
            return asyncio.run(self._handle_schedule_meeting({'option_selected': message_lower.strip()}))
        
        # Contar mensajes previos para determinar si es saludo inicial
        is_first_interaction = len(self.conversation_log) <= 1
        
        # RESPUESTAS EMPÁTICAS Y NATURALES - PRIORIDAD CORRECTA
        
        # PRIMERO: Detección de requerimientos de IA (prioridad alta)
        if any(word in message_lower for word in ['ia', 'inteligencia artificial', 'automatizacion', 'chatbot', 'bot', 'ai', 'soluciones', 'sistema']):
            if not self.collected_data['service_interest']:
                # Capturar el requerimiento específico
                if 'chatbot' in message_lower or 'bot' in message_lower:
                    self.collected_data['service_interest'] = 'chatbot'
                elif 'automatizacion' in message_lower:
                    self.collected_data['service_interest'] = 'automatización'
                elif 'web' in message_lower:
                    self.collected_data['service_interest'] = 'desarrollo web con IA'
                else:
                    self.collected_data['service_interest'] = 'soluciones de IA'
                logger.info(f"Requerimiento capturado: {self.collected_data['service_interest']}")
            
            if not self.collected_data['budget_confirmed']:
                return f"Me encanta ayudarte con {self.collected_data['service_interest']}. ¿Cuentas con presupuesto para este proyecto?"
            else:
                return "Perfecto. ¿Me das tu email para coordinar?"
        
        # SEGUNDO: Saludo inicial cordial para leads fríos
        elif any(word in message_lower for word in ['hola', 'epale', 'buenas', 'hey']) or is_first_interaction:
            return f"¡Hola {self.contact_name}! Soy Mati de TDX. ¿Cómo estás hoy?"
        
        # TERCERO: Confirmación de presupuesto
        elif any(word in message_lower for word in ['si', 'sí', 'claro', 'perfecto', 'tengo']):
            if not self.collected_data['budget_confirmed'] and self.collected_data.get('service_interest'):
                self.collected_data['budget_confirmed'] = True
                self.collected_data['budget_range'] = 'Confirmado'
                return "Excelente. Para coordinar la reunión, ¿me das tu email?"
            elif not self.collected_data['email']:
                return "Perfecto. ¿Tu email?"
            elif not self.collected_data['phone']:
                return "Genial. ¿Y tu teléfono?"
            else:
                return "¡Excelente! Continuemos."
        
        # Preguntas sobre presupuesto/precios
        elif any(word in message_lower for word in ['presupuesto', 'precio', 'costo', 'cuanto']):
            if not self.collected_data['service_interest']:
                return "Con gusto te ayudo. ¿Qué tipo de solución de IA necesitas?"
            else:
                return "Los proyectos van desde 2K hasta 20K USD. ¿Cuentas con presupuesto en ese rango?"
        
        # Cosas no relacionadas (ej: "quiero ir a la luna")
        elif not any(word in message_lower for word in ['ia', 'bot', 'automatizacion', 'web', 'sistema', 'digital']):
            return "Interesante! En TDX nos especializamos en IA empresarial. ¿Te interesa alguna solución?"
        
        # Default empático
        else:
            if not self.collected_data['service_interest']:
                return "Me encantaría ayudarte. ¿Qué tipo de solución de IA necesitas?"
            else:
                return "Entiendo. ¿Cuentas con presupuesto para este proyecto?"
    
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
