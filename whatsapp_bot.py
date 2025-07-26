import openai
import asyncio
from datetime import datetime
import logging
from typing import Dict, Any, Optional, List
import json
import os

# IMPORTAR recursos existentes (NO MODIFICAR)
from microsoft_graph_client import graph_client
from chatwoot_summary_integration import send_bot_summary_to_chatwoot
from whatsapp_client import ChatwootWhatsAppClient

logger = logging.getLogger("whatsapp-bot")

class TDXWhatsAppBot:
    def __init__(self, contact_name: str, company_name: str, prospect_info: Dict[str, Any], conversation_id: int):
        self.contact_name = contact_name
        self.company_name = company_name
        self.prospect_info = prospect_info
        self.conversation_id = conversation_id
        self.conversation_log = []
        self.user_id = str(prospect_info.get('chatwoot_id', conversation_id))
        
        # Cliente Chatwoot
        self.chatwoot_client = ChatwootWhatsAppClient()
        
        # Estado de conversación
        self.awaiting_response_type = None  # 'availability', 'confirmation', etc.
        self.last_offered_slots = []
        self.session_start_time = datetime.now()
        
        # Configurar OpenAI client
        self.openai_client = None
        try:
            import __main__
            if hasattr(__main__, 'openai_client') and __main__.openai_client:
                self.openai_client = __main__.openai_client
            else:
                self.openai_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        except:
            self.openai_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    async def process_message(self, message_content: str) -> Optional[str]:
        """Procesar mensaje con manejo de estado y UX + detección automática de transferencia"""
        try:
            # Log mensaje del usuario
            self.conversation_log.append({
                'turn': len(self.conversation_log) + 1,
                'type': 'user_message',
                'content': message_content,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"Processing WhatsApp message from {self.contact_name}: {message_content[:50]}...")
            
            # DETECCIÓN AUTOMÁTICA DE KEYWORDS DE TRANSFERENCIA - CRÍTICO
            transfer_triggered = await self.check_automatic_transfer_keywords(message_content)
            if transfer_triggered:
                return transfer_triggered
            
            # DETECCIÓN AUTOMÁTICA DE KEYWORDS DE AGENDAMIENTO - CRÍTICO
            schedule_triggered = await self.check_automatic_schedule_keywords(message_content)
            if schedule_triggered:
                return schedule_triggered
            
            # Generar respuesta
            response = await self.generate_contextual_response(message_content)
            
            # Verificar longitud para WhatsApp (reducido de 1000 a 500)
            if len(response) > 500:
                response = response[:485] + "...\n\n¿Te ayudo con algo específico? 😊"
            
            # Enviar respuesta con UX mejorado
            await self.send_response_with_ux(response)
            
            # Log respuesta del bot
            self.conversation_log.append({
                'turn': len(self.conversation_log) + 1,
                'type': 'assistant_message',
                'content': response,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"WhatsApp response sent successfully to {self.contact_name}")
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            error_response = "Disculpa, tuve un problema técnico 🔧\n\nUn ejecutivo te contactará pronto."
            await self.chatwoot_client.send_message_with_typing(
                self.conversation_id, error_response, self.user_id
            )
            return error_response
    
    async def check_automatic_transfer_keywords(self, message_content: str) -> Optional[str]:
        """Detectar keywords de transferencia automática - IDÉNTICO AL BOT DE VOZ"""
        try:
            # Keywords exactos del bot de voz
            TRANSFER_KEYWORDS = [
                "ejecutivo", "vendedor", "asesor", "consultor", "especialista",
                "hablar con alguien", "persona real", "humano", "representante", "agente",
                "gerente", "director", "supervisor", "jefe",
                "experto", "técnico", "ingeniero",
                "quiero hablar con", "me conecta con", "transfiere", "transferir",
                "no quiero bot", "quiero persona", "alguien más",
                "comunicar con", "conectar con", "pasar con"
            ]
            
            message_lower = message_content.lower()
            
            # Verificar si alguna keyword está presente
            for keyword in TRANSFER_KEYWORDS:
                if keyword in message_lower:
                    logger.info(f"🚨 AUTOMATIC TRANSFER triggered by keyword: '{keyword}' in message: {message_content[:50]}")
                    
                    # Transferir INMEDIATAMENTE sin preguntar
                    transfer_response = await self.transfer_to_human_whatsapp(
                        f"Transferencia automática activada por keyword: '{keyword}'"
                    )
                    
                    # Enviar respuesta inmediata
                    await self.chatwoot_client.send_message_with_typing(
                        self.conversation_id, transfer_response, self.user_id
                    )
                    
                    # Log de transferencia automática
                    self.conversation_log.append({
                        'turn': len(self.conversation_log) + 1,
                        'type': 'automatic_transfer',
                        'content': f"Auto-transfer triggered by: {keyword}",
                        'response': transfer_response,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    logger.info(f"✅ Automatic transfer completed for {self.contact_name}")
                    return transfer_response
            
            # No keywords detectadas, continuar flujo normal
            return None
            
        except Exception as e:
            logger.error(f"Error in automatic transfer detection: {e}")
            return None
    
    async def check_automatic_schedule_keywords(self, message_content: str) -> Optional[str]:
        """Detectar keywords de agendamiento - pero solo para casos SIMPLES sin fechas/horas específicas"""
        try:
            # Keywords para agendamiento simple (solo "agendar" sin detalles)
            SIMPLE_SCHEDULE_KEYWORDS = ["agendar", "programar", "disponibilidad", "horario"]
            
            message_lower = message_content.lower()
            
            # Detectar si el mensaje tiene fechas/horas específicas
            time_indicators = ["mañana", "lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo", 
                             "am", "pm", ":", "hora", "hoy", "tarde", "mañana", "noche",
                             "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]
            
            has_specific_time = any(indicator in message_lower for indicator in time_indicators)
            
            # Si tiene tiempo específico, NO usar detección automática - dejar que OpenAI lo procese
            if has_specific_time:
                logger.info(f"⏰ Scheduling message with specific time detected: {message_content[:50]} - passing to OpenAI")
                return None  # Dejar que OpenAI use schedule_meeting_whatsapp
            
            # Solo para mensajes simples como "quiero agendar" sin detalles
            for keyword in SIMPLE_SCHEDULE_KEYWORDS:
                if keyword in message_lower and not has_specific_time:
                    logger.info(f"📅 Simple schedule request triggered by: '{keyword}' - showing availability")
                    
                    # Solo mostrar disponibilidad para agendamiento simple
                    availability_response = await self.check_availability_whatsapp()
                    
                    # Enviar respuesta inmediata
                    await self.chatwoot_client.send_message_with_typing(
                        self.conversation_id, availability_response, self.user_id
                    )
                    
                    logger.info(f"✅ Simple availability check completed for {self.contact_name}")
                    return availability_response
            
            # No keywords simples detectadas, continuar flujo normal
            return None
            
        except Exception as e:
            logger.error(f"Error in automatic schedule detection: {e}")
            return None
    
    async def send_response_with_ux(self, response: str):
        """Enviar respuesta natural sin opciones predefinidas"""
        # Enviar respuesta directa sin quick replies
        await self.chatwoot_client.send_message_with_typing(
            self.conversation_id, response, self.user_id
        )
    
    async def generate_contextual_response(self, user_message: str) -> str:
        """Generar respuesta contextual con OpenAI"""
        try:
            messages = self.build_conversation_context(user_message)
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.3,
                max_tokens=200,
                tools=self.get_whatsapp_tools(),
                tool_choice="auto"
            )
            
            # Manejar function calls
            if response.choices[0].message.tool_calls:
                return await self.handle_function_call(response.choices[0].message.tool_calls[0])
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "Perdón, puedes repetir tu pregunta? 🤔"
    
    def build_conversation_context(self, user_message: str) -> List[Dict[str, str]]:
        """Construir contexto de conversación optimizado"""
        webhook_email = self.prospect_info.get('email')
        
        system_prompt = f"""Eres Mati, ejecutivo comercial de TDX. Conversación natural y fluida.

CLIENTE: {self.contact_name} de {self.company_name}
EMAIL: {webhook_email if webhook_email else 'Pendiente'}

PERSONALIDAD: Profesional, directo pero amigable. Conversación natural como humano real.

OBJETIVO: Agendar reunión de forma conversacional y eficiente.

HERRAMIENTAS DISPONIBLES:
- schedule_meeting_whatsapp: Agendar reunión con fecha/hora específica
- check_availability_whatsapp: Consultar disponibilidad (solo si necesario)
- collect_email_whatsapp: Guardar email del cliente
- transfer_to_human_whatsapp: Transferir a humano si es necesario

REGLAS DE CONVERSACIÓN:
1. NUNCA uses listas con viñetas o opciones múltiple
2. NUNCA agregues "OPCIONES:" o menús
3. Habla naturalmente como persona real
4. Máximo 2-3 oraciones por respuesta

USO OBLIGATORIO DE HERRAMIENTAS:
- Email detectado (ej: "freddyrincones@gmail.com") → USAR collect_email_whatsapp INMEDIATAMENTE
- Fecha/hora específica (ej: "lunes 3pm") → USAR schedule_meeting_whatsapp INMEDIATAMENTE  
- Solicitud de agendamiento sin detalles → USAR check_availability_whatsapp
- Solicitud de humano → USAR transfer_to_human_whatsapp

CONVERSIÓN DE FECHAS (hoy es 2025-07-26):
- "lunes" = 2025-07-28 (próximo lunes)
- "mañana" = 2025-07-27  
- "3pm" = "15:00"
- "10am" = "10:00"

DETECCIÓN DE EMAILS:
- Cualquier texto con @ y dominio = EMAIL → usar collect_email_whatsapp
- Ejemplo: "freddyrincones@gmail.com" = EMAIL válido

Responde como ejecutivo comercial real, no como bot."""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Contexto de conversación (últimos 8 intercambios)
        recent_log = self.conversation_log[-8:] if len(self.conversation_log) > 8 else self.conversation_log
        
        for entry in recent_log:
            role = "user" if entry['type'] == 'user_message' else "assistant"
            messages.append({"role": role, "content": entry['content']})
        
        messages.append({"role": "user", "content": user_message})
        return messages
    
    def get_whatsapp_tools(self) -> List[Dict[str, Any]]:
        """Definir herramientas disponibles para el bot"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "schedule_meeting_whatsapp",
                    "description": "Agendar reunión estratégica cuando el cliente acepta",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "description": "Fecha de la reunión en formato YYYY-MM-DD"
                            },
                            "time": {
                                "type": "string", 
                                "description": "Hora de la reunión en formato HH:MM"
                            }
                        },
                        "required": ["date", "time"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_availability_whatsapp",
                    "description": "Consultar disponibilidad de calendario para ofrecer opciones",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "transfer_to_human_whatsapp",
                    "description": "Transferir a agente humano cuando el cliente lo solicite o la consulta sea muy compleja",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "reason": {
                                "type": "string",
                                "description": "Razón de la transferencia"
                            }
                        },
                        "required": ["reason"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "collect_email_whatsapp",
                    "description": "SIEMPRE usar cuando el cliente proporciona un email address (ej: nombre@empresa.com). Guardar el email en el sistema.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "email": {
                                "type": "string",
                                "description": "Email address que proporciona el cliente (ej: freddyrincones@gmail.com)"
                            }
                        },
                        "required": ["email"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "qualify_prospect_whatsapp",
                    "description": "Calificar prospect usando metodología BANT (Budget, Authority, Need, Timeline)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "budget_range": {
                                "type": "string",
                                "enum": ["10k-50k", "50k-100k", "100k+", "sin_presupuesto"],
                                "description": "Rango de presupuesto del cliente"
                            },
                            "authority_level": {
                                "type": "string",
                                "enum": ["decision_maker", "influencer", "user"],
                                "description": "Nivel de autoridad del contacto"
                            },
                            "need_urgency": {
                                "type": "string",
                                "enum": ["high", "medium", "low"],
                                "description": "Urgencia de la necesidad"
                            },
                            "timeline": {
                                "type": "string",
                                "enum": ["immediate", "3_months", "6_months", "12_months+"],
                                "description": "Timeline de implementación"
                            }
                        },
                        "required": ["budget_range", "authority_level", "need_urgency", "timeline"]
                    }
                }
            }
        ]
    
    async def handle_function_call(self, tool_call) -> str:
        """Manejar llamadas a herramientas"""
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)
        
        logger.info(f"WhatsApp bot calling function: {function_name} with args: {function_args}")
        
        try:
            if function_name == "schedule_meeting_whatsapp":
                return await self.schedule_meeting_whatsapp(
                    function_args.get("date"),
                    function_args.get("time")
                )
            elif function_name == "check_availability_whatsapp":
                return await self.check_availability_whatsapp()
            elif function_name == "transfer_to_human_whatsapp":
                return await self.transfer_to_human_whatsapp(
                    function_args.get("reason", "Cliente solicita hablar con humano")
                )
            elif function_name == "collect_email_whatsapp":
                return await self.collect_email_whatsapp(
                    function_args.get("email")
                )
            elif function_name == "qualify_prospect_whatsapp":
                return await self.qualify_prospect_whatsapp(
                    function_args.get("budget_range"),
                    function_args.get("authority_level"),
                    function_args.get("need_urgency"),
                    function_args.get("timeline")
                )
            else:
                return "Disculpa, no pude procesar esa solicitud. ¿Puedes intentar de nuevo? 🤔"
                
        except Exception as e:
            logger.error(f"Error in function call {function_name}: {e}")
            return "Hubo un error procesando tu solicitud. Un momento por favor... 🔄"
    
    async def schedule_meeting_whatsapp(self, date: str, time: str) -> str:
        """Tool: Agendar reunión reutilizando graph_client"""
        try:
            final_email = self.prospect_info.get('email')
            
            if not final_email:
                return "📧 Necesito tu email para enviar la invitación de la reunión.\n\n¿Podrías compartirlo conmigo?"
            
            # Marcar estado
            self.awaiting_response_type = 'meeting_confirmation'
            
            # REUTILIZAR microsoft_graph_client (SIN MODIFICAR)
            result = await graph_client.create_meeting(
                attendee_email=final_email,
                meeting_date=date,
                meeting_time=time,
                contact_name=self.contact_name,
                company_name=self.company_name,
                meeting_type="discovery_call"
            )
            
            success_msg = f"""✅ ¡Reunión agendada exitosamente!

📅 **Fecha:** {date}
🕐 **Hora:** {time}
📧 **Invitación enviada a:** {final_email}
🎯 **Duración:** 30 minutos

Te llegará la invitación con el enlace de Teams.

¿Hay algo más en lo que pueda ayudarte? 😊"""

            logger.info(f"Meeting scheduled via WhatsApp: {self.conversation_id} -> {date} {time}")
            return success_msg
            
        except Exception as e:
            logger.error(f"Error scheduling meeting: {e}")
            return "⚠️ Hubo un problema agendando la reunión.\n\nUn ejecutivo te contactará pronto para coordinar."
    
    async def check_availability_whatsapp(self) -> str:
        """Tool: Verificar disponibilidad reutilizando graph_client"""
        try:
            from datetime import datetime, timedelta
            
            start_date = datetime.now() + timedelta(days=1)
            end_date = start_date + timedelta(days=7)
            
            # REUTILIZAR microsoft_graph_client (SIN MODIFICAR)
            slots = await graph_client.check_availability(start_date, end_date)
            
            # Guardar slots para siguiente interacción
            self.last_offered_slots = slots[:3]
            self.awaiting_response_type = 'slot_selection'
            
            availability_msg = f"""📅 **Disponibilidad para reunión estratégica:**

🟢 **Opción 1:** {slots[0]}
🟢 **Opción 2:** {slots[1]}  
🟢 **Opción 3:** {slots[2]}

¿Cuál de estas opciones te conviene mejor?

También puedes sugerir otra fecha si ninguna te funciona 😊"""

            return availability_msg
            
        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            return "📅 Tengo disponibilidad esta semana y la próxima.\n\n¿Qué día y hora prefieres para la reunión?"
    
    async def transfer_to_human_whatsapp(self, reason: str = "Cliente solicita hablar con humano") -> str:
        """Tool: Transferir a agente humano"""
        try:
            # Cambiar estado de conversación
            success = await self.chatwoot_client.handoff_to_human(self.conversation_id)
            
            if success:
                # Crear resumen para el agente humano
                await self.create_handoff_summary(reason)
                
                return f"""🤝 **Transferencia a ejecutivo humano**

Te estoy conectando con un especialista de nuestro equipo que podrá ayudarte mejor.

**Motivo:** {reason}

En un momento se unirá a la conversación.

¡Gracias por tu paciencia! 😊"""
            else:
                return "⚠️ No pude transferirte en este momento.\n\nUn ejecutivo te contactará pronto por este mismo canal."
                
        except Exception as e:
            logger.error(f"Error transferring to human: {e}")
            return "⚠️ Error en la transferencia.\n\nUn ejecutivo te contactará pronto."
    
    async def collect_email_whatsapp(self, email: str) -> str:
        """Tool: Recolectar email del cliente"""
        try:
            # Validación básica de email
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            
            if not re.match(email_pattern, email.lower()):
                return "📧 El email no parece válido.\n\n¿Podrías verificar y escribirlo de nuevo? Ejemplo: nombre@empresa.com"
            
            # Actualizar prospect_info
            self.prospect_info['email'] = email.lower()
            
            return f"""✅ Email guardado: {email.lower()}

Perfecto, ahora puedo enviarte la invitación de la reunión.

¿Te parece bien que revisemos tu disponibilidad? 📅"""
            
        except Exception as e:
            logger.error(f"Error collecting email: {e}")
            return "Hubo un problema guardando el email. ¿Puedes intentar de nuevo?"
    
    async def qualify_prospect_whatsapp(self, budget_range: str, authority_level: str, need_urgency: str, timeline: str) -> str:
        """Tool: Calificar prospect usando metodología BANT - IDÉNTICA AL BOT DE VOZ"""
        try:
            logger.info(
                f"qualifying WhatsApp prospect {self.contact_name}: Budget={budget_range}, Authority={authority_level}, Need={need_urgency}, Timeline={timeline}"
            )
            
            # Marcar estado de conversación
            self.awaiting_response_type = 'qualification_complete'
            
            # Score qualification - LÓGICA EXACTA DEL BOT DE VOZ
            score = 0
            if budget_range in ['50k-100k', '100k+']:
                score += 25
            elif budget_range == '10k-50k':
                score += 15
                
            if authority_level == 'decision_maker':
                score += 30
            elif authority_level == 'influencer':
                score += 20
                
            if need_urgency == 'high':
                score += 25
            elif need_urgency == 'medium':
                score += 15
                
            if timeline in ['immediate', '3_months']:
                score += 20
            elif timeline == '6_months':
                score += 10
            
            qualified = score >= 60
            recommendation = "schedule_meeting" if qualified else "nurture_lead"
            
            # Guardar resultado en prospect_info para seguimiento
            self.prospect_info.update({
                'qualification_score': score,
                'qualified': qualified,
                'budget_range': budget_range,
                'authority_level': authority_level,
                'need_urgency': need_urgency,
                'timeline': timeline,
                'qualification_date': datetime.now().isoformat()
            })
            
            # Generar respuesta basada en calificación
            if qualified:
                response = f"""✅ **Perfil calificado exitosamente** (Score: {score}/100)

🎯 **Análisis de tu perfil:**
• Presupuesto: {budget_range}
• Autoridad: {authority_level}
• Urgencia: {need_urgency}
• Timeline: {timeline}

**Recomendación:** Reunión estratégica inmediata 🚀

¿Te parece bien que agendemos una reunión de 30 minutos esta semana para revisar soluciones específicas para {self.company_name}?"""

            else:
                response = f"""📊 **Análisis de perfil completado** (Score: {score}/100)

🔍 **Tu perfil actual:**
• Presupuesto: {budget_range}
• Autoridad: {authority_level}
• Urgencia: {need_urgency}
• Timeline: {timeline}

**Recomendación:** Te mantendré informado de nuevas soluciones que se ajusten mejor a tu perfil actual.

¿Te gustaría que un especialista te contacte cuando tengamos opciones más adecuadas? 📞"""

            logger.info(f"WhatsApp prospect qualification completed: {self.contact_name} - Score: {score} - Qualified: {qualified}")
            return response
            
        except Exception as e:
            logger.error(f"Error qualifying WhatsApp prospect: {e}")
            return "⚠️ Hubo un problema evaluando tu perfil.\n\nUn especialista revisará tu caso personalmente. ¿Te parece bien?"
    
    async def create_handoff_summary(self, handoff_reason: str):
        """Crear resumen para el agente humano"""
        try:
            # Crear resumen estructurado
            summary_data = {
                'call_direction': 'whatsapp_chat',
                'contact_name': self.contact_name,
                'company_name': self.company_name,
                'prospect_info': self.prospect_info,
                'conversation_log': self.conversation_log,
                'total_turns': len(self.conversation_log),
                'session_start_time': self.session_start_time.isoformat(),
                'session_end_time': datetime.now().isoformat(),
                'handoff_reason': handoff_reason,
                'channel': 'whatsapp',
                'awaiting_response_type': self.awaiting_response_type,
                'last_offered_slots': self.last_offered_slots
            }
            
            # REUTILIZAR chatwoot_summary_integration (SIN MODIFICAR)
            phone = self.prospect_info.get('phone', 'N/A')
            if phone and phone != 'N/A':
                await send_bot_summary_to_chatwoot(
                    phone_number=phone,
                    conversation_summary=json.dumps(summary_data),
                    call_duration=None,
                    call_outcome="Transferido a humano via WhatsApp"
                )
                
                logger.info(f"Handoff summary created for WhatsApp conversation {self.conversation_id}")
                
        except Exception as e:
            logger.error(f"Error creating handoff summary: {e}")