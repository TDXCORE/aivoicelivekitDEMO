#!/usr/bin/env python3
"""
Monitor real-time de llamadas para debugging
"""

import asyncio
from dotenv import load_dotenv
from livekit import api
import os
import time

load_dotenv(dotenv_path=".env.local")

async def monitor_call_lifecycle():
    """Monitor completo del ciclo de vida de llamadas"""
    
    lk_api = api.LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET")
    )
    
    print("🔍 MONITOR EN TIEMPO REAL - TDX SDR BOT")
    print("📞 LLAMA AHORA AL +18632190153")
    print("=" * 60)
    
    rooms_previos = {}
    
    for i in range(180):  # Monitor por 3 minutos
        try:
            # Obtener rooms
            rooms = await lk_api.room.list_rooms(api.ListRoomsRequest())
            
            for room in rooms.rooms:
                if room.name not in rooms_previos:
                    # Nuevo room detectado
                    print(f"\n🆕 NUEVO ROOM: {room.name}")
                    print(f"   ⏰ Segundo: {i}")
                    print(f"   📋 Metadata: {room.metadata}")
                    print(f"   👥 Participantes iniciales: {room.num_participants}")
                    
                    # Monitorear este room por 30 segundos
                    for j in range(30):
                        await asyncio.sleep(1)
                        
                        try:
                            participants = await lk_api.room.list_participants(
                                api.ListParticipantsRequest(room=room.name)
                            )
                            
                            if j == 0 or len(participants.participants) != rooms_previos.get(room.name, {}).get('participant_count', 0):
                                print(f"   📊 T+{j}s - Participantes: {len(participants.participants)}")
                                
                                for p in participants.participants:
                                    print(f"      👤 {p.identity}")
                                    print(f"         📱 Kind: {p.kind}")
                                    print(f"         🔗 State: {p.state}")
                                    print(f"         🎵 Audio tracks: {len([t for t in p.tracks if t.type == 1])}")
                                    print(f"         📹 Video tracks: {len([t for t in p.tracks if t.type == 2])}")
                                    print(f"         📝 Metadata: {p.metadata[:50] if p.metadata else 'None'}")
                                
                                # Check if we have both SIP and agent
                                sip_participants = [p for p in participants.participants if p.identity.startswith('sip_')]
                                agent_participants = [p for p in participants.participants if p.identity.startswith('agent-')]
                                
                                if sip_participants and agent_participants:
                                    print(f"   ✅ CONEXIÓN ESTABLECIDA!")
                                    print(f"      📞 SIP: {sip_participants[0].identity}")
                                    print(f"      🤖 Agent: {agent_participants[0].identity}")
                                    break
                                elif len(participants.participants) >= 2:
                                    print(f"   ⚠️  2 participantes pero roles no identificados")
                        
                        except Exception as e:
                            print(f"   ❌ Error obteniendo participantes: {e}")
                    
                    rooms_previos[room.name] = {
                        'participant_count': len(participants.participants) if 'participants' in locals() else 0,
                        'monitored': True
                    }
                
                elif room.name in rooms_previos and not rooms_previos[room.name].get('monitored', False):
                    # Room existente, verificar cambios
                    if room.num_participants != rooms_previos[room.name]['participant_count']:
                        participants = await lk_api.room.list_participants(
                            api.ListParticipantsRequest(room=room.name)
                        )
                        print(f"\n🔄 CAMBIO EN {room.name}")
                        print(f"   👥 Participantes: {room.num_participants}")
                        
                        for p in participants.participants:
                            print(f"      👤 {p.identity} ({p.state})")
                        
                        rooms_previos[room.name]['participant_count'] = room.num_participants
            
            # Status cada 30 segundos
            if i % 30 == 0 and i > 0:
                print(f"\n⏱️  {i}s - Rooms activos: {len(rooms.rooms)}")
            
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            await asyncio.sleep(1)
    
    print("\n✅ Monitor completado")

if __name__ == "__main__":
    asyncio.run(monitor_call_lifecycle())