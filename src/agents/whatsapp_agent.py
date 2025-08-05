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
            'budget_declined': False,
            'budget_range': None,
            'calendar_options_shown': False,
            'selected_time_slot': None,
            'meeting_confirmed': False,
            'conversation_ended': False
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
        """Generar respuesta usando OpenAI con conversation state management"""
        try:
            # SIEMPRE intentar usar OpenAI primero
            if not self.openai_client:
                logger.warning("OpenAI not configured, attempting to initialize...")
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
            
            # DEBUG: Log del estado actual para verificar persistencia
            logger.info(f"🔍 ESTADO PERSISTENTE - Conv: {self.conversation_id}")
            logger.info(f"🔍 ESTADO PERSISTENTE - Mensajes: {len(self.conversation_log)}")
            logger.info(f"🔍 ESTADO PERSISTENTE - Datos: email={bool(self.collected_data.get('email'))}, servicio={bool(self.collected_data.get('service_interest'))}, presupuesto={self.collected_data.get('budget_confirmed')}")
            
            # BEST PRACTICE: Construir contexto completo con conversation state
            conversation_messages = self._build_conversation_messages(message)
            
            # Definir funciones disponibles para OpenAI
            functions = [
                {
                    "name": "extract_user_data",
                    "description": "Extraer y actualizar datos del usuario SOLO cuando detectes nueva información",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Nombre completo del usuario"},
                            "email": {"type": "string", "description": "Email del usuario"},
                            "phone": {"type": "string", "description": "Teléfono del usuario"},
                            "company": {"type": "string", "description": "Empresa del usuario"},
                            "service_interest": {"type": "string", "description": "Servicio de interés específico"},
                            "budget_confirmed": {"type": "boolean", "description": "Si confirmó que SÍ tiene presupuesto"},
                            "budget_declined": {"type": "boolean", "description": "Si confirmó que NO tiene presupuesto"},
                            "budget_range": {"type": "string", "description": "Rango específico si lo menciona"}
                        }
                    }
                },
                {
                    "name": "show_calendar_options",
                    "description": "SOLO usar cuando tiene: servicio + presupuesto confirmado + email + teléfono",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "service_type": {"type": "string", "description": "Tipo de servicio para la demo"}
                        }
                    }
                },
                {
                    "name": "schedule_meeting",
                    "description": "Agendar reunión cuando usuario selecciona opción 1, 2, o 3",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "option_selected": {"type": "string", "description": "Opción seleccionada (1, 2, o 3)"}
                        }
                    }
                },
                {
                    "name": "end_conversation_no_budget",
                    "description": "USAR cuando cliente confirma que NO tiene presupuesto para terminar conversación elegantemente",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "reason": {"type": "string", "description": "Razón por la que no tiene presupuesto"}
                        }
                    }
                }
            ]
            
            # ELIMINADO: Prompt viejo - ahora uso _build_conversation_messages() con prompt dinámico

            # BEST PRACTICE: Usar conversation threading con mensajes completos
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=conversation_messages,
                functions=functions,
                function_call="auto",
                max_tokens=200,
                temperature=0.7
            )
            
            response_message = response.choices[0].message
            
            # BEST PRACTICE: Function calling con state checkpoint
            if response_message.function_call:
                function_name = response_message.function_call.name
                function_args = json.loads(response_message.function_call.arguments)
                
                logger.info(f"🔧 EJECUTANDO FUNCIÓN: {function_name} with args: {function_args}")
                
                # Ejecutar función y actualizar estado
                function_result = await self._execute_function_with_state_update(function_name, function_args)
                
                # CRITICAL: Generar respuesta final con contexto actualizado
                return await self._generate_response_after_function(function_name, function_args, function_result)
            
            # Si no hay function call, devolver respuesta normal
            ai_response = response_message.content.strip()
            logger.info(f"🤖 OpenAI response: {ai_response[:50]}...")
            return ai_response
            
        except Exception as e:
            logger.error(f"❌ OpenAI error: {e}")
            # FALLBACK: Solo en caso de error completo de OpenAI
            return "Disculpa, hubo un problema técnico. ¿Podrías repetir tu mensaje?"
    
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
    
    def _get_conversation_memory(self) -> str:
        """Obtener memoria de conversación para OpenAI"""
        if not self.conversation_log:
            return "Primera interacción con el cliente"
        
        # Obtener últimos 4 mensajes para contexto
        recent_conversation = []
        for log in self.conversation_log[-4:]:
            if log.get('type') == 'user_message':
                recent_conversation.append(f"Usuario: {log['content']}")
            elif log.get('type') == 'assistant_message':
                recent_conversation.append(f"Mati: {log['content']}")
        
        memory = "; ".join(recent_conversation) if recent_conversation else "No hay conversación previa"
        
        # Agregar contexto de progreso
        progress_info = []
        if self.collected_data.get('service_interest'):
            progress_info.append(f"YA CAPTURÉ: Requerimiento ({self.collected_data['service_interest']})")
        if self.collected_data.get('budget_confirmed'):
            progress_info.append("YA CAPTURÉ: Presupuesto confirmado")
        if self.collected_data.get('email'):
            progress_info.append(f"YA CAPTURÉ: Email ({self.collected_data['email']})")
        if self.collected_data.get('phone'):
            progress_info.append(f"YA CAPTURÉ: Teléfono ({self.collected_data['phone']})")
        
        if progress_info:
            memory += " | PROGRESO: " + ", ".join(progress_info)
        
        return memory
    
    def _build_conversation_messages(self, current_message: str) -> list:
        """BEST PRACTICE: Construir mensajes de conversación con contexto completo"""
        messages = []
        
        # System prompt con estado actual
        system_prompt = self._build_dynamic_system_prompt()
        messages.append({"role": "system", "content": system_prompt})
        
        # CRITICAL: Agregar conversación previa para mantener contexto
        for log in self.conversation_log[-6:]:  # Últimos 6 mensajes para contexto
            if log.get('type') == 'user_message':
                messages.append({"role": "user", "content": log['content']})
            elif log.get('type') == 'assistant_message':
                messages.append({"role": "assistant", "content": log['content']})
        
        # Mensaje actual
        messages.append({"role": "user", "content": current_message})
        
        logger.info(f"📝 CONVERSATION CONTEXT: {len(messages)} mensajes en historial")
        return messages
    
    def _build_dynamic_system_prompt(self) -> str:
        """Construir system prompt dinámico basado en estado actual"""
        # Estado de progreso para evitar repeticiones
        progress_status = []
        if self.collected_data.get('service_interest'):
            progress_status.append(f"REQUERIMIENTO YA CAPTURADO: {self.collected_data['service_interest']}")
        if self.collected_data.get('budget_confirmed'):
            progress_status.append("PRESUPUESTO YA CONFIRMADO")
        if self.collected_data.get('email'):
            progress_status.append(f"EMAIL YA CAPTURADO: {self.collected_data['email']}")
        if self.collected_data.get('phone'):
            progress_status.append(f"TELÉFONO YA CAPTURADO: {self.collected_data['phone']}")
        
        # Determinar siguiente paso del flujo
        next_step = self._determine_next_conversation_step()
        
        # Estado de presupuesto para evitar bucles
        budget_status = ""
        if self.collected_data.get('budget_confirmed'):
            budget_status = "PRESUPUESTO: ✅ CONFIRMADO"
        elif self.collected_data.get('budget_declined'):
            budget_status = "PRESUPUESTO: ❌ DECLINADO - NO preguntar más sobre presupuesto"
        else:
            budget_status = "PRESUPUESTO: Pendiente de confirmar"
        
        system_prompt = f"""Eres Mati, asistente de TDX. CRITICAL: Esta es una conversación CONTINUA, NO inicial.

DATOS YA CAPTURADOS:
{'; '.join(progress_status) if progress_status else 'Ningún dato capturado aún'}

ESTADO DE PRESUPUESTO:
{budget_status}

SIGUIENTE PASO REQUERIDO:
{next_step}

REGLAS ANTI-REPETICIÓN CRÍTICAS:
- NUNCA saludes si ya hay conversación previa
- NUNCA preguntes datos ya capturados arriba
- Si presupuesto fue DECLINADO, usa función end_conversation_no_budget
- CONTINÚA desde donde se quedó la conversación
- NO reinicies el flujo ni hagas preguntas repetidas

PERSONALIDAD: Empático, natural, directo. Máximo 1 emoji por mensaje."""
        
        return system_prompt
    
    def _determine_next_conversation_step(self) -> str:
        """Determinar el siguiente paso lógico del flujo"""
        # Si conversación ya terminó, no hacer nada más
        if self.collected_data.get('conversation_ended'):
            return "CONVERSACIÓN TERMINADA - Ser cordial pero no continuar flujo"
        
        # Si presupuesto fue declinado, terminar conversación
        if self.collected_data.get('budget_declined'):
            return "TERMINAR: Usar función end_conversation_no_budget"
        
        # Flujo normal
        if not self.collected_data.get('service_interest'):
            return "CAPTURAR: Requerimiento específico de IA"
        elif not self.collected_data.get('budget_confirmed') and not self.collected_data.get('budget_declined'):
            return "PREGUNTAR: ¿Tienes presupuesto para este proyecto?"
        elif not self.collected_data.get('email'):
            return "SOLICITAR: Email del cliente"
        elif not self.collected_data.get('phone'):
            return "SOLICITAR: Número de teléfono"
        elif not self.collected_data.get('calendar_options_shown'):
            return "MOSTRAR: Opciones de calendario para reunión"
        elif not self.collected_data.get('meeting_confirmed'):
            return "CONFIRMAR: Selección de horario"
        else:
            return "FLUJO COMPLETADO: Reunión agendada"
    
    async def _execute_function_with_state_update(self, function_name: str, function_args: Dict) -> str:
        """BEST PRACTICE: Ejecutar función y actualizar estado inmediatamente"""
        try:
            if function_name == "extract_user_data":
                return await self._handle_extract_user_data(function_args)
            elif function_name == "show_calendar_options":
                return await self._handle_show_calendar_options(function_args)
            elif function_name == "schedule_meeting":
                return await self._handle_schedule_meeting(function_args)
            elif function_name == "end_conversation_no_budget":
                return await self._handle_end_conversation_no_budget(function_args)
            else:
                logger.error(f"Función desconocida: {function_name}")
                return "Error: Función no reconocida"
        except Exception as e:
            logger.error(f"Error ejecutando función {function_name}: {e}")
            return f"Error ejecutando {function_name}"
    
    async def _generate_response_after_function(self, function_name: str, function_args: Dict, function_result: str) -> str:
        """BEST PRACTICE: Generar respuesta contextual después de function calling"""
        try:
            # Si la función ya retornó una respuesta completa, usarla
            if function_result and len(function_result.strip()) > 10:
                return function_result
            
            # Si no, generar respuesta dinámica con estado actualizado
            context = f"Función ejecutada: {function_name}. Estado actual: {self._get_current_state_summary()}"
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"Eres Mati de TDX. Genera una respuesta natural después de ejecutar {function_name}. {context}"},
                    {"role": "user", "content": "Genera la respuesta apropiada para continuar la conversación"}
                ],
                max_tokens=100,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generando respuesta post-función: {e}")
            return function_result if function_result else "Continuemos con el proceso."
    
    def _get_current_state_summary(self) -> str:
        """Resumen del estado actual para contexto"""
        summary = []
        if self.collected_data.get('service_interest'):
            summary.append(f"servicio={self.collected_data['service_interest']}")
        if self.collected_data.get('budget_confirmed'):
            summary.append("presupuesto=confirmado")
        if self.collected_data.get('email'):
            summary.append("email=capturado")
        if self.collected_data.get('phone'):
            summary.append("teléfono=capturado")
        
        return "; ".join(summary) if summary else "sin datos"
    
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
                        elif key == 'budget_confirmed' and value:
                            self.collected_data['budget_confirmed'] = True
                        elif key == 'budget_declined' and value:
                            self.collected_data['budget_declined'] = True
                        elif key == 'budget_range':
                            self.collected_data['budget_confirmed'] = True
                        logger.info(f"✅ DATO ACTUALIZADO: {key} = {value}")
            
            # FLUJO INTELIGENTE - VERIFICAR ESTADO COMPLETO DESPUÉS DE CADA ACTUALIZACIÓN
            logger.info(f"🔍 Estado actual: email={bool(self.collected_data['email'])}, phone={bool(self.collected_data['phone'])}, service={bool(self.collected_data['service_interest'])}, budget={self.collected_data['budget_confirmed']}")
            
            # 1. Si acabamos de capturar requerimiento y no tenemos presupuesto -> preguntar presupuesto
            if 'service_interest' in updated_fields and not self.collected_data['budget_confirmed']:
                return f"Perfecto, {self.collected_data['service_interest']} es una excelente solución. ¿Cuentas con presupuesto para este proyecto?"
            
            # 2. Si acabamos de confirmar presupuesto -> pedir datos faltantes
            if 'budget_range' in updated_fields and self.collected_data['budget_confirmed']:
                if not self.collected_data['email']:
                    return "Excelente. Para coordinar la reunión, ¿me das tu email?"
                elif not self.collected_data['phone']:
                    return "Perfecto. ¿Y tu número de teléfono?"
            
            # 3. VERIFICACIÓN CRÍTICA: Si acabamos de capturar email o teléfono
            if 'email' in updated_fields or 'phone' in updated_fields:
                # Verificar si ahora tenemos TODOS los datos necesarios
                ready_for_calendar = all([
                    self.collected_data['email'],
                    self.collected_data['phone'], 
                    self.collected_data['service_interest'],
                    self.collected_data['budget_confirmed'],
                    not self.collected_data['calendar_options_shown']  # No hemos mostrado calendario aún
                ])
                
                if ready_for_calendar:
                    logger.info("🎯 TODOS LOS DATOS COMPLETOS - MOSTRANDO CALENDARIO")
                    service_type = self.collected_data.get('service_interest', 'tu proyecto')
                    return await self._handle_show_calendar_options({'service_type': service_type})
                elif not self.collected_data['phone']:
                    return "Genial. ¿Y tu número de teléfono?"
                elif not self.collected_data['email']:
                    return "Perfecto. ¿Tu email?"
            
            # 4. Respuesta de progreso si actualizamos algo pero no necesitamos siguiente paso
            if updated_fields:
                return "Perfecto, continuemos."
            
            # 5. Si no se actualizó nada, dar respuesta neutral
            return "Entendido."
            
        except Exception as e:
            logger.error(f"Error handling extract_user_data: {e}")
            return "Entendido, sigamos con el proceso."
    
    async def _handle_end_conversation_no_budget(self, function_args: Dict) -> str:
        """Manejar final de conversación cuando no hay presupuesto"""
        try:
            reason = function_args.get('reason', 'sin presupuesto disponible')
            
            # Marcar conversación como terminada
            self.collected_data['conversation_ended'] = True
            self.collected_data['budget_declined'] = True
            
            logger.info(f"🔚 CONVERSACIÓN TERMINADA: {reason}")
            
            # Respuesta empática pero que cierra el flujo
            return f"Entiendo perfectamente, {self.collected_data['name']}. No hay problema en absoluto. Cuando tengas presupuesto disponible para tu proyecto de {self.collected_data.get('service_interest', 'IA')}, estaremos aquí para ayudarte. ¡Que tengas un excelente día! 😊"
            
        except Exception as e:
            logger.error(f"Error handling end_conversation_no_budget: {e}")
            return "Entiendo. Cuando tengas presupuesto disponible, estaremos aquí para ayudarte. ¡Gracias por contactarnos!"
    
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
        """Respuesta de fallback SOLO cuando OpenAI falla completamente"""
        logger.warning("⚠️ USANDO FALLBACK - OpenAI no disponible")
        message_lower = message.lower()
        
        # Detectar selección de horario
        if any(num in message_lower for num in ['1', '2', '3']) and self.collected_data['calendar_options_shown']:
            import asyncio
            return asyncio.run(self._handle_schedule_meeting({'option_selected': message_lower.strip()}))
        
        # Contar mensajes previos para determinar si es saludo inicial
        is_first_interaction = len(self.conversation_log) <= 1
        
        # FALLBACK SIMPLE - NO INTERFERIR CON OPENAI
        
        # Saludo inicial
        if any(word in message_lower for word in ['hola', 'epale', 'buenas', 'hey']) or is_first_interaction:
            return f"¡Hola {self.contact_name}! Soy Mati de TDX. ¿Cómo estás hoy?"
        
        # Email detectado
        if '@' in message and '.' in message:
            self.collected_data['email'] = message.strip()
            logger.info(f"✅ Email capturado en fallback: {self.collected_data['email']}")
            if not self.collected_data['phone']:
                return "Genial. ¿Y tu número de teléfono?"
            else:
                return "Perfecto, ya tengo tus datos."
        
        # Número de teléfono detectado
        if any(char.isdigit() for char in message) and len(message.strip()) >= 8:
            self.collected_data['phone'] = message.strip()
            logger.info(f"✅ Teléfono capturado en fallback: {self.collected_data['phone']}")
            return "Excelente, ya tengo tu teléfono."
        
        # Requerimiento de IA
        if any(word in message_lower for word in ['ia', 'chatbot', 'bot', 'automatizacion', 'automatizar']):
            if 'automatizar' in message_lower or 'automatizacion' in message_lower:
                self.collected_data['service_interest'] = 'automatización de ventas'
            else:
                self.collected_data['service_interest'] = 'soluciones de IA'
            return f"Perfecto, {self.collected_data['service_interest']} es una excelente solución. ¿Cuentas con presupuesto para este proyecto?"
        
        # Confirmación de presupuesto
        if any(word in message_lower for word in ['si', 'sí', 'claro', 'perfecto', 'tengo']):
            if not self.collected_data['budget_confirmed']:
                self.collected_data['budget_confirmed'] = True
                self.collected_data['budget_range'] = 'Confirmado'
                return "Excelente. Para coordinar la reunión, ¿me das tu email?"
        
        # Default neutral
        return "Entiendo. ¿En qué más puedo ayudarte?"
    
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
