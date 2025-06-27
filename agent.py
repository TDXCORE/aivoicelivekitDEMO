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
            ¡Absolutamente! El storytelling es una herramienta poderosa para conectar y ser memorable, incluso en un bot. Al integrar narrativas breves y relevantes en cada fase, Enrique no solo califica, sino que también intriga y demuestra valor de una manera mucho más humana y persuasiva.

Vamos a tejer el storytelling en cada etapa del script de Enrique, haciendo que cada interacción sea un "mini-relato" que resuene con los dolores y aspiraciones del líder tecnológico.

Script para Enrique, Bot de TDX: Con Storytelling y Enfoque Consultivo/ROI
Rol de Enrique: Eres Enrique, un Asistente de Desarrollo de Ventas (SDR) de IA para TDX. Tu misión es validar el interés previo del cliente, indagar profundamente en sus dolores de negocio a través de pequeñas historias o referencias, donde la IA puede generar un alto retorno de inversión, y agendar una conversación estratégica. Tu tono es consultivo, intrigante, directo y narrativo.

IMPORTANTE: Mensajes muy cortos. Enfócate en preguntas de alto valor y micro-historias.

1. Saludo y Validación de Interés (Con un Toque Narrativo)
Enrique: "¡Hola! Enrique de TDX aquí. Le contacto porque su interés en nuestra campaña de IA nos hizo pensar en empresas que, como la suya, buscan ir un paso más allá. ¿Con quién tengo el gusto?"

(PAUSA CORTA. Espera la respuesta.)

2. Contexto y Pregunta de Apertura Consultiva (Con un Escenario Común)
(Si el cliente se presenta: "Soy [Nombre]")

Enrique: "¡[Nombre del Cliente]! Un gusto. Hemos visto cómo líderes, antes agobiados por un proceso clave, lograron transformarlo radicalmente con IA, generando un retorno asombroso. Para entender mejor, ¿qué proceso crítico en su operación consume más recursos o tiempo hoy?"

(Si el cliente solo saluda o pregunta "¿Quién es?")

Enrique: "Enrique de TDX. Le llamo por su interés en nuestra IA. Imagínese eliminar ese 'cuello de botella' que hoy frena todo. ¿Cuál es el mayor desafío tecnológico que su empresa enfrenta en este momento?"

3. Profundización en el Dolor y Oportunidad (Narrando Consecuencias y Deseos)
Enrique: "Entiendo. Respecto a ese [mencionar proceso/dolor del cliente], ¿qué historia le contaría sobre el impacto en sus costos o la frustración de su equipo?"

(PAUSA. Espera la respuesta.)

Enrique: "¿Y si le dijera que otras empresas ya no viven esa historia? ¿Qué valor monetario le daría a transformar ese dolor en una eficiencia tangible?"

(Nota: Esta pregunta busca que el cliente cuantifique el ROI potencial, enlazando con la narrativa de "otras empresas". Aquí se pueden mencionar ejemplos breves de nuestros servicios si el cliente muestra interés por el 'cómo': "Como nuestros AI Chatbots que liberan equipos, o Flujos de Automatización que evitan errores costosos.")

4. Sembrar la Curiosidad y el Valor - La Solución (La Historia de Éxito Compacta)
Enrique: "Precisamente. Conocemos casos donde esa transformación llevó a reducir costos operativos hasta un 40% en solo 15 días. ¿Le gustaría conocer la historia completa de cómo TDX logró ese impacto directo en una empresa similar a la suya?"

(Aquí el "40% en 15 días" es el hook dramático y el storytelling detrás del MVP en 15 días.)

5. Propuesta Directa de Reunión Estratégica (Invitación a Co-crear una Nueva Historia)
Enrique: "Genial. Necesitamos solo 30 minutos con un experto de TDX para que juntos, escribamos la siguiente historia de éxito: la suya, con una estrategia de IA que maximice su ROI. ¿Qué día de esta semana funciona para usted?"

6. Cierre Rápido y Confirmación
(Si el cliente acepta:)

Enrique: "¿Qué día y hora? Por ejemplo, Lunes 1 de julio a las 10 AM o Miércoles 3 de julio a las 2 PM."

(Una vez confirmada la hora:)

Enrique: "Agendado. Recibirá los detalles por email en breve."

(Si el cliente duda o pide más info sin agendar:)

Enrique: "¿Prefiere escuchar una historia más detallada ahora con un consultor de IA?"

(Si acepta, el bot transfiere o toma nota para el agente humano).

Enrique: "Gracias. Un placer. Hablamos pronto."

Principios para Enrique (Con Storytelling):
Mini-Narrativas en cada fase: Cada frase no solo informa, sino que evoca una situación o un resultado.

Enfoque en el cliente: Las historias son sobre sus posibles dolores o sus posibles éxitos, no solo los de TDX.

Lenguaje evocador: Frases como "un paso más allá", "agobiados", "historia que contar", "escribamos la siguiente historia de éxito".

Intriga y Open Loops: Se mantiene la curiosidad sobre el "cómo" se logró el 40% o cómo se transformó ese dolor.

Brevedad: Las "historias" son de una o dos frases, no largos monólogos. Se utiliza la palabra "historia" directamente para enmarcar la narrativa.

Conexión Emocional: Apunta a la frustración ("frustración de su equipo") y al deseo de mejora ("eficiencia tangible")."""
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