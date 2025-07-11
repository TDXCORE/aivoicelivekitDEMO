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
        """Procesar mensaje con manejo de estado y UX"""
        try:
            # Log mensaje del usuario
            self.conversation_log.append({
                'turn': len(self.conversation_log) + 1,
                'type': 'user_message',
                'content': message_content,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"Processing WhatsApp message from {self.contact_name}: {message_content[:50]}...")
            
            # Generar respuesta
            response = await self.generate_contextual_response(message_content)
            
            # Verificar longitud para WhatsApp
            if len(response) > 1000:
                response = response[:990] + "...\n\n¿Te ayudo con algo más específico? 😊"
            
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
    
    async def send_response_with_ux(self, response: str):
        """Enviar respuesta con UX mejorado"""
        # Añadir quick replies contextuales
        enhanced_response = response
        
        # Quick reply para fallback a voz si la conversación se complica
        if any(word in response.lower() for word in ['complejo', 'difícil', 'no entiendo', 'problema']):
            enhanced_response += "\n\n💬 ¿Prefieres hablar por teléfono?\n📞 Puedo conectarte con nuestro asistente de voz"
        
        # Quick reply para agendar si se menciona reunión
        elif 'reunión' in response.lower() or 'disponibilidad' in response.lower():
            enhanced_response += "\n\n📅 Opciones rápidas:\n• Esta semana\n• Próxima semana\n• Fecha específica"
        
        # Quick reply para más información
        elif 'ayud' in response.lower() and '?' in response:
            enhanced_response += "\n\n🤔 ¿Necesitas ayuda con algo específico?\n• Soluciones de IA\n• Agendar reunión\n• Hablar con ejecutivo"
        
        # Enviar con typing y rate limiting
        await self.chatwoot_client.send_message_with_typing(
            self.conversation_id, enhanced_response, self.user_id
        )
    
    async def generate_contextual_response(self, user_message: str) -> str:
        """Generar respuesta contextual con OpenAI"""
        try:
            messages = self.build_conversation_context(user_message)
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                max_tokens=400,
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
        
        system_prompt = f"""
        Eres Mati, asistente virtual de TDX especializado en soluciones de IA.
        
        📋 CONTEXTO DEL CLIENTE:
        • Nombre: {self.contact_name}
        • Empresa: {self.company_name}  
        • Email: {webhook_email if webhook_email else 'Pendiente de recolectar'}
        • Canal: WhatsApp
        • Conversación iniciada: {self.session_start_time.strftime('%H:%M')}
        
        🎯 OBJETIVO: Identificar necesidad de IA → agendar reunión estratégica o transferir a humano
        
        📱 ESTILO WHATSAPP:
        • Mensajes cortos (máx 3 líneas por punto)
        • Emojis moderados y apropiados
        • Tono amigable pero profesional
        • NO compartir datos sensibles en emojis (WhatsApp Policy)
        • Preguntas directas y específicas
        • Usa saltos de línea para legibilidad
        
        🔧 ESTADO ACTUAL: {self.awaiting_response_type or 'conversacion_general'}
        
        🚀 FLUJO DE CONVERSACIÓN:
        1. Saludo personalizado si es el primer mensaje
        2. Identificar necesidad específica de IA (soporte, ventas, automatización)
        3. Calificar urgencia y presupuesto
        4. Ofrecer reunión estratégica (preferido) o transferir a humano
        5. Si acepta reunión: usar herramientas de agendamiento
        6. Si rechaza o es muy complejo: transferir a humano
        
        HERRAMIENTAS DISPONIBLES:
        • check_availability_whatsapp: Consultar disponibilidad calendario
        • schedule_meeting_whatsapp: Agendar reunión confirmada
        • transfer_to_human_whatsapp: Escalamiento a humano
        • collect_email_whatsapp: Recolectar email si no está disponible
        
        EJEMPLOS DE RESPUESTAS EFECTIVAS:
        - "¡Hola {self.contact_name}! 👋 Soy Mati de TDX. Vi que te interesa la IA. ¿Qué desafío específico tiene {self.company_name}?"
        - "Entiendo que necesitas automatización. ¿Es para soporte al cliente, ventas, o algún proceso específico? 🤖"
        - "Perfecto. ¿Te conviene una reunión de 30 min esta semana para revisar soluciones específicas? 📅"
        
        Mantén la conversación enfocada y siempre busca agendar reunión o transferir si es necesario.
        Si el cliente menciona temas fuera de IA/tecnología, redirígelos amablemente.
        """
        
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
                    "description": "Solicitar email al cliente si no está disponible en el sistema",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "email": {
                                "type": "string",
                                "description": "Email proporcionado por el cliente"
                            }
                        },
                        "required": ["email"]
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