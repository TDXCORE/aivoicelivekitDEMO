#!/usr/bin/env python3
"""
Script para crear llamada con metadata completa
"""

import asyncio
import json
import os
from dotenv import load_dotenv
from livekit import api

load_dotenv(dotenv_path=".env.local")

async def create_call_with_metadata():
    """Crear room con metadata completa para activar worker"""
    
    lk_api = api.LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET")
    )
    
    # Usar timestamp para room único
    import time
    timestamp = str(int(time.time()))
    room_name = f"call-57315304154{timestamp[-1]}"
    
    # Metadata para el bot
    metadata = {
        "dial_info": {
            "phone_number": "+573153041548",
            "transfer_to": "+18632190153"
        },
        "prospect_info": {
            "company_name": "Empresa Test Colombia",
            "contact_name": "Juan Prueba"
        }
    }
    
    try:
        # Crear room con metadata completa
        room = await lk_api.room.create_room(
            api.CreateRoomRequest(
                name=room_name,
                metadata=json.dumps(metadata)
            )
        )
        
        print(f"✅ Room creado: {room.name}")
        print(f"📋 Metadata: {json.dumps(metadata, indent=2)}")
        
        # Esperar un momento para que el worker procese
        await asyncio.sleep(5)
        
        # Verificar si hay participantes
        participants = await lk_api.room.list_participants(
            api.ListParticipantsRequest(room=room.name)
        )
        
        print(f"\n📊 Estado después de 5 segundos:")
        print(f"   Participantes: {len(participants.participants)}")
        
        if participants.participants:
            for p in participants.participants:
                print(f"   - {p.identity} ({p.state})")
        else:
            print("   🔴 No hay participantes aún")
            print("   💡 El worker debería procesar este job automáticamente")
        
        return room.name
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(create_call_with_metadata())