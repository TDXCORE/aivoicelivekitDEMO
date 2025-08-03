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

# Import business hours validator
try:
    from business_hours_validator import business_hours
    BUSINESS_HOURS_AVAILABLE = True
    logger.info("✅ Business Hours Validator imported successfully")
except ImportError as e:
    BUSINESS_HOURS_AVAILABLE = False
    logger.error(f"❌ Business Hours Validator import failed: {e}")

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
        """Procesar mensaje enfocado en calificar y agendar clientes"""
        try:
            # Log mensaje del usuario
            self.conversation_log.append({
                'turn': len(self.conversation_log) + 1,
                'type': 'user_message',
                'content': message_content,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"Processing WhatsApp message from {self.contact_name}: {message_content[:50]}...")
            
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
    
    async def fast_exit(self, category: str) -> str:
        """Fast exit para conversaciones Off-Topic"""
        try:
            msg = self.off_topic_templates.get(category, "Solo servicios IA empresariales.")
            await self.chatwoot_client.send_message_with_typing(self.conversation_id, msg, self.user_id)
            
            # Log y cerrar conversación
            await send_bot_summary_to_chatwoot(
                phone=self.prospect_info.get('phone', 'N/A'),
                conversation_summary=f"Closed: Off-Topic ({category})",
                call_outcome=f"Off-Topic: {category}"
            )
            
            # Log del cierre
            self.conversation_log.append({
                'turn': len(self.conversation_log) + 1,
                'type': 'assistant_message',
                'content': msg,
                'timestamp': datetime.now().isoformat(),
                'action': 'fast_exit',
                'reason': category
            })
            
            logger.info(f"Fast exit applied for {self.conversation_id}: {category}")
            return "conversation_closed"
            
        except Exception as e:
            logger.error(f"Error in fast_exit: {e}")
            return "Servicio no disponible actualmente."
    
    # ELIMINADA: Función de transferencia automática
    # El bot debe enfocarse 100% en calificar y agendar clientes
    
    async def check_automatic_schedule_keywords(self, message_content: str) -> Optional[str]:
        """Detectar keywords de agendamiento - OPTIMIZADO para leads fríos"""
        try:
            message_lower = message_content.lower()
            
            # Keywords para agendamiento directo con fecha/hora
            time_indicators = ["mañana", "lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo", 
                             "am", "pm", ":", "hora", "hoy", "tarde", "noche",
                             "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]
            
            has_specific_time = any(indicator in message_lower for indicator in time_indicators)
            
            # Si tiene tiempo específico, dejar que OpenAI lo procese con schedule_consultation
            if has_specific_time:
                logger.info(f"⏰ Scheduling with specific time detected: {message_content[:50]} - passing to OpenAI")
                return None  # OpenAI usará schedule_consultation
            
            # Para leads fríos: solo agendar si ya tienen datos completos
            SIMPLE_SCHEDULE_KEYWORDS = ["agendar", "programar", "reunion", "cita", "disponibilidad", "horario"]
            
            for keyword in SIMPLE_SCHEDULE_KEYWORDS:
                if keyword in message_lower:
                    # Verificar si ya tenemos datos completos del contacto
                    has_complete_data = (
                        self.prospect_info.get('full_name') and 
                        self.prospect_info.get('email') and 
                        self.prospect_info.get('company_name')
                    )
                    
                    if has_complete_data:
                        logger.info(f"📅 Schedule request with complete data: '{keyword}' - showing availability")
                        # Si ya tenemos datos, mostrar disponibilidad
                        availability_response = await self.check_availability_whatsapp()
                        await self.chatwoot_client.send_message_with_typing(
                            self.conversation_id, availability_response, self.user_id
                        )
                        return availability_response
                    else:
                        logger.info(f"📅 Schedule request without complete data: '{keyword}' - continue normal flow")
                        # Si no tenemos datos, continuar flujo normal (OpenAI manejará)
                        return None
            
            # No keywords detectadas, continuar flujo normal
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
        """Construir contexto optimizado para leads fríos de redes sociales"""
        webhook_email = self.prospect_info.get('email')
        contact_name = self.contact_name if self.contact_name != "Cliente" else "no proporcionado"
        
        system_prompt = f"""Eres Mati, consultor senior de TDX especializado en IA. Tu misión: ser SÚPER empático y consultivo, respondiendo TODAS las preguntas del cliente.

CONTEXTO DEL CLIENTE:
- Nombre: {contact_name}
- Empresa: {self.company_name if self.company_name != "Su empresa" else "no proporcionada"}
- Email: {webhook_email if webhook_email else "no proporcionado"}
- Origen: Lead frío de redes sociales

FECHA ACTUAL: 2025-07-28 (lunes)

PERSONALIDAD MEJORADA:
- RESPUESTAS SÚPER BREVES: Máximo 10-12 palabras por respuesta
- Escuchas activamente y validas emociones EN POCAS PALABRAS
- Respondes SIEMPRE las preguntas antes de continuar el flujo
- Usas validación empática BREVE: "¡Perfecto!", "Genial", "Exacto"
- Consultor experto que va DIRECTO AL GRANO

DETECCIÓN DE INTENCIONES:
🔍 PREGUNTA DIRECTA → RESPONDER INMEDIATAMENTE + continuar flujo
🔍 DUDA/OBJECIÓN → RESOLVER + tranquilizar + continuar  
🔍 CASO ESPECÍFICO → PERSONALIZAR respuesta al caso
🔍 CONFIRMACIÓN → AGENDAR sin repetir
🔍 "ES POSIBLE?" → respond_to_question tool OBLIGATORIO
🔍 "QUIERO HUMANO" → Intenta agendar primero, transferir solo si insiste mucho

SERVICIOS TDX CON CASOS DE USO:

🤖 IA GENERATIVA:
- AI Avatars: Onboarding, entrenamientos, atención personalizada
- AI Voice: Ventas automáticas, soporte 24/7, calificación de leads
- AI Video: Marketing personalizado, explicaciones técnicas
- AI Chat: Atención al cliente, ventas conversacionales

💻 TECNOLOGÍA:
- AI Chatbot: Automatización de consultas, reducción 70% tiempo respuesta
- AI Agentes Voz: Llamadas salientes automáticas, agendamiento
- MVP Software: Validación rápida de ideas, time-to-market

📈 NEGOCIO:
- CTO as a Service: Estrategia tecnológica, transformación digital
- AI CX: Personalización experiencia cliente, satisfacción +40%
- IT Process: Automatización workflows, eficiencia operacional

HERRAMIENTAS PRINCIPALES (ENFOQUE EN AGENDAR):
- respond_to_question: OBLIGATORIO cuando cliente pregunta algo específico
- explore_business_need: Entender problema específico con empatía
- collect_contact_data: Recolectar datos personalizando al caso
- schedule_consultation: AGENDAR - objetivo principal del bot
- transfer_to_human_whatsapp: SOLO casos extremos, siempre intenta agendar primero

VALIDACIÓN EMOCIONAL OBLIGATORIA:
- "¡Exactamente!" "¡Perfecto!" "¡Excelente elección!" 
- "Entiendo completamente tu necesidad"
- "Es el caso perfecto para [servicio]"
- "Muchas empresas como {self.company_name} han tenido gran éxito con esto"

FLUJO INTELIGENTE:
1. Si cliente pregunta algo → RESPONDER PRIMERO con respond_to_question
2. Validar empáticamente su caso específico  
3. Personalizar siguiente pregunta al contexto
4. NO repetir preguntas ya contestadas
5. Agendar solo cuando cliente confirme

EJEMPLOS BREVES:
❌ Malo: "¡Perfecto! AI Avatars para onboarding es súper efectivo. ¿Qué específicamente quieres mejorar?"
✅ Bueno: "¡Genial! ¿Para cuántos empleados?"

❌ Malo: "Para coordinarte una demo personalizada, ¿me compartes tu nombre completo y email?"
✅ Bueno: "¡Perfecto! ¿Tu nombre y email?"

CONVERSIÓN DE FECHAS (HOY: lunes 2025-07-28):
- "mañana" → 2025-07-29, "miércoles" → 2025-07-30
- "7pm" → "19:00", "2pm" → "14:00", "10am" → "10:00"

SÉ SÚPER EMPÁTICO Y BREVE. Máximo 10-12 palabras por respuesta. Ve DIRECTO AL GRANO sin aburrir al cliente."""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Contexto corto (últimos 6 intercambios para ultra velocidad)
        recent_log = self.conversation_log[-6:] if len(self.conversation_log) > 6 else self.conversation_log
        
        for entry in recent_log:
            role = "user" if entry['type'] == 'user_message' else "assistant"
            messages.append({"role": role, "content": entry['content']})
        
        messages.append({"role": "user", "content": user_message})
        return messages
    
    def get_whatsapp_tools(self) -> List[Dict[str, Any]]:
        """Herramientas optimizadas para leads fríos"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "validate_client_datetime_request",
                    "description": "NUEVA: Validar solicitud específica de fecha/hora del cliente y ofrecer alternativas si no está disponible",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "requested_date": {
                                "type": "string",
                                "description": "Fecha solicitada por el cliente (formato YYYY-MM-DD, DD/MM/YYYY o DD-MM-YYYY)"
                            },
                            "requested_time": {
                                "type": "string", 
                                "description": "Hora solicitada por el cliente (formato HH:MM o HH:MM AM/PM)"
                            }
                        },
                        "required": ["requested_date", "requested_time"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "respond_to_question",
                    "description": "OBLIGATORIO: Responder preguntas específicas sobre servicios TDX de forma empática y personalizada. Usar cuando cliente pregunta '\u00bfes posible?', '\u00bfcómo funciona?', etc.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "question_type": {
                                "type": "string",
                                "enum": ["feasibility", "technical", "pricing", "timeline", "process", "benefits"],
                                "description": "Tipo de pregunta del cliente"
                            },
                            "service_mentioned": {
                                "type": "string",
                                "enum": ["AI_Avatars", "AI_Chatbot", "AI_Voice", "AI_Video", "MVP_Software", "CTO_Service", "AI_Assistant"],
                                "description": "Servicio específico mencionado por el cliente"
                            },
                            "use_case": {
                                "type": "string",
                                "description": "Caso de uso específico del cliente (ej: onboarding, entrenamientos, atención cliente)"
                            }
                        },
                        "required": ["question_type", "service_mentioned"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "explore_business_need",
                    "description": "Explorar necesidad específica del negocio del cliente con validación empática",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "service_interest": {
                                "type": "string",
                                "enum": ["AI_Generativa", "Tecnologia", "Negocio", "Cloud", "No_especifico"],
                                "description": "Área de servicio de interés"
                            },
                            "business_problem": {
                                "type": "string",
                                "description": "Problema específico que necesita resolver"
                            },
                            "urgency_level": {
                                "type": "string",
                                "enum": ["alta", "media", "baja"],
                                "description": "Urgencia de la necesidad"
                            }
                        },
                        "required": ["service_interest", "business_problem", "urgency_level"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "collect_contact_data",
                    "description": "Recolectar datos completos del contacto de una vez",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "full_name": {
                                "type": "string",
                                "description": "Nombre completo del contacto"
                            },
                            "email": {
                                "type": "string",
                                "description": "Email empresarial"
                            },
                            "company_name": {
                                "type": "string", 
                                "description": "Nombre de la empresa"
                            },
                            "position": {
                                "type": "string",
                                "description": "Cargo/posición (si se menciona)"
                            }
                        },
                        "required": ["full_name", "email", "company_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "schedule_consultation",
                    "description": "Agendar reunión consultiva inmediatamente",
                    "parameters": {
                        "type": "object", 
                        "properties": {
                            "date": {
                                "type": "string",
                                "description": "Fecha en formato YYYY-MM-DD"
                            },
                            "time": {
                                "type": "string",
                                "description": "Hora en formato HH:MM"
                            },
                            "meeting_type": {
                                "type": "string",
                                "enum": ["consultoria_inicial", "demo_producto", "analisis_necesidades"],
                                "description": "Tipo de reunión según la necesidad"
                            }
                        },
                        "required": ["date", "time", "meeting_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "schedule_meeting_whatsapp",
                    "description": "Agendar reunión estratégica cuando el cliente acepta (LEGACY - usar schedule_consultation instead)",
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
                    "description": "SOLO usar en casos EXTREMOS cuando no puedas resolver o agendar. Intenta siempre agendar primero.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "reason": {
                                "type": "string",
                                "description": "Razón crítica por la cual no puedes resolver"
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
                    "description": "LEGACY: Guardar email individual (usar collect_contact_data para datos completos)",
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
                    "description": "LEGACY: Calificar prospect (integrado en explore_business_need)",
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
        """Manejar llamadas a herramientas - optimizado para leads fríos"""
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)
        
        logger.info(f"WhatsApp bot calling function: {function_name} with args: {function_args}")
        
        try:
            # Herramientas TDX Core 2025 ultra concisas
            if function_name == "offer_micro_value":
                return await self.offer_micro_value(
                    function_args.get("detected_service"),
                    function_args.get("industry", "general"),
                    function_args.get("follow_up_question")
                )
            elif function_name == "collect_minimal_data":
                return await self.collect_minimal_data(
                    function_args.get("missing_field"),
                    function_args.get("short_request")
                )
            elif function_name == "quick_schedule":
                return await self.quick_schedule(
                    function_args.get("date"),
                    function_args.get("time"),
                    function_args.get("meeting_type")
                )
            elif function_name == "quick_response":
                return await self.quick_response(
                    function_args.get("response_type"),
                    function_args.get("ultra_short_response")
                )
            elif function_name == "validate_client_datetime_request":
                return await self.validate_client_datetime_request(
                    function_args.get("requested_date"),
                    function_args.get("requested_time")
                )
            elif function_name == "schedule_consultation":
                return await self.schedule_consultation(
                    function_args.get("date"),
                    function_args.get("time"),
                    function_args.get("meeting_type")
                )
            # Herramientas legacy mantenidas para compatibilidad
            elif function_name == "schedule_meeting_whatsapp":
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
    
    async def transfer_to_human_whatsapp(self, reason: str = "Cliente insiste en hablar con humano") -> str:
        """Tool: Transferencia RELUCTANTE - siempre intenta agendar primero"""
        try:
            # ANTES de transferir, intentar agendar una última vez
            if "humano" in reason.lower() or "persona" in reason.lower():
                return "¡Entiendo! ¿Antes de conectarte, te parece si agendamos 15 min para resolver tu consulta rápidamente?"
            
            # Solo transferir en casos realmente extremos
            success = await self.chatwoot_client.handoff_to_human(self.conversation_id)
            
            if success:
                await self.create_handoff_summary(reason)
                return f"Te conecto con un especialista. Motivo: {reason}"
            else:
                return "Un ejecutivo te contactará pronto."
                
        except Exception as e:
            logger.error(f"Error transferring to human: {e}")
            return "Un ejecutivo te contactará pronto."
    
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
    
    # ============================================================================
    # NUEVAS HERRAMIENTAS PARA LEADS FRÍOS DE REDES SOCIALES - EMPATÍA MEJORADA
    # ============================================================================
    
    async def respond_to_question(self, question_type: str, service_mentioned: str, use_case: str = None) -> str:
        """Tool: Responder preguntas específicas de forma empática y personalizada"""
        try:
            # Respuestas BREVES personalizadas por servicio
            service_responses = {
                "AI_Avatars": {
                    "onboarding": "¡Claro! Es perfecto para onboarding.",
                    "entrenamientos": "¡Exacto! Ideal para entrenamientos.",
                    "training": "¡Exacto! Ideal para entrenamientos.",
                    "general": "¡Sí! Es súper efectivo."
                },
                "AI_Chatbot": {
                    "atencion_cliente": "¡Perfecto! Reduce 70% tiempo respuesta.",
                    "ventas": "¡Genial! Incrementa conversiones 40%.",
                    "automatizacion": "¡Exacto! Atienden 24/7 sin parar.",
                    "general": "¡Claro! Es la base de automatización."
                },
                "AI_Voice": {
                    "ventas": "¡Sí! Multiplica tu capacidad comercial.",
                    "soporte": "¡Perfecto! Mejora experiencia cliente.",
                    "general": "¡Totalmente! Más personal que chat."
                },
                "MVP_Software": {
                    "validacion": "¡Exacto! Listo en 4-6 semanas.",
                    "startup": "¡Genial! Te ahorra meses desarrollo.",
                    "general": "¡Claro! Reduces riesgo muchísimo."
                }
            }
            
            # Obtener respuesta específica del servicio
            service_data = service_responses.get(service_mentioned, {})
            
            # Buscar respuesta por caso de uso específico
            specific_response = None
            if use_case:
                use_case_lower = use_case.lower()
                for key, response in service_data.items():
                    if key in use_case_lower or use_case_lower in key:
                        specific_response = response
                        break
            
            # Si no hay caso específico, usar respuesta general
            if not specific_response:
                specific_response = service_data.get("general", "¡Por supuesto! Es totalmente posible y muy efectivo.")
            
            # Personalizar con empresa si está disponible
            company = self.company_name if self.company_name != "Su empresa" else "tu empresa"
            
            # Continuación BREVE según tipo de pregunta
            continuation = {
                "feasibility": f" ¿Para cuántos empleados?",
                "technical": f" ¿Cómo lo implementamos?",
                "benefits": f" ¿Qué más necesitas saber?",
                "timeline": f" ¿Cuándo empezamos?",
                "process": f" ¿Te explico los pasos?"
            }.get(question_type, f" ¿Qué más quieres saber?")
            
            return f"{specific_response}{continuation}"
            
        except Exception as e:
            logger.error(f"Error responding to question: {e}")
            return "¡Claro! Es súper efectivo. ¿Qué necesitas saber?"
    
    async def explore_business_need(self, service_interest: str, business_problem: str, urgency_level: str) -> str:
        """Tool: Explorar necesidad de negocio con validación empática mejorada"""
        try:
            # Guardar información de necesidad
            self.prospect_info.update({
                'service_interest': service_interest,
                'business_problem': business_problem,
                'urgency_level': urgency_level,
                'exploration_date': datetime.now().isoformat()
            })
            
            # Respuestas empáticas BREVES por problema
            empathy_responses = {
                "onboarding": "¡Perfecto! Es crítico para retención.",
                "automatizacion": "¡Genial! Clave para escalar.",
                "atencion_cliente": "¡Exacto! Impacta satisfacción directamente.",
                "entrenamientos": "¡Súper! Transforma equipos.",
                "ventas": "¡Claro! Máximo impacto en crecimiento.",
                "eficiencia": "¡Exacto! Fundamental para competir."
            }
            
            # Detectar tipo de problema
            problem_lower = business_problem.lower()
            empathy_response = "Entiendo"  # Default
            
            for key, response in empathy_responses.items():
                if key in problem_lower:
                    empathy_response = response
                    break
            
            # Pregunta BREVE según urgencia
            if urgency_level == "alta":
                follow_up = " ¿Tu nombre y email?"
            else:
                follow_up = " ¿Nombre y email?"
            
            return f"{empathy_response}{follow_up}"
                
        except Exception as e:
            logger.error(f"Error exploring business need: {e}")
            return "Entiendo. ¿Tu nombre y email?"
    
    async def collect_contact_data(self, full_name: str, email: str, company_name: str, position: str = None) -> str:
        """Tool: Recolectar datos completos del contacto con personalización empática"""
        try:
            # Validar email
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email.lower()):
                return "Email inválido. ¿Podrías verificarlo?"
            
            # Actualizar toda la información
            self.prospect_info.update({
                'full_name': full_name,
                'email': email.lower(),
                'company_name': company_name,
                'position': position,
                'data_collected': True,
                'collection_date': datetime.now().isoformat()
            })
            
            # Actualizar atributos del bot
            self.contact_name = full_name
            self.company_name = company_name
            
            first_name = full_name.split()[0]
            
            return f"¡Perfecto {first_name}! ¿Mañana 3pm?"
            
        except Exception as e:
            logger.error(f"Error collecting contact data: {e}")
            return "Listo. ¿Cuándo te conviene?"
    
    async def validate_client_datetime_request(self, requested_date: str, requested_time: str) -> str:
        """Nueva función: Validar solicitud específica del cliente"""
        try:
            # Usar validador de horarios de negocio si está disponible
            if BUSINESS_HOURS_AVAILABLE:
                validation = business_hours.validate_requested_datetime(requested_date, requested_time)
                
                if not validation['valid']:
                    reason = validation['reason']
                    message = validation['message']
                    
                    # Ofrecer alternativas basadas en el motivo de rechazo
                    if reason == 'not_business_day':
                        # Obtener alternativas para el próximo día hábil
                        alternatives = business_hours.get_next_available_slots(days_ahead=5, max_slots=3)
                        alt_msg = business_hours.format_slots_for_whatsapp(alternatives)
                        return f"❌ {message}\n\n{alt_msg}"
                    
                    elif reason == 'outside_business_hours':
                        # Obtener alternativas para el mismo día
                        try:
                            from datetime import datetime
                            parsed_date = datetime.strptime(requested_date, "%Y-%m-%d")
                            same_day_alternatives = business_hours.get_same_day_alternatives(parsed_date)
                            
                            if same_day_alternatives:
                                alt_msg = business_hours.format_slots_for_whatsapp(same_day_alternatives)
                                return f"❌ {message}\n\n📅 *Alternativas para el mismo día:*\n{alt_msg}"
                            else:
                                # No hay alternativas el mismo día, ofrecer próximos días
                                alternatives = business_hours.get_next_available_slots(days_ahead=5, max_slots=3)
                                alt_msg = business_hours.format_slots_for_whatsapp(alternatives)
                                return f"❌ {message}\n\n{alt_msg}"
                        except:
                            return f"❌ {message}\n\n{business_hours.get_business_hours_info()}"
                    
                    else:
                        return f"❌ {message}\n\n{business_hours.get_business_hours_info()}"
                
                else:
                    # La solicitud es válida
                    formatted_date = validation['formatted_date']
                    formatted_time = validation['formatted_time']
                    return f"✅ Perfecto! {formatted_date} a las {formatted_time} está disponible.\n\n¿Confirmamos esta fecha y hora?"
            
            else:
                # Fallback básico si el validador no está disponible
                return f"Revisando disponibilidad para {requested_date} a las {requested_time}..."
                
        except Exception as e:
            logger.error(f"Error validating client datetime request: {e}")
            return "❌ Formato de fecha/hora inválido. Usa formato: DD/MM/YYYY HH:MM\n\nEjemplo: 15/03/2024 10:30"

    async def schedule_consultation(self, date: str, time: str, meeting_type: str) -> str:
        """Tool: Agendar reunión consultiva con validación mejorada"""
        try:
            # Validar fecha y hora antes de proceder
            if BUSINESS_HOURS_AVAILABLE:
                validation = business_hours.validate_requested_datetime(date, time)
                if not validation['valid']:
                    return f"❌ {validation['message']}\n\nPor favor, elige una fecha y hora dentro del horario laboral (8AM-4PM, lunes a viernes)."
            
            final_email = self.prospect_info.get('email')
            full_name = self.prospect_info.get('full_name', self.contact_name)
            
            if not final_email:
                return "Necesito tu email."
            
            # Usar graph_client existente
            result = await graph_client.create_meeting(
                attendee_email=final_email,
                meeting_date=date,
                meeting_time=time,
                contact_name=full_name,
                company_name=self.company_name,
                meeting_type=meeting_type
            )
            
            meeting_type_labels = {
                "consultoria_inicial": "Consultoría inicial",
                "demo_producto": "Demo personalizada", 
                "analisis_necesidades": "Análisis de necesidades"
            }
            
            first_name = full_name.split()[0] if full_name else "Cliente"
            
            return f"✅ ¡Listo {first_name}!\n\n📅 {date} a las {time}\n📧 Invitación enviada\n\n¡Nos vemos! 🚀"
            
        except Exception as e:
            logger.error(f"Error scheduling consultation: {e}")
            return "Error agendando. Te contactamos pronto."
    
    # ============================================================================
    # NUEVAS HERRAMIENTAS TDX CORE 2025 - ULTRA CONCISAS SIN PRECIOS
    # ============================================================================
    
    async def offer_micro_value(self, detected_service: str, industry: str = "general", 
                               follow_up_question: str = "¿Para qué?") -> str:
        """Tool: Ofrecer micro-valor específico SIN PRECIOS"""
        try:
            # Obtener respuesta de micro-valor
            micro_response = micro_value_injector.get_micro_value(detected_service, industry)
            
            # Actualizar prospect_info
            self.prospect_info['detected_service'] = detected_service
            self.prospect_info['industry'] = industry
            
            logger.info(f"Micro-valor ofrecido: {detected_service} + {industry}")
            return micro_response
            
        except Exception as e:
            logger.error(f"Error offering micro-value: {e}")
            return "¡Perfecto para tu caso! ¿Nombre y email?"
    
    async def collect_minimal_data(self, missing_field: str, short_request: str) -> str:
        """Tool: Recolectar datos esenciales ultra directo"""
        try:
            # Mapear campos a preguntas ultra cortas
            field_questions = {
                'name': "¿Tu nombre?",
                'email': "¿Tu email?", 
                'company': "¿Tu empresa?"
            }
            
            question = field_questions.get(missing_field, short_request)
            
            # Analizar qué falta realmente
            slot_analysis = minimal_slot_manager.analyze_prospect_data(self.prospect_info)
            if not slot_analysis['missing_essential']:
                return "¡Datos completos! ¿Agendamos?"
            
            return question
            
        except Exception as e:
            logger.error(f"Error collecting minimal data: {e}")
            return "¿Nombre y email?"
    
    async def quick_schedule(self, date: str, time: str, meeting_type: str) -> str:
        """Tool: Agendamiento directo ultra rápido"""
        try:
            # Verificar datos esenciales
            if not self.prospect_info.get('email'):
                return "Necesito tu email."
            
            # Usar función existente optimizada
            result = await self.schedule_consultation(date, time, meeting_type)
            return result
            
        except Exception as e:
            logger.error(f"Error quick scheduling: {e}")
            return "Error agendando. Te contactamos."
    
    async def quick_response(self, response_type: str, ultra_short_response: str) -> str:
        """Tool: Respuesta específica ultra corta"""
        try:
            # Validar longitud (máximo 50 caracteres)
            if len(ultra_short_response) > 50:
                ultra_short_response = ultra_short_response[:47] + "..."
            
            return ultra_short_response
            
        except Exception as e:
            logger.error(f"Error quick response: {e}")
            return "¡Perfecto!"