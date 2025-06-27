#!/usr/bin/env python3
"""
Debug simple para verificar la llamada
"""

import asyncio
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from livekit import api

load_dotenv(dotenv_path=".env.local")

async def debug_call():
    """Debug simple de la llamada"""
    
    lk_api = api.LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET")
    )
    
    print("🔍 DEBUG SIMPLE DE LLAMADA")
    print("=" * 40)
    
    # 1. Verificar participantes SIP activos ANTES
    print(f"\n👥 1. PARTICIPANTES SIP ANTES:")
    try:
        participants_before = await lk_api.sip.list_sip_participant(api.ListSIPParticipantRequest())
        print(f"   📊 Participantes activos: {len(participants_before.items)}")
        for p in participants_before.items:
            print(f"   📞 {p.participant_identity} en {p.room_name}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 2. Crear llamada
    print(f"\n📞 2. CREANDO LLAMADA:")
    test_number = "+573153041548"
    timestamp = str(int(datetime.now().timestamp()))
    room_name = f"call-debug-{timestamp[-4:]}"
    
    metadata = {
        "dial_info": {"phone_number": test_number},
        "prospect_info": {"company_name": "Debug Test", "contact_name": "Test"}
    }
    
    try:
        # Crear room
        print(f"   📋 Creando room: {room_name}")
        room = await lk_api.room.create_room(
            api.CreateRoomRequest(
                name=room_name,
                metadata=json.dumps(metadata)
            )
        )
        print(f"   ✅ Room creado: {room.name}")
        
        # Crear participante SIP
        print(f"   📞 Creando SIP participant...")
        sip_participant = await lk_api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                sip_trunk_id=os.getenv("SIP_OUTBOUND_TRUNK_ID"),
                sip_call_to=f"tel:{test_number}",
                room_name=room.name,
                participant_identity=f"sip_{test_number.replace('+', '')}"
            )
        )
        print(f"   ✅ SIP participant creado: {sip_participant.participant_identity}")
        print(f"   📋 Call ID: {sip_participant.sip_call_id}")
        
    except Exception as e:
        print(f"   ❌ Error creando llamada: {e}")
        return
    
    # 3. Esperar y verificar
    print(f"\n⏳ 3. ESPERANDO 15 SEGUNDOS...")
    for i in range(15):
        await asyncio.sleep(1)
        print(f"   {15-i}s restantes", end='\r')
    print()
    
    # 4. Verificar participantes SIP DESPUÉS
    print(f"\n👥 4. PARTICIPANTES SIP DESPUÉS:")
    try:
        participants_after = await lk_api.sip.list_sip_participant(api.ListSIPParticipantRequest())
        print(f"   📊 Participantes activos: {len(participants_after.items)}")
        
        our_participant = None
        for p in participants_after.items:
            print(f"   📞 {p.participant_identity}")
            print(f"       Room: {p.room_name}")
            print(f"       Estado: {p.participant_state}")
            print(f"       Call ID: {p.sip_call_id}")
            print()
            
            if p.room_name == room.name:
                our_participant = p
        
        if our_participant:
            print(f"   ✅ Nuestra llamada encontrada:")
            print(f"       Estado: {our_participant.participant_state}")
            print(f"       Call ID: {our_participant.sip_call_id}")
        else:
            print(f"   ❌ Nuestra llamada NO encontrada en participantes activos")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 5. Verificar room
    print(f"\n🏠 5. VERIFICANDO ROOM:")
    try:
        room_participants = await lk_api.room.list_participants(
            api.ListParticipantsRequest(room=room.name)
        )
        print(f"   📊 Participantes en room: {len(room_participants.participants)}")
        for p in room_participants.participants:
            print(f"   👤 {p.identity} - Estado: {p.state}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 6. Limpiar
    print(f"\n🧹 6. LIMPIANDO:")
    try:
        await lk_api.room.delete_room(api.DeleteRoomRequest(room=room.name))
        print(f"   ✅ Room eliminado")
    except Exception as e:
        print(f"   ❌ Error eliminando room: {e}")
    
    print(f"\n" + "=" * 40)
    print("🎯 DEBUG COMPLETADO")

if __name__ == "__main__":
    asyncio.run(debug_call())