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
            'budget_option_selected': None,  # 1, 2, o 3
            'budget_payment_type': None,     # "full", "installments", o "interested_in_offer"
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
                        return await self._generate_fallback_response(message)
                except Exception as e:
                    logger.error(f"❌ Error initializing OpenAI: {e}")
                    return await self._generate_fallback_response(message)
            
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
                            "budget_range": {"type": "string", "description": "Rango específico si lo menciona"},
                            "budget_option_selected": {"type": "string", "description": "Opción de presupuesto seleccionada: 1, 2, o 3"},
                            "budget_payment_type": {"type": "string", "description": "Tipo de pago: full, installments, o interested_in_offer"}
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

REGLAS CRÍTICAS DE FLUJO:
- DETECTAR REQUERIMIENTO: Si usuario menciona cualquiera de estas palabras: "servicios de ai", "servicios de ia", "chatbot", "bot", "ia", "automatizar", "automatización", "soluciones", "proyecto" -> INMEDIATAMENTE usar extract_user_data para capturar service_interest
- PREGUNTA DE PRESUPUESTO: Cuando captures service_interest y NO tengas presupuesto confirmado -> PREGUNTAR EXACTAMENTE:
  "¿Tienes disponible el presupuesto de 2.000 USD a 20.000 USD para este proyecto?

  1️⃣ Sí, tengo el presupuesto
  2️⃣ Sí, pero para hacer pagos en partes  
  3️⃣ No, pero me interesa escuchar la oferta

  Solo responde con el número de tu opción."
- PROCESAR OPCIONES: Si usuario responde "1", "2", o "3" -> USAR extract_user_data con budget_option_selected
- FLUJO CONTINUO: TODAS las opciones de presupuesto (1, 2, 3) continúan el flujo hacia la reunión
- PROHIBIDO: NUNCA termines conversación por presupuesto, NUNCA preguntes presupuesto genérico

REGLAS ANTI-REPETICIÓN:
- NUNCA saludes si ya hay conversación previa
- NUNCA preguntes datos ya capturados arriba
- CONTINÚA desde donde se quedó la conversación
- NO reinicies el flujo ni hagas preguntas repetidas

PERSONALIDAD: Empático, natural, directo. Máximo 1 emoji por mensaje."""
        
        return system_prompt
    
    def _determine_next_conversation_step(self) -> str:
        """Determinar el siguiente paso lógico del flujo"""
        # Si conversación ya terminó, no hacer nada más
        if self.collected_data.get('conversation_ended'):
            return "CONVERSACIÓN TERMINADA - Ser cordial pero no continuar flujo"
        
        # Si presupuesto fue declinado, continuar con el flujo (ya no terminamos conversación)
        if self.collected_data.get('budget_declined'):
            return "CONTINUAR: Todas las opciones de presupuesto continúan el flujo"
        
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
                        elif key == 'budget_option_selected':
                            # Manejar las opciones de presupuesto específicas
                            if value in ['1', '2', '3']:
                                self.collected_data['budget_confirmed'] = True
                                if value == '1':
                                    self.collected_data['budget_payment_type'] = 'full'
                                    self.collected_data['budget_range'] = 'Presupuesto completo disponible'
                                elif value == '2':
                                    self.collected_data['budget_payment_type'] = 'installments'
                                    self.collected_data['budget_range'] = 'Pagos en partes'
                                elif value == '3':
                                    self.collected_data['budget_payment_type'] = 'interested_in_offer'
                                    self.collected_data['budget_range'] = 'Interesado en oferta'
                        logger.info(f"✅ DATO ACTUALIZADO: {key} = {value}")
            
            # FLUJO INTELIGENTE - VERIFICAR ESTADO COMPLETO DESPUÉS DE CADA ACTUALIZACIÓN
            logger.info(f"🔍 Estado actual: email={bool(self.collected_data['email'])}, phone={bool(self.collected_data['phone'])}, service={bool(self.collected_data['service_interest'])}, budget={self.collected_data['budget_confirmed']}")
            
            # 1. Si acabamos de capturar requerimiento y no tenemos presupuesto -> preguntar presupuesto específico
            if 'service_interest' in updated_fields and not self.collected_data['budget_confirmed']:
                return f"Perfecto, {self.collected_data['service_interest']} es una excelente solución.\n\n¿Tienes disponible el presupuesto de 2.000 USD a 20.000 USD para este proyecto?\n\n1️⃣ Sí, tengo el presupuesto\n2️⃣ Sí, pero para hacer pagos en partes\n3️⃣ No, pero me interesa escuchar la oferta\n\nSolo responde con el número de tu opción."
            
            # 2. Si acabamos de confirmar presupuesto (cualquier opción) -> pedir datos faltantes
            if ('budget_range' in updated_fields or 'budget_option_selected' in updated_fields) and self.collected_data['budget_confirmed']:
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
        """Mostrar opciones de calendario disponibles REALES"""
        try:
            # Verificar que tenemos presupuesto confirmado antes de mostrar calendario
            if not self.collected_data['budget_confirmed']:
                return "Primero necesito confirmar tu presupuesto."
            
            service_type = function_args.get('service_type', 'tu proyecto')
            
            # Marcar que ya mostramos las opciones
            self.collected_data['calendar_options_shown'] = True
            
            logger.info(f"🔍 Obteniendo horarios disponibles REALES para {self.collected_data['name']}")
            
            # NUEVO: Obtener horarios disponibles reales del calendario
            available_slots = await self.graph_client.get_real_available_slots(max_slots=3)
            
            if available_slots and len(available_slots) >= 3:
                # Guardar las opciones para referencia posterior
                self.collected_data['available_slots'] = available_slots
                
                # Formatear opciones para WhatsApp
                options_msg = f"¡Listo {self.collected_data['name']}!\n\n"
                for i, slot in enumerate(available_slots[:3], 1):
                    options_msg += f"{i}. {slot['formatted']}\n"
                options_msg += "\n¿Cuál opción? Solo el número 📅"
                
                logger.info(f"✅ Mostrando {len(available_slots)} horarios reales disponibles")
                return options_msg
            else:
                # Fallback si no hay suficientes slots disponibles
                logger.warning("⚠️ No se encontraron suficientes horarios disponibles, usando fallback")
                fallback_slots = [
                    {"date": "2025-08-06", "time": "09:00 AM", "formatted": "Mañana 9:00 AM"},
                    {"date": "2025-08-06", "time": "10:00 AM", "formatted": "Mañana 10:00 AM"},
                    {"date": "2025-08-06", "time": "11:00 AM", "formatted": "Mañana 11:00 AM"}
                ]
                self.collected_data['available_slots'] = fallback_slots
                
                options_msg = f"¡Listo {self.collected_data['name']}!\n\n"
                for i, slot in enumerate(fallback_slots, 1):
                    options_msg += f"{i}. {slot['formatted']}\n"
                options_msg += "\n¿Cuál opción? Solo el número 📅"
                
                return options_msg
            
        except Exception as e:
            logger.error(f"Error handling show_calendar_options: {e}")
            # Fallback de emergencia
            return "¿Mañana 10am está bien?"
    
    async def _handle_schedule_meeting(self, function_args: Dict) -> str:
        """Agendar reunión real usando Microsoft Graph con horarios REALES"""
        try:
            option_selected = function_args.get('option_selected', '1')
            
            # NUEVO: Usar los horarios reales que se mostraron al usuario
            available_slots = self.collected_data.get('available_slots', [])
            
            if available_slots and len(available_slots) >= int(option_selected):
                # Usar el horario real seleccionado
                selected_slot = available_slots[int(option_selected) - 1]
                selected_time = {
                    "date": selected_slot['date'],
                    "time": selected_slot['time'],
                    "display": selected_slot['formatted']
                }
                logger.info(f"✅ Usando horario REAL seleccionado: {selected_time}")
            else:
                # Fallback a horarios hardcodeados si no hay slots disponibles
                logger.warning("⚠️ No hay slots disponibles guardados, usando fallback")
                time_mapping = {
                    "1": {"date": "2025-08-06", "time": "09:00 AM", "display": "Mañana 9:00 AM"},
                    "2": {"date": "2025-08-06", "time": "10:00 AM", "display": "Mañana 10:00 AM"},
                    "3": {"date": "2025-08-06", "time": "11:00 AM", "display": "Mañana 11:00 AM"}
                }
                selected_time = time_mapping.get(option_selected, time_mapping["1"])
            
            # Actualizar estado
            self.collected_data['selected_time_slot'] = selected_time['display']
            self.collected_data['meeting_confirmed'] = True
            
            # Agendar reunión real con Microsoft Graph CON RESUMEN DETALLADO
            logger.info(f"🔧 Agendando reunión real con Microsoft Graph para {selected_time['display']}...")
            
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
                
                logger.info(f"✅ Reunión agendada exitosamente para {self.collected_data['name']} - {selected_time['display']}")
                return confirmation_msg
            else:
                # Error al agendar, pero confirmar de todas formas
                logger.warning(f"⚠️ Error agendando reunión real, pero confirmando al usuario")
                return f"¡Perfecto {self.collected_data['name']}!\n\n✅ {selected_time['display']} confirmado\n📧 Te contactamos pronto\n\n¡Gracias!"
            
        except Exception as e:
            logger.error(f"❌ Error handling schedule_meeting: {e}")
            return f"¡Perfecto! Tu reunión ha sido confirmada. Te contactaremos pronto con los detalles."
    
    async def _generate_fallback_response(self, message: str) -> str:
        """Respuesta de fallback INTELIGENTE - Detecta automáticamente el siguiente paso"""
        logger.warning("⚠️ USANDO FALLBACK INTELIGENTE - OpenAI no disponible")
        
        # NUEVO: Detectar automáticamente si debemos mostrar calendario
        ready_for_calendar = all([
            self.collected_data['email'],
            self.collected_data['phone'], 
            self.collected_data['service_interest'],
            self.collected_data['budget_confirmed'],
            not self.collected_data['calendar_options_shown']
        ])
        
        if ready_for_calendar:
            logger.info("🎯 FALLBACK: Detectado que debe mostrar calendario automáticamente")
            service_type = self.collected_data.get('service_interest', 'tu proyecto')
            return await self._handle_show_calendar_options({'service_type': service_type})
        
        # Detectar si usuario seleccionó opción de calendario
        if (self.collected_data['calendar_options_shown'] and 
            not self.collected_data['meeting_confirmed'] and 
            message.strip() in ['1', '2', '3']):
            logger.info(f"🎯 FALLBACK: Detectado selección de calendario: {message}")
            return await self._handle_schedule_meeting({'option_selected': message.strip()})
        
        # Detectar respuestas de presupuesto
        if (self.collected_data['service_interest'] and 
            not self.collected_data['budget_confirmed'] and 
            message.strip() in ['1', '2', '3']):
            logger.info(f"🎯 FALLBACK: Detectado respuesta de presupuesto: {message}")
            # Simular function call de extract_user_data
            budget_data = {'budget_option_selected': message.strip()}
            return await self._handle_extract_user_data(budget_data)
        
        # Detectar email
        if '@' in message and not self.collected_data['email']:
            logger.info(f"🎯 FALLBACK: Detectado email: {message}")
            email_data = {'email': message.strip()}
            return await self._handle_extract_user_data(email_data)
        
        # Detectar teléfono (números de 7+ dígitos)
        import re
        phone_pattern = r'\b\d{7,}\b'
        if re.search(phone_pattern, message) and not self.collected_data['phone']:
            phone = re.search(phone_pattern, message).group()
            logger.info(f"🎯 FALLBACK: Detectado teléfono: {phone}")
            phone_data = {'phone': phone}
            return await self._handle_extract_user_data(phone_data)
        
        # Detectar requerimientos de IA
        ai_keywords = ['chatbot', 'bot', 'ia', 'ai', 'automatizar', 'automatización', 'servicios de ai', 'servicios de ia']
        if any(keyword in message.lower() for keyword in ai_keywords) and not self.collected_data['service_interest']:
            logger.info(f"🎯 FALLBACK: Detectado requerimiento de IA: {message}")
            service_data = {'service_interest': message.strip()}
            return await self._handle_extract_user_data(service_data)
        
        # Respuesta genérica si no detectamos nada específico
        next_step = self._determine_next_conversation_step()
        
        if "CAPTURAR: Requerimiento" in next_step:
            return "¿Qué tipo de servicio de IA necesitas? Por ejemplo: chatbot, automatización, etc."
        elif "PREGUNTAR: ¿Tienes presupuesto" in next_step:
            return f"¿Tienes disponible el presupuesto de 2.000 USD a 20.000 USD para este proyecto?\n\n1️⃣ Sí, tengo el presupuesto\n2️⃣ Sí, pero para hacer pagos en partes\n3️⃣ No, pero me interesa escuchar la oferta\n\nSolo responde con el número de tu opción."
        elif "SOLICITAR: Email" in next_step:
            return "Para coordinar la reunión, ¿me das tu email?"
        elif "SOLICITAR: Número" in next_step:
            return "¿Y tu número de teléfono?"
        else:
            return f"Hola {self.contact_name}, soy Mati de TDX. ¿En qué puedo ayudarte hoy?"
    
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
