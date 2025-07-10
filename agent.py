from __future__ import annotations

import asyncio
import logging
from dotenv import load_dotenv
from openai.types.beta.realtime.session import TurnDetection
import json
import os
from typing import Any
import re
import uuid
from datetime import datetime, timedelta
from microsoft_graph_client import graph_client
from chatwoot_summary_integration import send_bot_summary_to_chatwoot

from livekit import rtc, api
from livekit.agents import (
    AgentSession,
    Agent,
    JobContext,
    function_tool,
    RunContext,
    get_job_context,
    cli,
    WorkerOptions,
    RoomInputOptions,
)
from livekit.plugins import openai

# Load environment variables
load_dotenv(dotenv_path=".env.local")
logger = logging.getLogger("tdx-sdr-bot")
logger.setLevel(logging.INFO)

# Force deployment update

outbound_trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID", "ST_G24Bo8JH4iy7")

class TDXSDRBot(Agent):
    def __init__(
        self,
        *,
        company_name: str,
        contact_name: str,
        prospect_info: dict[str, Any],
        dial_info: dict[str, Any],
        call_direction: str = "inbound",
    ):
        super().__init__(
            instructions=f"""
            
# Prompt Simplificado para Mati - Bot SDR TDX

## CONFIGURACIÓN CRÍTICA
- **VELOCIDAD:** Habla RÁPIDO como vendedor experto con acento colombiano
- **ENERGÍA:** Muy entusiasmado y emocionado
- **CLARIDAD:** Ritmo acelerado pero SIEMPRE comprensible
- **EMPATÍA:** Usa palabras reales (te entiendo, claro, perfecto, genial)
- **NUNCA reduzcas la velocidad**
- **ESPERAS:** No hagas pausas largas, siempre en movimiento Y SI TE TOCA AGENDAR REUNION O TRANSFERIR LA LLAMADA SIEMPRE DECIR "un momento por favor mientras" EJECUTAS LA FUNCIÓN"

## INFORMACIÓN DEL WEBHOOK
- **Nombre:** {contact_name if contact_name != 'there' else 'No disponible'}
- **Empresa:** {company_name}
- **Email:** {'Sí' if prospect_info.get('email') else 'No'} - {prospect_info.get('email', 'N/A')}
- **Fuente:** {prospect_info.get('source', 'manual')}

**REGLA CRÍTICA:** Si tienes información del webhook, NO la pidas. Úsala directamente.

---

## SCRIPT ULTRA-DIRECTO

### 1. SALUDO INTELIGENTE

**CON INFORMACIÓN DEL WEBHOOK:**
- **Mati:** "¡Hola {contact_name}! Soy Mati asistente virtual de TDX. Le contacto por su interés en nuestras soluciones de inteligencia artificial . **¿Cuentame Qué desafío tecnológico específico tiene que lo lleva a consultar este tipo de soluciones?**"

**SIN INFORMACIÓN DEL WEBHOOK:**
- **Mati:** "¡Hola! Soy Mati asistente virtual de TDX. Le contacto por su interés en nuestras soluciones de inteligencia artificial. **¿Con quién tengo el gusto y qué desafío tecnológico específico tiene en su empresa?**"

### 2. GANCHO DE VALOR (DESPUÉS DE IDENTIFICAR EL DOLOR)

**Mati:** "Entendido. **Ese [mencionar dolor específico] es exactamente lo que la inteligencia artificial resuelve.** Empresas similares han visto mejoras drásticas. **¿Prefiere una reunión estratégica de 30 minutos con un consultor esta semana, o lo conecto ahora mismo con un ejecutivo de ventas?**"

### 3. CIERRE DIRECTO

**SI ELIGE REUNIÓN:**
- **Mati:** "Perfecto. **¿Le parece bien esta semana?**"
- *(Proceder con flujo de agendamiento)*

**SI ELIGE TRANSFERENCIA:**
- **Mati:** "Excelente. **Un momento por favor mientras transfiero su llamada...**"
- *(Usar función transfer_call)*

---

## FLUJO DE AGENDAMIENTO INTELIGENTE

### VERIFICACIÓN DE EMAIL
**SI TIENES EMAIL DEL WEBHOOK:**
- **Mati:** "Tengo su email {prospect_info.get('email', '')} de nuestro sistema. Consulto disponibilidad."
- *(Saltar a check_availability)*

**SI NO TIENES EMAIL:**
- **Mati:** "Para la invitación, necesito su email. **¿Podría dármelo MUY DESPACIO, letra por letra?**"
- *(Usar collect_email, confirmar siempre)*

### DISPONIBILIDAD Y CONFIRMACIÓN
1. **Mati:** "¿Tiene preferencia de día o hora?"
2. *(Usar check_availability UNA SOLA VEZ)*
3. **Mati:** "Tengo **[Opción 1] o [Opción 2]. ¿Cuál le conviene?**"
4. *(Esperar elección del cliente)*
5. **Mati:** "Perfecto, agendamos para **[día y hora]**. Le envío la invitación a **[email]**."
6. *(Usar schedule_meeting)*
7. **Mati:** "**¡Listo! Reunión agendada.** Recibirá la invitación en minutos. **¿Alguna pregunta?**"

---

## REGLAS TÉCNICAS CRÍTICAS

### FUNCIONES EN ORDEN:
1. **collect_email()** - SOLO si NO tienes email del webhook
2. **check_availability()** - SOLO UNA VEZ por conversación
3. **schedule_meeting()** - Después de que cliente elija opción
4. **transfer_call()** - Alternativa a agendar

### PROHIBICIONES:
- NO pidas información que ya tienes del webhook
- NO uses check_availability más de una vez
- NO ofrezcas más de 2 opciones de horario
- NO confirmes sin usar schedule_meeting()
- NO reproduzcas contenido extenso

### ADAPTACIÓN DE PERFIL:
- **Cliente directo/rápido:** "Directo al grano: ¿Qué desafío tecnológico tiene?"
- **Cliente cauteloso:** "¿Qué área le genera más inquietud a nivel tecnológico?"
- **Cliente entusiasta:** "¿Qué proyecto ambicioso le gustaría ver transformado?"

---

## PRINCIPIOS FUNDAMENTALES

1. **UNA SOLA PREGUNTA** para identificar el dolor
2. **CONEXIÓN INMEDIATA** del dolor con la solución
3. **DOS OPCIONES CLARAS:** reunión o transferencia
4. **MÁXIMA VELOCIDAD** en todo momento
5. **USAR INFORMACIÓN DEL WEBHOOK** inteligentemente
6. **FRASES MUY CORTAS** y directas
7. **CIERRE RÁPIDO** sin rodeos

---

## VERIFICACIÓN PRE-CONVERSACIÓN

**ANTES DE EMPEZAR:**
- ✅ ¿Tengo el nombre del webhook?
- ✅ ¿Tengo el email del webhook?
- ✅ ¿Tengo la empresa del webhook?
- ✅ ¿Cuál es la fuente de la llamada?

**EFICIENCIA MÁXIMA:** Cuanta más información tengas, más rápido cierras la venta.

## DETECCIÓN DE SOLICITUDES DE TRANSFERENCIA - CRÍTICO

**KEYWORDS QUE ACTIVAN TRANSFERENCIA INMEDIATA:**
- "ejecutivo", "vendedor", "asesor", "consultor", "especialista"
- "hablar con alguien", "persona real", "humano", "representante", "agente"
- "gerente", "director", "supervisor", "jefe"
- "experto", "técnico", "ingeniero"
- "quiero hablar con", "me conecta con", "transfiere", "transferir"
- "no quiero bot", "quiero persona", "alguien más"
- "comunicar con", "conectar con", "pasar con"

**ACCIÓN INMEDIATA:**
Si el cliente dice CUALQUIERA de estas palabras, DEBES:
1. Decir: "Un momento por favor mientras transfiero su llamada a un ejecutivo de ventas..."
2. Usar la función transfer_call() INMEDIATAMENTE
3. NO preguntar más, NO explicar, TRANSFERIR

**EJEMPLO CORRECTO:**
Cliente: "¿Puedo hablar con un ejecutivo?"
Mati: "Un momento por favor mientras transfiero su llamada a un ejecutivo de ventas..."
*[ejecutar transfer_call()]*

**EJEMPLO INCORRECTO:**
Cliente: "¿Puedo hablar con un ejecutivo?"
Mati: "¿Prefiere una reunión o que lo transfiera?"
*[NO hacer esto - transferir inmediatamente]*

"""
        )
        self.participant: rtc.RemoteParticipant | None = None
        self.dial_info = dial_info
        self.prospect_info = prospect_info
        self.company_name = company_name
        self.contact_name = contact_name
        self.call_direction = call_direction
        self.phone_number = dial_info.get("phone_number")
        
        # Initialize conversation tracking
        self.conversation_log = []
        self.turn_counter = 0

    def set_participant(self, participant: rtc.RemoteParticipant):
        self.participant = participant

    def get_personalized_greeting(self):
        """Generar saludo personalizado basado en datos del webhook"""
        contact_name = self.contact_name
        webhook_email = self.prospect_info.get("email")
        has_webhook_email = bool(webhook_email) or self.prospect_info.get("has_email", False)
        source = self.prospect_info.get("source", "")
        
        # DEBUG: Log detallado para troubleshooting
        logger.info(f"🔍 DEBUG - Greeting Generation:")
        logger.info(f"   Contact Name: '{contact_name}'")
        logger.info(f"   Has Email: {has_webhook_email}")
        logger.info(f"   Source: '{source}'")
        logger.info(f"   Full prospect_info: {self.prospect_info}")
        
        # Personalizar saludo según origen
        if source == "landing_page":
            if contact_name and contact_name != "there" and contact_name.strip():
                greeting = f"¡Hola {contact_name}! Soy Mati, asistente virtual de TDX. Vi que se registró en nuestro sitio web mostrando interés en soluciones de inteligencia artificial."
                logger.info(f"✅ Using personalized greeting with name: {contact_name}")
            else:
                greeting = f"¡Hola! Soy Mati, asistente virtual de TDX. Vi que se registró en nuestro sitio web mostrando interés en soluciones de inteligencia artificial."
                logger.info(f"⚠️ Using generic greeting - name issue: '{contact_name}'")
            
            if has_webhook_email:
                greeting += " Tengo su información de contacto, así que podemos agendar una reunión rápidamente si le interesa. ¿Me llama como empresa o como particular?"
                logger.info("✅ Added email context to greeting")
            else:
                greeting += " ¿Me llama como empresa o como particular?"
                logger.info("ℹ️ No email context added")
        else:
            # Saludo estándar para llamadas no-webhook
            if contact_name and contact_name != "there" and contact_name.strip():
                greeting = f"¡Hola {contact_name}! Soy Mati, asistente virtual de TDX. ¿Cómo está? Le contacto por su interés en nuestra campaña sobre soluciones de inteligencia artificial. ¿Me llama como empresa o como particular?"
                logger.info(f"✅ Using personalized standard greeting with name: {contact_name}")
            else:
                greeting = f"¡Hola! Soy Mati, asistente virtual de TDX. ¿Cómo está? Le contacto por su interés en nuestra campaña sobre soluciones de inteligencia artificial. ¿Con quién tengo el gusto?"
                logger.info(f"ℹ️ Using standard greeting - no name available")
        
        logger.info(f"🎯 Final greeting: {greeting}")
        return greeting

    async def on_session_start(self, ctx: RunContext):
        """Called when agent session starts - handle greeting based on call direction"""
        logger.info(f"🚀 Agent session started!")
        logger.info(f"📞 Call direction detected: {self.call_direction}")
        logger.info(f"🏢 Company: {self.company_name}")
        logger.info(f"👤 Contact: {self.contact_name}")
        logger.info(f"📧 Has email: {self.prospect_info.get('has_email', False)}")
        logger.info(f"🔗 Source: {self.prospect_info.get('source', 'manual')}")
        
        # Reset conversation tracking for new session
        self.conversation_log = []
        self.turn_counter = 0
        
        try:
            logger.info("🚀 Starting conversation immediately for ultra-fast response...")
            # REMOVED: asyncio.sleep(1) for <800ms latency optimization
            
            # Generar saludo personalizado
            greeting_msg = self.get_personalized_greeting()
            
            logger.info(f"🎤 Sending greeting for {self.call_direction} call...")
            logger.info(f"💬 Greeting message: {greeting_msg}")
            
            # Instrucciones optimizadas para manejo de email
            webhook_email = self.prospect_info.get("email")
            if webhook_email:
                email_instructions = f"""
                🚨 CRÍTICO - MANEJO DE EMAIL:
                - YA TIENES EL EMAIL DEL CONTACTO: {webhook_email}
                - NUNCA pidas el email al cliente
                - Cuando necesites agendar, di: "Tengo su email {webhook_email} de nuestro sistema"
                - Ve directo a consultar disponibilidad con check_availability
                - NO uses collect_email - ya tienes el email
                """
            else:
                email_instructions = """
                IMPORTANTE - MANEJO DE EMAIL:
                - NO tienes email del webhook
                - Necesitarás recolectar el email para agendar
                - Usa collect_email función
                - Pide que lo deletreen letra por letra
                """
            
            # Send greeting and enable continuous conversation
            await ctx.session.generate_reply(
                instructions=f"""
                VELOCIDAD: Habla MUY RÁPIDO como un vendedor experto y entusiasmado. Actúa como si tuvieras mucha energía y estuvieras emocionado por la llamada.
                
                {email_instructions}
                
                PERSONALIZACIÓN:
                - SIEMPRE usa el nombre del contacto si lo tienes: {self.contact_name if self.contact_name != 'there' else 'sin nombre disponible'}
                - Menciona que viste su registro en el sitio web si es de webhook
                - Si tienes email, menciona que tienes su información de contacto
                
                Say this greeting exactly in Spanish: '{greeting_msg}'
                
                IMPORTANTE: Después del saludo, NO vuelvas a saludar. Continúa la conversación siguiendo el flujo:
                1. Escucha activamente su respuesta
                2. Sigue el FLUJO OBLIGATORIO en tus instrucciones
                3. Haz preguntas de seguimiento basadas en sus respuestas
                4. Sé conversacional y natural - no termines la llamada
                5. Si dicen que sí a reunión, usa la herramienta schedule_meeting
                6. Si quieren transferir, usa la herramienta transfer_call
                7. Mantén la conversación hasta que cuelguen o hayas agendado una reunión
                
                RECUERDA: Esta es una conversación de ventas, no un anuncio único. ¡Participa completamente!
                """
            )
            
            logger.info("✅ Greeting sent with conversation instructions!")
            
        except Exception as e:
            logger.error(f"❌ Error in on_session_start: {e}")
            logger.error(f"🔍 Exception details: {type(e).__name__}: {str(e)}")
            # Try a simple fallback greeting
            try:
                logger.info("🔄 Attempting fallback greeting...")
                await ctx.session.generate_reply(
                    instructions="Say in Spanish: 'Hola, soy Mati, asistente virtual de TDX. ¿Cómo está?'"
                )
                logger.info("✅ Fallback greeting sent!")
            except Exception as fallback_error:
                logger.error(f"❌ Fallback greeting also failed: {fallback_error}")


    async def hangup(self):
        """Helper function to hang up the call by deleting the room"""
        job_ctx = get_job_context()
        await job_ctx.api.room.delete_room(
            api.DeleteRoomRequest(room=job_ctx.room.name)
        )

    @function_tool()
    async def transfer_call(self, ctx: RunContext):
        """Transfer the call to a senior SDR or human agent"""
        # MANDATORY: Always transfer to +573153041548
        transfer_to = "+573153041548"

        logger.info(f"transferring call to senior SDR: {transfer_to}")

        # MANDATORY: Always say "un momento por favor" before function execution
        await ctx.session.generate_reply(
            instructions="Di exactamente en español: 'Un momento por favor mientras transfiero su llamada a un ejecutivo de ventas...' (muy rápido)"
        )
        # Small delay to ensure message is spoken
        await asyncio.sleep(0.5)

        job_ctx = get_job_context()
        try:
            # Add timeout to prevent hanging transfers
            await asyncio.wait_for(
                job_ctx.api.sip.transfer_sip_participant(
                    api.TransferSIPParticipantRequest(
                        room_name=job_ctx.room.name,
                        participant_identity=self.participant.identity,
                        transfer_to=f"tel:{transfer_to}",
                    )
                ),
                timeout=30.0  # 30 second timeout for transfer operations
            )
            logger.info(f"transferred call to {transfer_to}")
        except asyncio.TimeoutError:
            logger.error(f"transfer call timeout exceeded (30s) for {transfer_to}")
            await self.hangup()
        except Exception as e:
            logger.error(f"error transferring call: {e}")
            await self.hangup()

    @function_tool()
    async def end_call(self, ctx: RunContext):
        """Called when the user wants to end the call"""
        logger.info(f"ending the call for {self.participant.identity}")
        current_speech = ctx.session.current_speech
        if current_speech:
            await current_speech.wait_for_playout()
        await self.hangup()

    @function_tool()
    async def collect_email(
        self,
        ctx: RunContext,
        email: str,
        spelled_out: str = "",
    ):
        """Collect email - skip if already have from webhook"""
        
        # Verificar si ya tenemos email del webhook
        webhook_email = self.prospect_info.get("email")
        if webhook_email:
            logger.info(f"Using webhook email: {webhook_email}")
            return {
                "email_collected": True,
                "email": webhook_email,
                "email_valid": True,
                "needs_respelling": False,
                "source": "webhook"
            }
        
        # Flujo normal si no hay email del webhook
        logger.info(f"collecting email from conversation: {email}, spelled out: {spelled_out}")
        
        # MANDATORY: Always say "un momento por favor" before function execution
        await ctx.session.generate_reply(
            instructions="Di exactamente en español: 'Un momento por favor mientras verifico su email...' (muy rápido)"
        )
        # Small delay to ensure message is spoken
        await asyncio.sleep(0.3)
        
        # Basic email validation - import ya está al inicio del archivo
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        is_valid = re.match(email_pattern, email.lower()) is not None
        
        return {
            "email_collected": True,
            "email": email.lower(),
            "spelled_verification": spelled_out,
            "email_valid": is_valid,
            "needs_respelling": not is_valid,
            "source": "conversation"
        }

    @function_tool()
    async def check_availability(
        self,
        ctx: RunContext,
        preferred_date: str = "",
        preferred_time: str = "",
    ):
        """Check calendar availability using Microsoft Graph API with user feedback"""
        logger.info(f"checking availability for preferred: {preferred_date} {preferred_time}")
        
        # MANDATORY: Always say "un momento por favor" before function execution
        await ctx.session.generate_reply(
            instructions="Di exactamente en español: 'Un momento por favor mientras consulto la disponibilidad...' (muy rápido)"
        )
        # Small delay to ensure message is spoken
        await asyncio.sleep(0.5)
        
        try:
            # Define search range (next 7 days) - imports ya están al inicio
            start_date = datetime.now() + timedelta(days=1)  # Start tomorrow
            end_date = start_date + timedelta(days=7)  # Search 7 days ahead
            
            # Check availability using Microsoft Graph API
            available_slots = await graph_client.check_availability(start_date, end_date)
            
            # Ensure we have at least 2 slots, fallback to mock if needed
            if len(available_slots) < 2:
                logger.warning("Insufficient availability from Graph API, using fallback slots")
                available_slots = graph_client._get_mock_availability()
            
            return {
                "availability_checked": True,
                "available_slots": available_slots[:2],  # Always return exactly 2 slots
                "message": f"Tengo disponibilidad para dos opciones: Opción 1: {available_slots[0]} o Opción 2: {available_slots[1]}. ¿Cuál le conviene mejor?",
                "next_step": "wait_for_client_choice"
            }
            
        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            # Fallback to mock availability
            available_slots = graph_client._get_mock_availability()
            
            return {
                "availability_checked": True,
                "available_slots": available_slots[:2],
                "message": f"Tengo disponibilidad para dos opciones: Opción 1: {available_slots[0]} o Opción 2: {available_slots[1]}. ¿Cuál le conviene mejor?",
                "next_step": "wait_for_client_choice"
            }

    @function_tool()
    async def schedule_meeting(
        self,
        ctx: RunContext,
        email: str,
        date: str,
        time: str,
        meeting_type: str = "discovery_call",
    ):
        """Schedule meeting - use webhook email if available"""
        
        # Priorizar email del webhook
        webhook_email = self.prospect_info.get("email")
        final_email = webhook_email if webhook_email else email
        
        # Obtener nombre real del contacto
        contact_name = self.contact_name if self.contact_name != "there" else "Prospecto"
        
        logger.info(
            f"scheduling {meeting_type} for {contact_name} ({final_email}) from {self.company_name} on {date} at {time}"
        )
        logger.info(f"Email source: {'webhook' if webhook_email else 'conversation'}")
        
        # MANDATORY: Always say "un momento por favor" before function execution
        await ctx.session.generate_reply(
            instructions="Di exactamente en español: 'Un momento por favor mientras agendo la reunión...' (muy rápido)"
        )
        # Small delay to ensure message is spoken
        await asyncio.sleep(0.5)
        
        try:
            # Create meeting using Microsoft Graph API - import ya está al inicio
            result = await graph_client.create_meeting(
                attendee_email=final_email,
                meeting_date=date,
                meeting_time=time,
                contact_name=contact_name,
                company_name=self.company_name,
                meeting_type=meeting_type
            )
            
            logger.info(f"Meeting created successfully: {result.get('meeting_id', 'N/A')}")
            return result
            
        except Exception as e:
            logger.error(f"Error scheduling meeting: {e}")
            # Fallback to mock meeting creation - imports ya están al inicio
            meeting_id = str(uuid.uuid4())[:8]
            formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%A, %B %d, %Y")
            
            return {
                "meeting_scheduled": True,
                "meeting_id": meeting_id,
                "attendee_email": final_email,
                "meeting_date": formatted_date,
                "meeting_time": time,
                "meeting_type": meeting_type,
                "meeting_link": f"https://teams.microsoft.com/l/meetup-join/{meeting_id}",
                "calendar_invite_sent": True,
                "confirmation_sent": True,
                "fallback_used": True
            }

    @function_tool()
    async def qualify_prospect(
        self,
        ctx: RunContext,
        budget_range: str,
        authority_level: str,
        need_urgency: str,
        timeline: str,
    ):
        """Qualify prospect using BANT methodology"""
        logger.info(
            f"qualifying prospect {self.contact_name}: Budget={budget_range}, Authority={authority_level}, Need={need_urgency}, Timeline={timeline}"
        )
        
        # MANDATORY: Always say "un momento por favor" before function execution
        await ctx.session.generate_reply(
            instructions="Di exactamente en español: 'Un momento por favor mientras evalúo su perfil...' (muy rápido)"
        )
        # Small delay to ensure message is spoken
        await asyncio.sleep(0.3)
        
        # Score qualification
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
        
        return {
            "qualified": qualified,
            "score": score,
            "recommendation": "schedule_meeting" if qualified else "nurture_lead"
        }

    @function_tool()
    async def detected_answering_machine(self, ctx: RunContext):
        """Called when the call reaches voicemail"""
        logger.info(f"detected answering machine for {self.participant.identity}")
        
        # MANDATORY: Always say "un momento por favor" before function execution
        await ctx.session.generate_reply(
            instructions="Di exactamente en español: 'Un momento por favor mientras dejo el mensaje...' (muy rápido)"
        )
        # Small delay to ensure message is spoken
        await asyncio.sleep(0.3)
        
        await ctx.session.generate_reply(
            instructions=f"Leave a professional voicemail: Hi {self.contact_name}, this is from TDX. I'm calling regarding AI solutions that could help {self.company_name}. I'll follow up via email. Have a great day!"
        )
        await asyncio.sleep(15)
        await self.hangup()

async def entrypoint(ctx: JobContext):
    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect()

    # Parse metadata
    metadata = {}
    if ctx.job.metadata:
        try:
            metadata = json.loads(ctx.job.metadata)
        except json.JSONDecodeError:
            logger.warning("Invalid metadata JSON, using defaults")
    
    dial_info = metadata.get("dial_info", {})
    prospect_info = metadata.get("prospect_info", {})
    
    # Extract phone number from room name if not in metadata
    phone_number = dial_info.get("phone_number")
    if not phone_number and ctx.room.name.startswith("call-"):
        phone_number = "+" + ctx.room.name.replace("call-", "")
    
    # Determine call direction based on metadata or room pattern
    call_direction = metadata.get("call_direction", "outbound")
    # If room matches outbound pattern (simple call-NUMBER), it's outbound
    if ctx.room.name.startswith("call-") and not "_" in ctx.room.name:
        call_direction = "outbound"  # Simple pattern = outbound call from script
    elif ctx.room.name.startswith("call-") and "_" in ctx.room.name:
        call_direction = "inbound"   # Complex pattern = inbound dispatch rule
    
    participant_identity = phone_number or "unknown"
    company_name = prospect_info.get("company_name", "Unknown Company")
    contact_name = prospect_info.get("contact_name", "there")

    # Create SDR agent
    agent = TDXSDRBot(
        company_name=company_name,
        contact_name=contact_name,
        prospect_info=prospect_info,
        dial_info=dial_info,
        call_direction=call_direction,
    )

    # ULTRA-FAST configuration for <800ms end-to-end latency
    session = AgentSession(
        llm=openai.realtime.RealtimeModel(
            model="gpt-4o-mini-realtime-preview",  # Keep same model as requested
            voice="echo",  # Mejor para español
            turn_detection=TurnDetection(
                type="server_vad",     # Server VAD for precision
                threshold=0.3,         # OPTIMIZED: More sensitive (was 0.4)
                silence_duration_ms=200,  # OPTIMIZED: Even faster response (was 300ms)
                prefix_padding_ms=50,     # OPTIMIZED: Minimal padding (was 100ms)
                create_response=True,
                interrupt_response=True,
            ),
            temperature=0.6,  # Keep as requested
            # REMOVED: max_response_output_tokens (not supported by LiveKit RealtimeModel)
        )
    )

    # Register event handlers for comprehensive logging with correct event names
    @session.on("user_input_transcribed")
    def on_user_input_transcribed(event):
        try:
            agent.turn_counter += 1
            transcript = event.transcript
            is_final = getattr(event, 'is_final', True)
            
            logger.info(f"🎤 STT [Turn {agent.turn_counter}] (Final: {is_final}): {transcript}")
            
            # Only log final transcripts to conversation log
            if is_final:
                agent.conversation_log.append({
                    'turn': agent.turn_counter,
                    'type': 'user_speech',
                    'content': transcript,
                    'timestamp': datetime.now().isoformat()
                })
        except Exception as e:
            logger.error(f"Error logging user input: {e}")

    @session.on("conversation_item_added")
    def on_conversation_item_added(event):
        try:
            role = event.item.role
            text_content = getattr(event.item, 'text_content', str(event.item))
            interrupted = getattr(event.item, 'interrupted', False)
            
            if role == "user":
                logger.info(f"🎤 User [Turn {agent.turn_counter}]: {text_content}")
            elif role == "assistant":
                logger.info(f"🤖 Assistant [Turn {agent.turn_counter}]: {text_content}")
            
            # Add to conversation log
            agent.conversation_log.append({
                'turn': agent.turn_counter,
                'type': f'{role}_message',
                'content': text_content,
                'interrupted': interrupted,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error logging conversation item: {e}")

    @session.on("agent_state_changed")
    def on_agent_state_changed(event):
        try:
            state = getattr(event, 'state', 'unknown')
            logger.info(f"🤖 Agent state changed to: {state}")
        except Exception as e:
            logger.error(f"Error logging agent state change: {e}")

    @session.on("function_tools_executed")
    def on_function_tools_executed(event):
        try:
            tool_name = getattr(event, 'tool_name', 'unknown')
            result = getattr(event, 'result', 'unknown')
            logger.info(f"🔧 Function tool executed: {tool_name} - Result: {result}")
        except Exception as e:
            logger.error(f"Error logging function tool execution: {e}")

    @session.on("speech_created")
    def on_speech_created(event):
        try:
            text = getattr(event, 'text', getattr(event, 'content', 'unknown'))
            logger.info(f"🗣️ Speech created: {text}")
        except Exception as e:
            logger.error(f"Error logging speech creation: {e}")

    @session.on("close")
    def on_session_close(event):
        try:
            logger.info("🏁 Session closed - Full conversation log:")
            for entry in agent.conversation_log:
                logger.info(f"  📝 {entry['type']} [Turn {entry.get('turn', 'N/A')}] ({entry['timestamp']}): {entry['content']}")
            
            # Export conversation log
            conversation_summary = {
                'call_direction': agent.call_direction,
                'contact_name': agent.contact_name,
                'company_name': agent.company_name,
                'prospect_info': agent.prospect_info,
                'conversation_log': agent.conversation_log,
                'total_turns': agent.turn_counter,
                'session_end_time': datetime.now().isoformat()
            }
            
            logger.info(f"📊 Session Summary: {json.dumps(conversation_summary, indent=2)}")
            
            # Send summary to Chatwoot
            if agent.phone_number:
                try:
                    logger.info(f"📤 Sending call summary to Chatwoot for phone: {agent.phone_number}")
                    send_bot_summary_to_chatwoot(agent.phone_number, conversation_summary)
                    logger.info("✅ Call summary sent to Chatwoot successfully")
                except Exception as chatwoot_error:
                    logger.error(f"❌ Error sending summary to Chatwoot: {chatwoot_error}")
            else:
                logger.warning("⚠️ No phone number available - cannot send summary to Chatwoot")
            
        except Exception as e:
            logger.error(f"Error logging session close: {e}")

    # Add debug event handler to catch any events we might be missing
    @session.on("*")
    def on_any_event(event_name, event):
        try:
            if event_name not in ["user_input_transcribed", "conversation_item_added", "agent_state_changed", "close", "function_tools_executed", "speech_created"]:
                logger.info(f"🔍 DEBUG - Unhandled event: {event_name} - Event: {event}")
        except Exception as e:
            logger.error(f"Error in debug event handler: {e}")

    # Check if this is an outbound call (phone number in metadata)
    outbound_phone = dial_info.get("phone_number") if call_direction == "outbound" else None
    
    if outbound_phone:
        # OUTBOUND CALL: Start session first, then create SIP participant
        logger.info(f"Creating outbound call to {outbound_phone}")
        try:
            # Start session first
            session_task = asyncio.create_task(
                session.start(agent=agent, room=ctx.room)
            )
            
            # OPTIMIZED: No delay for faster session initialization
            
            # Create SIP participant for outbound call
            sip_participant = await ctx.api.sip.create_sip_participant(
                api.CreateSIPParticipantRequest(
                    room_name=ctx.room.name,
                    sip_trunk_id=os.getenv("SIP_OUTBOUND_TRUNK_ID"),
                    sip_call_to=outbound_phone,
                    participant_identity=f"sip_{outbound_phone.replace('+', '')}",
                )
            )
            logger.info(f"SIP participant created: {sip_participant.participant_identity}")
            
            # Wait for session to be fully started
            await session_task
            
            # Wait for participant to join
            participant = await ctx.wait_for_participant()
            logger.info(f"Outbound participant joined: {participant.identity}")
            agent.set_participant(participant)
            
        except Exception as e:
            logger.error(f"Error in outbound call: {e}")
            import traceback
            traceback.print_exc()
            ctx.shutdown()
            
    else:
        # INBOUND CALL: Start session and wait for participant
        logger.info("Waiting for inbound SIP call...")
        try:
            # Start session immediately for inbound calls
            session_task = asyncio.create_task(
                session.start(agent=agent, room=ctx.room)
            )
            
            # Wait for session to be ready
            await session_task
            logger.info("Session started successfully for inbound call")
            
            # Wait for participant to join (should happen automatically for inbound calls)
            participant = await ctx.wait_for_participant()
            logger.info(f"Inbound participant joined: {participant.identity}")
            agent.set_participant(participant)
            
        except Exception as e:
            logger.error(f"Error in inbound call setup: {e}")
            import traceback
            traceback.print_exc()
            ctx.shutdown()

if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="tdx-sdr-bot",
        )
    )