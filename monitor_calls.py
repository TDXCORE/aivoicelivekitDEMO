#!/usr/bin/env python3
"""
Script para monitorear llamadas entrantes en tiempo real
"""

import asyncio
from dotenv import load_dotenv
from livekit import api
import os
import time

load_dotenv(dotenv_path=".env.local")

async def monitor_incoming_calls():
    """Monitorear llamadas entrantes en tiempo real"""
    
    lk_api = api.LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET")
    )
    
    print("🔍 MONITOREANDO LLAMADAS ENTRANTES...")
    print("📞 Llama ahora al +18632190153")
    print("=" * 50)
    
    rooms_anteriores = set()
    
    for i in range(60):  # Monitorear por 60 segundos
        try:
            # Listar rooms cada segundo
            rooms = await lk_api.room.list_rooms(api.ListRoomsRequest())
            rooms_actuales = {room.name for room in rooms.rooms}
            
            # Detectar nuevos rooms
            nuevos_rooms = rooms_actuales - rooms_anteriores
            
            if nuevos_rooms:
                for room_name in nuevos_rooms:
                    print(f"\n🆕 NUEVO ROOM DETECTADO: {room_name}")
                    
                    # Obtener detalles del room
                    for room in rooms.rooms:
                        if room.name in nuevos_rooms:
                            print(f"   📋 Metadata: {room.metadata}")
                            print(f"   👥 Participantes: {room.num_participants}")
                            
                            # Obtener participantes detallados
                            participants = await lk_api.room.list_participants(
                                api.ListParticipantsRequest(room=room.name)
                            )
                            
                            for p in participants.participants:
                                print(f"   👤 Participante: {p.identity} ({p.state})")
                                print(f"      📞 Joined: {p.joined_at}")
                                print(f"      🎵 Tracks: {len(p.tracks)}")
            
            # Mostrar progreso cada 10 segundos
            if i % 10 == 0 and i > 0:
                print(f"⏱️  Monitoreando... {i}s transcurridos")
                print(f"   🏠 Rooms activos: {len(rooms_actuales)}")
            
            rooms_anteriores = rooms_actuales
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"❌ Error monitoreando: {e}")
            await asyncio.sleep(1)
    
    print("\n✅ Monitoreo completado")

if __name__ == "__main__":
    asyncio.run(monitor_incoming_calls())