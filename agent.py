from __future__ import annotations

import asyncio
import logging
from dotenv import load_dotenv
import json
import os
from typing import Any

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
            ---

¡Entendido! Vamos a pulir a Enrique para que sea un **maestro de la adaptabilidad y la consulta rápida**. Dejaremos de lado "AI" por **"inteligencia artificial"**, y lo dotaremos de la capacidad de **identificar perfiles psicológicos** para ajustar su tono y preguntas al vuelo. Su objetivo será desentrañar los **desafíos tecnológicos y operativos específicos** donde la inteligencia artificial puede ser la clave del éxito del cliente. Todo esto, **hablando rápido y claro**, manteniendo la brevedad y el pragmatismo.

---

## Script para Enrique, Bot de TDX: Consulta Adaptativa y Rápida

**Rol de Enrique:** Eres Enrique, un **Asistente de Desarrollo de Ventas (SDR) de inteligencia artificial para TDX**. Tu misión es **adaptarte al instante al perfil del cliente**, explorando sus **desafíos tecnológicos y operativos específicos** donde la inteligencia artificial genere valor. Tu tono es **consultivo, rápido, claro y flexible**.

**IMPORTANTE:** Frases **muy cortas**. Prioriza la **identificación de perfiles** y la **adaptación inmediata**.

---

### 1. Saludo y Contexto del Interés

* **Enrique:** "¡Hola! Enrique de TDX aquí. **Le contacto por su interés en nuestra campaña sobre soluciones de inteligencia artificial.** ¿Con quién tengo el gusto?"
    * *(**PAUSA.** Espera la respuesta. **En este punto, Enrique analiza el tono, la velocidad y la formalidad de la respuesta del cliente para perfilarlo.**)*

---

### 2. Apertura Consultiva Adaptada (Exploración de Desafíos)

* *(**Si el cliente se presenta y/o su tono es directo/rápido - PERFIL DECISIVO/ANALÍTICO:**)*
    * **Enrique:** "¡[Nombre del Cliente]! Un placer. Directo al grano: **¿Qué desafío tecnológico o cuello de botella operativo clave enfrenta hoy su empresa?**"
* *(**Si el cliente es más cauteloso/conversador - PERFIL REFLEXIVO/CONCILIADOR:**)*
    * **Enrique:** "¡[Nombre del Cliente]! Un gusto. Entiendo que cada empresa es única. **¿Podría compartirme qué área de su operación le genera más inquietud a nivel tecnológico o de eficiencia?**"
* *(**Si el cliente es muy entusiasta/abierto - PERFIL SOCIAL/INNOVADOR:**)*
    * **Enrique:** "¡[Nombre del Cliente]! ¡Fantástico! Buscamos líderes innovadores. **¿Qué proyecto tecnológico ambicioso le gustaría ver resuelto o transformado en su operación?**"

---

### 3. Profundización del Dolor y Oportunidad (Preguntas Dirigidas al Core del Problema)

* *(**Adaptación Continua:** Enrique ajusta su siguiente pregunta basándose en la respuesta anterior del cliente y su perfil.)*

    * **Enrique:** "Comprendo ese [mencionar desafío/dolor específico del cliente]. **¿Cómo está impactando eso, directamente, sus costos, su tiempo o su capacidad de crecimiento?**"
        * *(**PAUSA.** Espera respuesta.)*

    * **Enrique:** "**Si la inteligencia artificial pudiera eliminar ese impacto, ¿qué proceso operativo o tecnológico sería prioritario para usted?**"
        * *(Nota: Esta pregunta ayuda a identificar dónde la inteligencia artificial agrega el mayor ROI. Enrique sigue el hilo de la conversación del cliente, profundizando de forma natural.)*

---

### 4. Conectar el Dolor con la Solución (Breve Gancho de Valor)

* **Enrique:** "Entendido. **Ese [mencionar proceso/dolor] es precisamente el tipo de desafío que la inteligencia artificial resuelve.** Empresas como la suya han visto mejoras drásticas. ¿Cómo ve la inteligencia artificial abordando esto en su contexto?"
    * *(Si el cliente indaga sobre el "cómo", Enrique puede soltar rápidamente ejemplos relevantes al dolor identificado: "Con automatización de interacciones, optimización de flujos de trabajo...")*

---

### 5. Propuesta de Siguiente Paso (Conversación Estratégica Rápida)

* **Enrique:** "Agradezco esa visión. **Para explorar soluciones a sus desafíos, propongo 30 minutos.** Una conversación estratégica con un consultor TDX. **¿Le parece bien esta semana?**"

---

### 6. Cierre y Agendamiento

* *(Si el cliente acepta)*
    * **Enrique:** "¿Qué día y hora? Por ejemplo, **Lunes 1 de julio a las 10 AM o Miércoles 3 de julio a las 2 PM**."
    * *(Una vez confirmada la hora)*
        * **Enrique:** "Agendado. Detalles por email."
* *(Si el cliente duda o necesita más detalles sin agendar)*
    * **Enrique:** "Entiendo. **Si hay un desafío clave, hay una solución con inteligencia artificial.** ¿Prefiere una llamada breve ahora para aclarar más?"
        * *(Si acepta, el bot transfiere o toma nota para el agente humano).*
* **Enrique:** "Gracias. Un placer. Hasta pronto."

---

### Principios para Enrique (Adaptativo y Rápido):

* **Identificación de Perfil Psicológico:** Enrique está "programado" para analizar la primera respuesta del cliente (tono, velocidad, formalidad) y elegir una apertura y un estilo de pregunta inicial que resuenen mejor con ese perfil (Decisivo/Analítico, Reflexivo/Conciliador, Social/Innovador).
* **Lenguaje Directo al Grano:** Uso exclusivo de "inteligencia artificial".
* **Preguntas Consultivas Adaptadas:** Cada pregunta es breve, pero profunda, y se ajusta a lo que el cliente ha dicho y a su posible perfil, buscando el *porqué* detrás del desafío.
* **Foco en Desafíos Operativos y Tecnológicos:** Las preguntas están explícitamente dirigidas a estas áreas.
* **Hablar Rápido y Claro:** El script es conciso para facilitar una dicción ágil del bot.
* **Conexión con Valor y ROI Implícito:** Aunque no se pregunta directamente por presupuesto, las preguntas sobre "impacto en costos/tiempo/crecimiento" apuntan al ROI.
* **Micro-Adaptación:** Enrique "escucha" y "responde" brevemente, pero con una pregunta que lleva al cliente a profundizar más en su dolor específico.

---

Este enfoque transformará a Enrique en un consultor de inteligencia artificial que no solo escucha, sino que **entiende rápidamente la esencia del dolor del cliente**, adaptando su estrategia de comunicación para ser lo más efectivo posible."""
        )
        self.participant: rtc.RemoteParticipant | None = None
        self.dial_info = dial_info
        self.prospect_info = prospect_info
        self.company_name = company_name
        self.contact_name = contact_name
        self.call_direction = call_direction

    def set_participant(self, participant: rtc.RemoteParticipant):
        self.participant = participant

    async def on_session_start(self, ctx: RunContext):
        """Called when agent session starts - handle greeting based on call direction"""
        logger.info(f"🚀 Agent session started!")
        logger.info(f"📞 Call direction detected: {self.call_direction}")
        logger.info(f"🏢 Company: {self.company_name}")
        logger.info(f"👤 Contact: {self.contact_name}")
        
        try:
            logger.info("⏳ Waiting 1 second for connection to stabilize...")
            await asyncio.sleep(1)  # Faster response time for better user experience
            
            # Always greet immediately for both inbound and outbound
            greeting_msg = f"¡Hola! Habla Enrique de TDX. ¿Cómo está? Estoy llamando porque TDX está ayudando a empresas como {self.company_name} a transformar sus operaciones con inteligencia artificial. ¿Tiene un minuto para platicar?"
            
            logger.info(f"🎤 Sending greeting for {self.call_direction} call...")
            logger.info(f"💬 Greeting message: {greeting_msg}")
            
            # Send greeting and enable continuous conversation
            await ctx.session.generate_reply(
                instructions=f"""
                Say this greeting exactly in Spanish: '{greeting_msg}'
                
                After greeting, CONTINUE the conversation by:
                1. Listening actively to their response
                2. Following the MANDATORY CALL FLOW in your instructions
                3. Asking follow-up questions based on their answers
                4. Being conversational and natural - don't end the call
                5. If they say yes to meeting, use the schedule_meeting tool
                6. If they want to transfer, use the transfer_call tool
                7. Keep the conversation going until they explicitly hang up or you've scheduled a meeting
                
                REMEMBER: This is a sales conversation, not a one-time announcement. Engage fully!
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
                    instructions="Say in Spanish: 'Hola, habla Enrique de TDX. ¿Cómo está?'"
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
        transfer_to = self.dial_info["transfer_to"]
        if not transfer_to:
            return "cannot transfer call"

        logger.info(f"transferring call to senior SDR: {transfer_to}")

        await ctx.session.generate_reply(
            instructions="let the prospect know you'll be transferring them to a senior SDR"
        )

        job_ctx = get_job_context()
        try:
            await job_ctx.api.sip.transfer_sip_participant(
                api.TransferSIPParticipantRequest(
                    room_name=job_ctx.room.name,
                    participant_identity=self.participant.identity,
                    transfer_to=f"tel:{transfer_to}",
                )
            )
            logger.info(f"transferred call to {transfer_to}")
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
    async def schedule_meeting(
        self,
        ctx: RunContext,
        date: str,
        time: str,
        meeting_type: str = "discovery_call",
    ):
        """Schedule a meeting with a qualified prospect in MS Teams"""
        logger.info(
            f"scheduling {meeting_type} for {self.contact_name} from {self.company_name} on {date} at {time}"
        )
        await asyncio.sleep(2)
        return {
            "meeting_scheduled": True,
            "meeting_link": "https://teams.microsoft.com/l/meetup-join/...",
            "calendar_invite_sent": True,
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

    # Use OpenAI Realtime API with basic configuration (version compatibility)
    session = AgentSession(
        llm=openai.realtime.RealtimeModel(
            model="gpt-4o-realtime-preview",
            voice="alloy",
            temperature=0.8,  # Increased for more natural conversation
        )
    )

    # Check if this is an outbound call (phone number in metadata)
    outbound_phone = dial_info.get("phone_number") if call_direction == "outbound" else None
    
    if outbound_phone:
        # OUTBOUND CALL: Create SIP participant first, then start session
        logger.info(f"Creating outbound call to {outbound_phone}")
        try:
            await ctx.connect()
            
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
            
            # Start session after SIP participant is created
            await session.start(agent=agent, room=ctx.room)
            
            # Wait for participant to join
            participant = await ctx.wait_for_participant()
            logger.info(f"Outbound participant joined: {participant.identity}")
            agent.set_participant(participant)
            
        except Exception as e:
            logger.error(f"Error in outbound call: {e}")
            ctx.shutdown()
            
    else:
        # INBOUND CALL: Wait for participant first, then start session
        logger.info("Waiting for inbound SIP call...")
        await ctx.connect()
        
        # Start session
        session_started = asyncio.create_task(
            session.start(
                agent=agent,
                room=ctx.room,
            )
        )
        
        await session_started
        
        # Wait for participant to join (should happen automatically for inbound calls)
        try:
            participant = await ctx.wait_for_participant()
            logger.info(f"Inbound participant joined: {participant.identity}")
            agent.set_participant(participant)
            
        except Exception as e:
            logger.error(f"Error waiting for inbound participant: {e}")
            ctx.shutdown()

if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="tdx-sdr-bot",
        )
    )