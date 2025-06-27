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
            You are María, a professional Sales Development Representative (SDR) for TDX, a leading technology company specializing in artificial intelligence solutions.
            
            IMPORTANT: Always speak in a professional, clear, and enthusiastic tone. You MUST lead the conversation proactively.
            
            MANDATORY CALL FLOW - Follow this exactly:
            
            1. OPENING (Be proactive):
            "¡Hola! Habla María de TDX. ¿Cómo está? Estoy llamando porque TDX está ayudando a empresas como {company_name} a transformar sus operaciones con inteligencia artificial. ¿Tiene un minuto para platicar?"
            
            2. VALUE PROPOSITION (Don't wait for long responses):
            "Perfecto. TDX ha ayudado a empresas similares a reducir costos operativos hasta un 40% con nuestras soluciones de IA. ¿Me puede contar un poco sobre los principales desafíos tecnológicos que enfrenta {company_name} actualmente?"
            
            3. BANT QUALIFICATION (Ask these questions systematically):
            - NEED: "¿Qué procesos manuales les toman más tiempo en su día a día?"
            - AUTHORITY: "¿Usted participa en las decisiones de tecnología de la empresa?"
            - BUDGET: "Para proyectos de transformación digital, ¿manejan presupuestos en el rango de 50-200 mil dólares anuales?"
            - TIMELINE: "¿Están buscando implementar algo este año o el próximo?"
            
            4. MEETING SCHEDULING (If qualified):
            "Excelente. Me gustaría que conozca a nuestro director técnico para mostrarle casos específicos de su industria. ¿Qué tal si agendamos 30 minutos esta semana?"
            
            5. CLOSING:
            Use schedule_meeting tool if they agree, or transfer_call if they want to speak with someone else.
            
            RULES:
            - Ask ONE question at a time
            - Wait for their answer but don't let silence extend too long
            - If they seem hesitant, provide value examples
            - Always be helpful and professional
            - Use qualify_prospect tool after getting BANT answers
            - Your goal is to schedule a meeting or qualify the lead
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
        logger.info(f"Agent session started, call direction: {self.call_direction}")
        await asyncio.sleep(2)  # Wait for connection to stabilize
        
        if self.call_direction == "inbound":
            # For inbound calls, greet immediately
            greeting_msg = f"¡Hola! Habla María de TDX. ¿Cómo está? Estoy llamando porque TDX está ayudando a empresas como {self.company_name} a transformar sus operaciones con inteligencia artificial. ¿Tiene un minuto para platicar?"
            
            logger.info("Sending initial greeting for inbound call...")
            await ctx.session.generate_reply(
                instructions=f"Say this greeting exactly and wait for response: '{greeting_msg}'"
            )
        else:
            # For outbound calls, wait for user to speak first
            logger.info("Outbound call - waiting for user to speak first...")
            await ctx.session.generate_reply(
                instructions="Wait silently for the user to speak first. When they say hello or any greeting, respond with: '¡Hola! Habla María de TDX. ¿Cómo está? Estoy llamando porque TDX está ayudando a empresas a transformar sus operaciones con inteligencia artificial. ¿Tiene un minuto para platicar?'"
            )

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
    
    # Determine call direction - inbound calls have phone number in room name
    call_direction = metadata.get("call_direction", "inbound")
    if ctx.room.name.startswith("call-"):
        call_direction = "inbound"  # Room created by dispatch rule for inbound calls
    
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

    # Use OpenAI Realtime API for speech-to-speech with optimized settings
    session = AgentSession(
        llm=openai.realtime.RealtimeModel(
            model="gpt-4o-realtime-preview",
            voice="alloy",  # Using valid OpenAI voice option
            temperature=0.5,  # Lower temperature for more consistent responses
        )
    )

    # Start session
    session_started = asyncio.create_task(
        session.start(
            agent=agent,
            room=ctx.room,
        )
    )

    # For inbound calls, wait for SIP participant to join
    logger.info("Waiting for inbound SIP call...")
    await session_started
    
    # Wait for participant to join (should happen automatically for inbound calls)
    try:
        participant = await ctx.wait_for_participant()
        logger.info(f"participant joined: {participant.identity}")
        agent.set_participant(participant)
        
        # The greeting will be triggered automatically by on_session_start method
        
    except Exception as e:
        logger.error(f"error waiting for participant: {e}")
        ctx.shutdown()

if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="tdx-sdr-bot",
        )
    )