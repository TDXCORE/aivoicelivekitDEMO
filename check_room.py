#!/usr/bin/env python3
"""
Script para verificar el estado del room y participantes
"""

import asyncio
from dotenv import load_dotenv
from livekit import api
import os

load_dotenv(dotenv_path=".env.local")

async def check_room_status():
    """Verificar estado del room call-573153041548"""
    
    lk_api = api.LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET")
    )
    
    try:
        # Listar rooms activos
        rooms = await lk_api.room.list_rooms(api.ListRoomsRequest())
        
        print(f"🏠 Total rooms activos: {len(rooms.rooms)}")
        
        for room in rooms.rooms:
            print(f"\n📋 Room: {room.name}")
            print(f"   Participantes: {room.num_participants}")
            print(f"   Creado: {room.creation_time}")
            print(f"   Estado: {'🟢 Activo' if room.num_participants > 0 else '🔴 Sin participantes'}")
            
            # Si es nuestro room de prueba, obtener más detalles
            if room.name == "call-573153041548":
                participants = await lk_api.room.list_participants(
                    api.ListParticipantsRequest(room=room.name)
                )
                
                print(f"   🎯 ROOM DE PRUEBA ENCONTRADO:")
                print(f"   📞 Participantes detallados:")
                
                for p in participants.participants:
                    print(f"      - {p.identity} ({p.state})")
                    print(f"        Joined: {p.joined_at}")
                    print(f"        Tracks: {len(p.tracks)}")
        
    except Exception as e:
        print(f"❌ Error verificando rooms: {e}")

if __name__ == "__main__":
    asyncio.run(check_room_status())