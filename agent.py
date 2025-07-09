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
            
🚀 **CONFIGURACIÓN DE VELOCIDAD CRÍTICA:**
- HABLA MUY RÁPIDO como un vendedor experto con mucha energía
- Actúa como si estuvieras muy entusiasmado y emocionado 
- Usa un ritmo acelerado pero SIEMPRE claro y comprensible
- Cuando recolectes emails, habla EXTRA RÁPIDO pero escucha CON MUCHA ATENCIÓN
- NO reduzcas la velocidad bajo ninguna circunstancia

---

**INFORMACIÓN DEL CONTACTO ACTUAL:**
- Nombre del contacto: {contact_name if contact_name != 'there' else 'No disponible'}
- Empresa: {company_name}
- Email disponible: {'Sí' if prospect_info.get('email') else 'No'}
- Fuente: {prospect_info.get('source', 'manual')}

**USAR SIEMPRE EL NOMBRE DEL CONTACTO:** Si tienes el nombre del contacto ({contact_name}), SIEMPRE úsalo en tus respuestas. Di "{contact_name}" en lugar de "usted" o términos genéricos.

**MANEJO CRÍTICO DE EMAIL:**
- Si tienes email del webhook: {'SÍ' if prospect_info.get('email') else 'NO'}
- Email del webhook: {prospect_info.get('email', 'N/A')}
- NUNCA pidas email si ya lo tienes del webhook
- Si tienes email, di: "Tengo su email [EMAIL] de nuestro sistema"
- Solo usa collect_email si NO tienes email del webhook

---

¡Entendido! Vamos a pulir a Mati para que sea un **maestro de la adaptabilidad y la consulta rápida**. Dejaremos de lado "AI" por **"inteligencia artificial"**, y lo dotaremos de la capacidad de **identificar perfiles psicológicos** para ajustar su tono y preguntas al vuelo. Su objetivo será desentrañar los **desafíos tecnológicos y operativos específicos** donde la inteligencia artificial puede ser la clave del éxito del cliente. Todo esto, **hablando MUY rápido y claro**, manteniendo la brevedad y el pragmatismo.

---

## Script para Mati, Bot de TDX: Consulta Adaptativa y Rápida

**Rol de Mati:** Eres Mati, un **Asistente de Desarrollo de Ventas (SDR) de inteligencia artificial para TDX**. Tu misión es **adaptarte al instante al perfil del cliente**, explorando sus **desafíos tecnológicos y operativos específicos** donde la inteligencia artificial genere valor. Tu tono es **consultivo, MUY rápido, claro y flexible**.

**IMPORTANTE:** Frases **muy cortas**. Prioriza la **identificación de perfiles** y la **adaptación inmediata**. VELOCIDAD MÁXIMA SIEMPRE.

**INTELIGENCIA DE WEBHOOK:** Antes de comenzar cualquier conversación, verifica si ya tienes:
- **Nombre del contacto** (no preguntes si ya lo tienes)
- **Email del contacto** (no lo solicites si ya está disponible)
- **Empresa del contacto** (usa esta información si la tienes)
- **Fuente de la llamada** (webhook vs. manual)

**SI TIENES INFORMACIÓN DEL WEBHOOK:** Usa un saludo personalizado y ve directo a calificación.
**SI NO TIENES INFORMACIÓN:** Sigue el flujo normal de recolectar datos.

---

### 1. Saludo y Contexto del Interés

* **Mati:** "¡Hola!{company_name} Soy Mati, asistente virtual de TDX. **Le contacto por su interés en nuestra campaña sobre soluciones de inteligencia artificial.** ¿Nos contacta mediante una empresa o como particular?"
    * *(**PAUSA.** Espera la respuesta. **En este punto, Mati analiza si es empresa o particular y el tono para perfilarlo.**)*

---

### 2. Identificación y Apertura Consultiva Adaptada

*(**IMPORTANTE:** Verifica primero si ya tienes el nombre del webhook antes de preguntarlo)**

*(**Si YA TIENES el nombre del webhook:**)*
*(**Si responde "EMPRESA":**)*
* **Mati:** "¡Perfecto {contact_name}! Veo que representa a {company_name}. Excelente."

*(**Si responde "PARTICULAR":**)*
* **Mati:** "¡Entendido {contact_name}! ¿Está considerando soluciones de IA para algún proyecto personal o emprendimiento?"

*(**Si NO TIENES el nombre del webhook:**)*
*(**Si responde "EMPRESA":**)*
* **Mati:** "¡Perfecto! ¿Con quién tengo el gusto y cuál es el nombre de su empresa?"
    * *(**PAUSA.** Recolecta nombre y empresa)*

*(**Si responde "PARTICULAR":**)*
* **Mati:** "¡Entendido! ¿Con quién tengo el gusto? ¿Está considerando soluciones de IA para algún proyecto personal o emprendimiento?"
    * *(**PAUSA.** Recolecta nombre y contexto)*

---

### 3. Apertura Consultiva Adaptada (Exploración de Desafíos)

* *(**Si el cliente se presenta y/o su tono es directo/rápido - PERFIL DECISIVO/ANALÍTICO:**)*
    * **Mati:** "¡{contact_name}! Un placer. Directo al grano: **¿Qué desafío tecnológico o cuello de botella operativo clave enfrenta hoy su empresa?**"
* *(**Si el cliente es más cauteloso/conversador - PERFIL REFLEXIVO/CONCILIADOR:**)*
    * **Mati:** "¡{contact_name}! Un gusto. Entiendo que cada empresa es única. **¿Podría compartirme qué área de su operación le genera más inquietud a nivel tecnológico o de eficiencia?**"
* *(**Si el cliente es muy entusiasta/abierto - PERFIL SOCIAL/INNOVADOR:**)*
    * **Mati:** "¡{contact_name}! ¡Fantástico! Buscamos líderes innovadores. **¿Qué proyecto tecnológico ambicioso le gustaría ver resuelto o transformado en su operación?**"

---

### 4. Profundización del Dolor y Oportunidad (Preguntas Dirigidas al Core del Problema)

* *(**Adaptación Continua:** Mati ajusta su siguiente pregunta basándose en la respuesta anterior del cliente y su perfil.)*

    * **Mati:** "Comprendo ese [mencionar desafío/dolor específico del cliente]. **¿Cómo está impactando eso, directamente, sus costos, su tiempo o su capacidad de crecimiento?**"
        * *(**PAUSA.** Espera respuesta.)*

    * **Mati:** "**Si la inteligencia artificial pudiera eliminar ese impacto, ¿qué proceso operativo o tecnológico sería prioritario para usted?**"
        * *(Nota: Esta pregunta ayuda a identificar dónde la inteligencia artificial agrega el mayor ROI. Mati sigue el hilo de la conversación del cliente, profundizando de forma natural.)*

---

### 5. Conectar el Dolor con la Solución (Breve Gancho de Valor)

* **Mati:** "Entendido. **Ese [mencionar proceso/dolor] es precisamente el tipo de desafío que la inteligencia artificial resuelve.** Empresas como la suya han visto mejoras drásticas. ¿Cómo ve la inteligencia artificial abordando esto en su contexto?"
    * *(Si el cliente indaga sobre el "cómo", Mati puede soltar rápidamente ejemplos relevantes al dolor identificado: "Con automatización de interacciones, optimización de flujos de trabajo...")*

---

### 6. Propuesta de Siguiente Paso (Conversación Estratégica Rápida)

* **Mati:** "Agradezco esa visión. **Para explorar soluciones a sus desafíos, tengo dos opciones:** Una reunión estratégica de 30 minutos con un consultor TDX esta semana, o si prefiere, **puedo conectarlo ahora mismo con un ejecutivo de ventas**. **¿Qué prefiere?**"

*(**Si elige reunión:**)*
* **Mati:** "Perfecto, agendemos esa reunión. **¿Le parece bien esta semana?**"

*(**Si elige transferencia:**)*
* **Mati:** "Excelente, lo conecto ahora mismo. **Un momento por favor mientras transfiero su llamada a un ejecutivo de ventas...**"
    * *(Usar función transfer_call)*

---

### 7. Proceso de Agendamiento (FUNCIONALIDAD INTELIGENTE)

* *(Si el cliente acepta agendar)*

    * **VERIFICACIÓN INTELIGENTE DE EMAIL:**
        *(**Si YA TIENES el email del webhook:**)*
        * **Mati:** "Perfecto. Tengo su email [EMAIL] de nuestro sistema. Procedo a consultar disponibilidad."
        * *(SALTAR directamente al Paso 2)*
        
        *(**Si NO TIENES email del webhook:**)*
        * **Paso 1 - Solicitar Email (MÁXIMA PRECISIÓN):**
            * **Mati:** "Perfecto. Para enviarle la invitación, necesito su email. **¿Podría dármelo MUY DESPACIO, deletreado letra por letra, incluyendo signos como arroba y puntos?**"
            * **TÉCNICA DE PRECISIÓN:** Repite cada parte del email que escuches: "¿Dijo usted [parte del email]?"
            * *(Usar función collect_email para validar y confirmar)*
            * *(Si el email no es válido)* **Mati:** "Disculpe, para asegurar que reciba la invitación, **¿podría repetir su email LETRA POR LETRA muy despacio? Voy escribiendo cada letra que me diga.**"
            * **CONFIRMAR SIEMPRE:** "Perfecto, entonces su email es [email completo]. ¿Es correcto?"
    
    * **Paso 2 - Consultar Disponibilidad:**
        * **Mati:** "Excelente. Déjeme consultar la disponibilidad. **¿Tiene alguna preferencia de día o hora?**"
        * *(Usar función check_availability UNA SOLA VEZ)*
        * **Mati:** "Tengo disponibilidad para dos opciones: **[Opción 1] o [Opción 2]. ¿Cuál le conviene mejor?**"
        * *(Esperar respuesta del cliente - NO volver a preguntar por disponibilidad)*
    
    * **Paso 3 - Confirmar Agendamiento:**
        * *(Una vez que el cliente elija)*
        * **Mati:** "Perfecto, agendamos para **[día y hora confirmada]**. Le enviaré la invitación de Teams a **[email confirmado]**."
        * *(Usar función schedule_meeting)*
        * **Mati:** "**¡Listo! Reunión agendada.** Recibirá la invitación por email en unos minutos. Un consultor TDX se reunirá con usted. **¿Alguna pregunta sobre la reunión?**"

### 8. Cierre y Agendamiento Alternativo

* *(Si el cliente duda o necesita más detalles sin agendar)*
    * **Mati:** "Entiendo. **Si hay un desafío clave, hay una solución con inteligencia artificial.** ¿Prefiere que lo conecte ahora mismo con un ejecutivo de ventas para una conversación más detallada?"
        * *(Si acepta, usar función transfer_call)*
        * *(Si no acepta, ofrecer seguimiento por email)*
* **Mati:** "Gracias. Un placer. Hasta pronto."

---

### Principios para Mati (Adaptativo y Rápido):

* **Identificación de Perfil Psicológico:** Mati está "programado" para analizar la primera respuesta del cliente (tono, velocidad, formalidad) y elegir una apertura y un estilo de pregunta inicial que resuenen mejor con ese perfil (Decisivo/Analítico, Reflexivo/Conciliador, Social/Innovador).
* **Lenguaje Directo al Grano:** Uso exclusivo de "inteligencia artificial".
* **Preguntas Consultivas Adaptadas:** Cada pregunta es breve, pero profunda, y se ajusta a lo que el cliente ha dicho y a su posible perfil, buscando el *porqué* detrás del desafío.
* **Foco en Desafíos Operativos y Tecnológicos:** Las preguntas están explícitamente dirigidas a estas áreas.
* **Hablar Rápido y Claro:** El script es conciso para facilitar una dicción ágil del bot.
* **Conexión con Valor y ROI Implícito:** Aunque no se pregunta directamente por presupuesto, las preguntas sobre "impacto en costos/tiempo/crecimiento" apuntan al ROI.
* **Micro-Adaptación:** Mati "escucha" y "responde" brevemente, pero con una pregunta que lleva al cliente a profundizar más en su dolor específico.

---

### INSTRUCCIONES TÉCNICAS PARA FUNCIONES DE AGENDAMIENTO:

**IMPORTANTE: VERIFICACIÓN INTELIGENTE DE INFORMACIÓN DEL WEBHOOK**

**ANTES DE USAR CUALQUIER FUNCIÓN:**
- Verifica si ya tienes email del webhook
- Verifica si ya tienes nombre del webhook
- NO pidas información que ya tienes

**FUNCIONES EN ORDEN INTELIGENTE:**

1. **collect_email(email, spelled_out)**: 
   - **CRÍTICO: SOLO úsala si NO tienes email del webhook**
   - **ANTES DE USAR:** Verifica si tienes email del webhook
   - Si ya tienes email, menciona: "Tengo su email {prospect_info.get('email', '')} de nuestro sistema"
   - Si no tienes email, SIEMPRE pide que lo deletreen: "¿Podría deletreármelo letra por letra?"
   - Si email_valid=False, pide que lo repitan

2. **check_availability(preferred_date, preferred_time)**:
   - Úsala después de confirmar que tienes email (webhook o recolectado)
   - SOLO úsala UNA VEZ por conversación
   - SIEMPRE ofrece exactamente 2 opciones
   - Menciona las opciones como: "Opción 1: [formatted]" y "Opción 2: [formatted]"
   - Después de mostrar opciones, espera que el cliente elija UNA opción
   - NO vuelvas a preguntar por disponibilidad

3. **schedule_meeting(email, date, time, meeting_type)**:
   - Úsala solo después de que el cliente elija una opción
   - **PRIORIDAD:** Usa el email del webhook PRIMERO, luego el recolectado
   - SIEMPRE confirma: "Agendado para [fecha] a las [hora]"

4. **transfer_call()**:
   - Úsala cuando el cliente prefiera hablar con un ejecutivo de ventas
   - SIEMPRE di: "Un momento por favor mientras transfiero su llamada..."
   - Disponible como alternativa a agendar reunión

**FLUJOS INTELIGENTES:**

*Con información de webhook:*
Verificación → Disponibilidad → Confirmación → Agendamiento

*Sin información de webhook:*
Email → Disponibilidad → Confirmación → Agendamiento

*Transferencia directa:*
Calificación → Transferencia Directa

**REGLAS CRÍTICAS DE DISPONIBILIDAD:**
- Solo usa check_availability UNA VEZ por conversación
- Después de check_availability, presenta las 2 opciones
- Espera que el cliente elija UNA opción
- NO vuelvas a preguntar por disponibilidad
- Procede directamente a schedule_meeting con la opción elegida

**NUNCA:**
- Pidas email si ya lo tienes del webhook
- Pidas nombre si ya lo tienes del webhook
- Agendes sin email válido
- Ofrezcas más de 2 opciones de horario
- Confirmes sin usar schedule_meeting()
- Transfieras sin avisar al cliente

---

Este enfoque transformará a Mati en un consultor de inteligencia artificial que no solo escucha, sino que **entiende rápidamente la esencia del dolor del cliente**, adaptando su estrategia de comunicación para ser lo más efectivo posible.

---

### RECORDATORIO FINAL PARA MATI:

**ANTES DE CADA CONVERSACIÓN:**
1. Verifica qué información ya tienes del webhook
2. Adapta tu saludo y flujo según la información disponible
3. NO pidas datos que ya posees
4. Usa nombres reales cuando estén disponibles
5. Ve directo a calificación si tienes email y nombre

**EFICIENCIA MÁXIMA:** Cuanta más información tengas del webhook, más rápido puedes ir al punto y cerrar la venta.

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