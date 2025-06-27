#!/usr/bin/env python3
"""
Script para debug en tiempo real de llamadas entrantes
"""

import asyncio
from dotenv import load_dotenv
from livekit import api
import os
import json

load_dotenv(dotenv_path=".env.local")

async def debug_incoming_calls():
    """Debug detallado de llamadas entrantes"""
    
    lk_api = api.LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET")
    )
    
    print("🔍 DEBUG LLAMADAS ENTRANTES - TIEMPO REAL")
    print("📞 LLAMA AHORA AL +18632190153")
    print("=" * 60)
    
    rooms_anteriores = set()
    
    for i in range(120):  # Monitorear por 2 minutos
        try:
            # Listar rooms cada segundo
            rooms = await lk_api.room.list_rooms(api.ListRoomsRequest())
            rooms_actuales = {room.name for room in rooms.rooms}
            
            # Detectar cambios
            nuevos_rooms = rooms_actuales - rooms_anteriores
            rooms_eliminados = rooms_anteriores - rooms_actuales
            
            if nuevos_rooms:
                for room_name in nuevos_rooms:
                    print(f"\n🆕 NUEVO ROOM: {room_name}")
                    print(f"   ⏰ Timestamp: {i}s")
                    
                    # Obtener detalles completos
                    for room in rooms.rooms:
                        if room.name == room_name:
                            print(f"   📋 Metadata: {room.metadata}")
                            print(f"   👥 Participantes: {room.num_participants}")
                            print(f"   🕐 Creado: {room.creation_time}")
                            
                            # Participantes detallados cada 2 segundos
                            for j in range(10):
                                await asyncio.sleep(2)
                                participants = await lk_api.room.list_participants(
                                    api.ListParticipantsRequest(room=room.name)
                                )
                                
                                print(f"   📊 T+{j*2}s - Participantes: {len(participants.participants)}")
                                
                                for p in participants.participants:
                                    print(f"      👤 {p.identity}")
                                    print(f"         Estado: {p.state}")
                                    print(f"         Tracks: {len(p.tracks)}")
                                    print(f"         Metadata: {p.metadata}")
                                
                                if len(participants.participants) >= 2:
                                    print("   ✅ ¡AMBOS PARTICIPANTES CONECTADOS!")
                                    break
            
            if rooms_eliminados:
                for room_name in rooms_eliminados:
                    print(f"\n🗑️  ROOM ELIMINADO: {room_name}")
            
            # Status cada 15 segundos
            if i % 15 == 0 and i > 0:
                print(f"\n⏱️  {i}s - Rooms activos: {len(rooms_actuales)}")
                if len(rooms_actuales) > 0:
                    for room_name in rooms_actuales:
                        participants = await lk_api.room.list_participants(
                            api.ListParticipantsRequest(room=room_name)
                        )
                        print(f"   🏠 {room_name}: {len(participants.participants)} participantes")
            
            rooms_anteriores = rooms_actuales
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            await asyncio.sleep(1)
    
    print("\n✅ Debug completado")

if __name__ == "__main__":
    asyncio.run(debug_incoming_calls())