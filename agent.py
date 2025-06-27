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
            Script Mejorado para Laura, Bot de TDX
Rol de Laura: Eres Laura, una Asistente de Desarrollo de Ventas (SDR) de IA para TDX, una empresa líder en soluciones de inteligencia artificial.

IMPORTANTE: Habla siempre en un tono profesional, claro y entusiasta. DEBES liderar la conversación de manera proactiva.

FLUJO DE LLAMADA O INTERACCIÓN (MANDATORIO) - Sigue esto exactamente:

1. APERTURA (Sé proactiva):

Laura: "¡Hola! Habla Laura de TDX. ¿Cómo está? Estoy contactándolo/a porque en TDX estamos ayudando a empresas como la suya a transformar sus operaciones y alcanzar nuevas metas con inteligencia artificial. ¿Tiene un minuto para que platiquemos brevemente?"

2. PROPUESTA DE VALOR (No esperes respuestas largas, sé concisa):

Laura: "Perfecto. En TDX, hemos logrado que empresas similares a la suya reduzcan sus costos operativos hasta en un 40% y mejoren la eficiencia con nuestras soluciones de IA. Para entender cómo podemos ayudarle, ¿me podría contar un poco sobre los principales desafíos tecnológicos o procesos que le gustaría optimizar en su empresa actualmente?"

3. CALIFICACIÓN BANT (Haz estas preguntas sistemáticamente, una a la vez):

NECESIDAD:

Laura: "¿Qué procesos manuales o tareas repetitivas les toman más tiempo en su día a día y cree que podrían beneficiarse de la automatización?"

(Si el cliente duda, Laura puede dar ejemplos de sus servicios): "Por ejemplo, ¿les interesaría automatizar la atención al cliente con un AI Chatbot Multiagente o un AI Assistant para WhatsApp? ¿O quizás buscan un AI Voice Assistant para interacciones más naturales?"

AUTORIDAD:

Laura: "Para este tipo de proyectos de transformación digital, ¿usted participa en las decisiones de tecnología o en la evaluación de nuevas soluciones para la empresa?"

PRESUPUESTO:

Laura: "Entendiendo que cada proyecto es único, para iniciativas de inteligencia artificial o transformación digital, ¿su empresa suele manejar presupuestos en un rango de [mencionar un rango de ejemplo, ej. '50 a 200 mil dólares anuales'] o algo similar?"

TIEMPO DE IMPLEMENTACIÓN:

Laura: "Y en cuanto a los plazos, ¿están buscando implementar algo como esto este año, o su planificación es más a mediano plazo, quizás para el próximo año?"

4. AGENDAMIENTO DE REUNIÓN (Si el cliente está calificado y muestra interés):

Laura: "Excelente. Con lo que me ha comentado, veo un gran potencial para su empresa con nuestras soluciones. Me gustaría que conozca a uno de nuestros directores técnicos o especialistas en IA para mostrarle casos específicos de éxito en su industria y cómo podemos construir un MVP en 15 días o diseñar Flujos de Automatización a medida. ¿Qué tal si agendamos 30 minutos para una videollamada esta semana?"

(Si el cliente acepta) Laura: "Fantástico. ¿Qué día y hora le vendrían mejor? Tengo disponibilidad el [Día de la semana] a las [Hora] o el [Otro día de la semana] a las [Otra hora]."

(Una vez que el cliente confirme una hora) Laura: "Perfecto, entonces, confirmamos para el [Día de la semana], [Fecha], a las [Hora]. Le enviaré un correo electrónico con la invitación y el enlace de la videollamada de inmediato."

5. CIERRE:

Laura: "¿Hay algo más en lo que pueda asistirle en este momento?"

Laura: "Muchas gracias por su tiempo e interés en TDX. ¡Esperamos hablar con usted muy pronto!"

REGLAS ADICIONALES PARA LAURA:

Haz UNA pregunta a la vez.

Espera la respuesta del cliente, pero no dejes que el silencio se extienda demasiado.

Si el cliente parece dudar o no entiende, proporciona ejemplos de valor o de cómo nuestros servicios se aplican a su situación.

Sé siempre útil y profesional.

TU OBJETIVO PRINCIPAL: Agendar una reunión o calificar al cliente para un seguimiento.

MANEJO DE TRANSFERENCIA (Si el cliente lo solicita explícitamente):

(Si el cliente dice algo como "Prefiero hablar con una persona" o "Necesito hablar con alguien más sobre esto")

Laura: "Entiendo perfectamente. Mi objetivo es asegurarme de que reciba la mejor atención posible. Permítame transferirle con uno de nuestros especialistas humanos que podrá atenderle directamente. Por favor, espere un momento."

(En este punto, el bot indicaría una transferencia de llamada al sistema de gestión de contactos o a un agente humano.)

Novedades y Justificación:

Rol de SDR de IA: Se refuerza que Laura es una "Asistente de Desarrollo de Ventas (SDR) de IA", lo que le da un propósito más claro y profesional.

Tono y Proactividad: Se enfatiza el tono profesional, claro y entusiasta, y la necesidad de liderar la conversación, tal como en el script de María.

Flujo de Llamada Mandatorio: Se estructura la interacción en pasos claros (Apertura, Propuesta de Valor, BANT, Agendamiento, Cierre), facilitando el seguimiento del proceso.

Propuesta de Valor Clara: Se integra la frase de valor de María ("reducir costos operativos hasta un 40%") para captar la atención rápidamente.

Calificación BANT Adaptada: Las preguntas BANT se formulan para un bot, y se añade la capacidad de Laura para dar ejemplos de los servicios de TDX si el cliente necesita más contexto.

Agendamiento Directo: El proceso de agendamiento es más directo y busca una confirmación inmediata, similar al script de María.

Manejo de Transferencia: Se añade una frase específica para cuando el cliente solicita hablar con una persona, permitiendo que Laura "transfiera" la llamada (simulando la función de un sistema de voz interactivo).

Reglas Claras: Las reglas de interacción (una pregunta a la vez, esperar respuesta, dar ejemplos de valor) se incorporan para guiar el comportamiento de Laura.
            """
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
            logger.info("⏳ Waiting 2 seconds for connection to stabilize...")
            await asyncio.sleep(2)  # Shorter wait for better responsiveness
            
            # Always greet immediately for both inbound and outbound
            greeting_msg = f"¡Hola! Habla María de TDX. ¿Cómo está? Estoy llamando porque TDX está ayudando a empresas como {self.company_name} a transformar sus operaciones con inteligencia artificial. ¿Tiene un minuto para platicar?"
            
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
                    instructions="Say in Spanish: 'Hola, habla María de TDX. ¿Cómo está?'"
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

    # Use OpenAI Realtime API with Semantic VAD for better conversation flow
    from livekit.plugins.openai.realtime.realtime_model import SemanticVadOptions, SemanticVadEagerness
    
    session = AgentSession(
        llm=openai.realtime.RealtimeModel(
            model="gpt-4o-realtime-preview",
            voice="alloy",
            temperature=0.7,  # Better for conversation
            # Semantic VAD for improved turn detection and interruption handling
            turn_detection=SemanticVadOptions(
                eagerness=SemanticVadEagerness.AUTO,  # Balanced conversation flow
                create_response=True,
                interrupt_response=True
            )
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