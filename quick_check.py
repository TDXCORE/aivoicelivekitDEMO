#!/usr/bin/env python3
"""
Verificación rápida del estado actual
"""

import asyncio
from dotenv import load_dotenv
from livekit import api
import os

load_dotenv(dotenv_path=".env.local")

async def quick_status():
    """Verificación rápida"""
    
    lk_api = api.LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET")
    )
    
    try:
        print("🔍 ESTADO ACTUAL:")
        
        # Listar rooms
        rooms = await lk_api.room.list_rooms(api.ListRoomsRequest())
        print(f"🏠 Rooms activos: {len(rooms.rooms)}")
        
        for room in rooms.rooms:
            print(f"\n📋 Room: {room.name}")
            print(f"   👥 Participantes: {room.num_participants}")
            
            if room.num_participants > 0:
                participants = await lk_api.room.list_participants(
                    api.ListParticipantsRequest(room=room.name)
                )
                
                for p in participants.participants:
                    print(f"   👤 {p.identity} - Estado: {p.state}")
                    print(f"      🎵 Tracks: {len(p.tracks)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(quick_status())