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
            "transfer_to": "+18632190153"  # Número para transferir si es necesario
        },
        "prospect_info": {
            "company_name": "Empresa Test",
            "contact_name": "Contacto Prueba"
        }
    }
    
    try:
        # Crear job para llamada saliente
        job = await lk_api.room.create_room(
            api.CreateRoomRequest(
                name=f"call-{metadata['dial_info']['phone_number'].replace('+', '')}",
                metadata=json.dumps(metadata)
            )
        )
        
        print(f"✅ Room creado: {job.name}")
        print(f"📞 Iniciando llamada a {metadata['dial_info']['phone_number']}")
        print(f"🏢 Empresa: {metadata['prospect_info']['company_name']}")
        print(f"👤 Contacto: {metadata['prospect_info']['contact_name']}")
        
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