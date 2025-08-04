import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import requests
import openai

# Import all the AI components
from src.ai.intent_classifier import IntentClassifier
from src.ai.bant_scorer import BANTScorer
from src.ai.service_mapper import ServiceMapper
from src.ai.micro_value_injector import MicroValueInjector
from src.ai.minimal_slot_manager import MinimalSlotManager
from src.ai.conversation_guard import ConversationGuard
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
            'contact_info_complete': False
        }
        
        # Configuración de APIs
        self.chatwoot_account_id = os.getenv('VITE_CHATWOOT_ACCOUNT_ID')
        self.chatwoot_api_token = os.getenv('VITE_CHATWOOT_API_TOKEN')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        # Inicializar componentes de IA
        self.intent_classifier = IntentClassifier()
        self.bant_scorer = BANTScorer()
        self.service_mapper = ServiceMapper()
        self.value_injector = MicroValueInjector()
        self.slot_manager = MinimalSlotManager()
        self.conversation_guard = ConversationGuard()
        self.graph_client = MicrosoftGraphClient()
        
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
            
            # 1. Clasificación de intención con IA
            intent_result = self.intent_classifier.classify(message_content)
            logger.info(f"🎯 Intent classified: {intent_result}")
            
            # 2. Detección de servicio TDX
            service_match = self.service_mapper.detect_service(message_content)
            service_result = {
                'service': service_match.service if service_match else 'UNKNOWN',
                'confidence': service_match.confidence if service_match else 0.0,
                'matched_keywords': service_match.matched_keywords if service_match else []
            }
            logger.info(f"🔧 Service mapped: {service_result}")
            
            # 3. Actualizar datos recopilados del usuario
            self._update_collected_data(message_content)
            
            # 4. Actualización de slots (datos del prospect)
            current_prospect = self.slot_manager.get_current_prospect_info() if hasattr(self.slot_manager, 'get_current_prospect_info') else self.prospect_info
            slot_updates = self.slot_manager.extract_slots_from_message(message_content, current_prospect)
            if slot_updates:
                logger.info(f"📊 Slots updated: {slot_updates}")
            
            # 5. Generación de respuesta con IA
            ai_response = await self._generate_ai_response(message_content, intent_result, service_result)
            
            # 5. Verificación de guardia conversacional
            response = self.conversation_guard.check_for_loops(
                ai_response,
                str(self.conversation_id),
                self.conversation_log
            )
            
            # 6. Evaluación BANT después de cada mensaje
            current_prospect = self.prospect_info.copy()
            current_prospect.update(slot_updates)
            # Agregar servicio detectado al contexto del prospect
            if hasattr(intent_result, 'detected_service') and intent_result.detected_service:
                current_prospect['detected_service'] = intent_result.detected_service
            bant_score = self.bant_scorer.calculate_bant_score(
                current_prospect, message_content
            )
            logger.info(f"📊 BANT Score: {bant_score.total_score}/100")
            
            # 7. Decisión de agendamiento si BANT es alto
            if bant_score.total_score >= 60 and not self._already_scheduling():
                logger.info("📅 High BANT score detected - suggesting meeting")
                response += "\n\n¿Te gustaría agendar una llamada de 15 minutos para mostrarte cómo podemos ayudarte exactamente?"
                self.conversation_state = "scheduling"
            
            if response:
                # Log de la respuesta del bot
                self.conversation_log.append({
                    'timestamp': datetime.now().isoformat(),
                    'type': 'assistant_message',
                    'content': response,
                    'intent': intent_result,
                    'service': service_result,
                    'bant_score': bant_score.total_score
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
    
    async def _generate_ai_response(self, message: str, intent_result, service_result: Dict) -> str:
        """Generar respuesta inteligente usando OpenAI y toda la IA disponible"""
        
        # Obtener información actualizada del prospect
        current_prospect = self.prospect_info.copy()
        
        # Determinar el contexto de la conversación
        context = self._build_conversation_context(intent_result, service_result, current_prospect)
        
        # Analizar el historial de conversación para evitar repeticiones
        recent_bot_messages = [log.get('content', '') for log in self.conversation_log[-5:] if log.get('type') == 'assistant_message']
        recent_user_messages = [log.get('content', '') for log in self.conversation_log[-5:] if log.get('type') == 'user_message']
        
        # Detectar si el usuario está dando información específica que debemos reconocer
        scheduling_context = self._extract_scheduling_info(message, recent_user_messages)
        
        # Generar micro-valor específico si se detectó un servicio
        micro_value = ""
        if service_result['service'] != 'UNKNOWN' and service_result['confidence'] > 0.5:
            industry = getattr(intent_result, 'industry', 'general') or 'general'
            micro_value = self.value_injector.generate_micro_value(
                service_result['service'], industry, message
            )
        
        # Preparar prompt para OpenAI
        system_prompt = f"""Eres Mati, asistente virtual experto de TDX, empresa líder en soluciones de IA empresarial.

DATOS DEL CLIENTE:
- Nombre: {self.contact_name}
- Empresa: {self.company_name}
- Email: {current_prospect.get('email', 'No proporcionado')}
- Teléfono: {current_prospect.get('phone', 'No proporcionado')}

CONTEXTO CONVERSACIÓN:
{context}

HISTORIAL RECIENTE:
- Últimos mensajes del usuario: {'; '.join(recent_user_messages[-3:]) if recent_user_messages else 'Primer mensaje'}
- Últimas respuestas tuyas: {'; '.join(recent_bot_messages[-2:]) if recent_bot_messages else 'Primera respuesta'}

INFORMACIÓN DE AGENDAMIENTO DETECTADA:
{scheduling_context}

SERVICIOS TDX DISPONIBLES:
- AI_CHATBOT: Reduce 70% tiempo respuesta, automatización 24/7
- AI_VOICE: 60% mejor conversión, prospección automática  
- AI_ASSISTANT_WHATSAPP: 95% automatización WhatsApp
- AI_VIDEO: Avatares realistas para onboarding
- WEB_STARTER: Vitrina digital 24/7
- WEB_BUSINESS: Web + chat automático, 5x más leads
- WEB_ECOMMERCE: Ventas automáticas 24/7
- MVP: Producto mínimo viable en 15 días
- WHATSAPP_API: API oficial Meta
- SEO: 10x más visibilidad Google

INSTRUCCIONES CRÍTICAS:
1. NUNCA repitas preguntas que ya hiciste en mensajes anteriores
2. Si el usuario da información específica (horarios, fechas, servicios), RECONÓCELA y actúa en consecuencia
3. Si el usuario menciona "mañana 3pm" o horarios específicos, confirma y procede con el agendamiento
4. Mantén el flujo conversacional progresivo, no circular
5. Responde de forma conversacional, amigable pero profesional
6. Usa emojis apropiados (máximo 2 por mensaje)
7. NO menciones precios específicos, solo beneficios y ROI
8. Mantén respuestas entre 1-3 líneas máximo
9. Si detectas información de agendamiento, confirma y solicita datos faltantes (nombre, email)

MICRO-VALOR DETECTADO:
{micro_value}

Responde al siguiente mensaje del cliente:"""
        
        try:
            # Llamar a OpenAI para generar respuesta inteligente
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Agregar micro-valor si está disponible y no se incluyó ya
            if micro_value and micro_value.lower() not in ai_response.lower():
                ai_response += f"\n\n{micro_value}"
            
            logger.info(f"🤖 OpenAI response generated: {ai_response[:50]}...")
            return ai_response
            
        except Exception as e:
            logger.error(f"❌ OpenAI error: {e}")
            # Fallback a respuesta determinística
            return self._generate_fallback_response(message, intent_result, service_result)
    
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
        
        # CASO 1: Si ya tenemos toda la información de contacto
        if self.collected_data['contact_info_complete']:
            return "¡Perfecto! Ya tengo todos tus datos. Te contactaremos pronto para agendar la demo de automatización. ¡Gracias por tu interés en TDX!"
        
        # CASO 2: Usuario proporcionó teléfono (después de email)
        if has_phone and self.collected_data['email']:
            return "¡Excelente! Ya tengo tu email y teléfono. Te contactaremos muy pronto para coordinar la demo de automatización."
        
        # CASO 3: Usuario proporcionó email pero falta teléfono
        if has_email and not self.collected_data['phone']:
            # Pedir teléfono solo si no lo hemos pedido recientemente
            if not any('teléfono' in msg for msg in recent_bot_messages[-1:]):
                return "Excelente, Freddy. Para completar el agendamiento, ¿me podrías proporcionar tu número de teléfono?"
            else:
                return "Perfecto. Te contactaremos al email que proporcionaste para coordinar la demo."
        
        # CASO 4: Usuario proporcionó teléfono pero falta email
        if has_phone and not self.collected_data['email']:
            return "Perfecto, ya tengo tu teléfono. ¿Me puedes proporcionar tu email para enviarte la información de la demo?"
        
        # CASO 3: Usuario ya confirmó interés y mencionó servicio
        if has_confirmation and has_service_info:
            # Si no tenemos datos personales, pedirlos
            if not has_personal_data and not any('nombre' in msg and 'email' in msg for msg in recent_bot_messages[-2:]):
                return "¡Excelente! Para agendar la demo, ¿me puedes dar tu nombre completo y email?"
            else:
                return "Perfecto. Procederemos con el agendamiento en breve."
        
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
            
            # Detectar y actualizar email
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
            
            # Detectar interés en servicios
            if 'automatización' in message_lower or 'automatizar' in message_lower:
                self.collected_data['service_interest'] = 'automatización'
            elif 'chatbot' in message_lower:
                self.collected_data['service_interest'] = 'chatbots'
            elif 'finanzas' in message_lower:
                self.collected_data['service_interest'] = 'finanzas'
            
            # Detectar confirmación de demo
            if any(word in message_lower for word in ['si claro', 'si', 'sí', 'dale', 'ok', 'perfecto', 'genial']):
                if self.conversation_state in ['qualifying', 'scheduling']:
                    self.collected_data['demo_confirmed'] = True
            
            # Actualizar estado de información completa
            self.collected_data['contact_info_complete'] = bool(
                self.collected_data['email'] and 
                self.collected_data['phone'] and 
                self.collected_data['name']
            )
            
            # Actualizar estado de conversación basado en datos recopilados
            if self.collected_data['contact_info_complete'] and self.collected_data['demo_confirmed']:
                self.conversation_state = "closing"
            elif self.collected_data['service_interest'] and self.collected_data['demo_confirmed']:
                self.conversation_state = "scheduling"
            elif self.collected_data['service_interest']:
                self.conversation_state = "qualifying"
            
        except Exception as e:
            logger.error(f"Error updating collected data: {e}")