#!/usr/bin/env python3
"""
Script para probar llamadas salientes del TDX SDR Bot
"""

import asyncio
import json
import os
from dotenv import load_dotenv
from livekit import api

# Load environment variables
load_dotenv(dotenv_path=".env.local")

async def make_outbound_call():
    """Crear una llamada saliente de prueba"""
    
    # LiveKit API client
    lk_api = api.LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET")
    )
    
    # Metadata para el bot
    metadata = {
        "dial_info": {
            "phone_number": "+573153041548",
            "transfer_to": "+18632190153"
        },
        "prospect_info": {
            "company_name": "Empresa Test Colombia",
            "contact_name": "Contacto Prueba"
        }
    }
    
    try:
        # Crear room que coincida con el patrón de dispatch rule
        # Usar patrón: call-{participant.identity}_+number_randomID
        import time
        import random
        import string
        random_id = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        room_name = f"call-sip_{metadata['dial_info']['phone_number'].replace('+', '')}_{metadata['dial_info']['phone_number']}_{random_id}"
        
        job = await lk_api.room.create_room(
            api.CreateRoomRequest(
                name=room_name,
                metadata=json.dumps(metadata)
            )
        )
        
        print(f"✅ Room creado: {job.name}")
        
        # HACER LA LLAMADA REAL usando SIP - FORMATO CORRECTO
        sip_participant = await lk_api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                sip_trunk_id=os.getenv("SIP_OUTBOUND_TRUNK_ID"),
                sip_call_to=metadata['dial_info']['phone_number'],  # Sin tel: prefix
                room_name=job.name,
                participant_identity=f"sip_{metadata['dial_info']['phone_number'].replace('+', '')}"
            )
        )
        
        print(f"📞 Llamada SIP iniciada: {sip_participant.participant_identity}")
        print(f"📞 Marcando a {metadata['dial_info']['phone_number']}")
        print(f"🏢 Empresa: {metadata['prospect_info']['company_name']}")
        print(f"👤 Contacto: {metadata['prospect_info']['contact_name']}")
        
        print(f"🤖 Room creado con patrón para auto-dispatch...")
        print(f"   El dispatch rule debería detectar automáticamente este room")
        
        return job.name
        
    except Exception as e:
        print(f"❌ Error creando llamada: {e}")
        return None

if __name__ == "__main__":
    room_name = asyncio.run(make_outbound_call())
    if room_name:
        print(f"\n🎯 Room creado exitosamente: {room_name}")
        print("El bot debería iniciar la llamada automáticamente.")
    else:
        print("\n❌ No se pudo crear la llamada.")