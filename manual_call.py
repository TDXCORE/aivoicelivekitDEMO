#!/usr/bin/env python3
"""
Llamada outbound con dispatch manual del agente
"""

import asyncio
import json
import os
from dotenv import load_dotenv
from livekit import api
from agent import entrypoint, JobContext

load_dotenv(dotenv_path=".env.local")

async def manual_outbound_call():
    """Crear llamada outbound con agente manual"""
    
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
        },
        "call_direction": "outbound"
    }
    
    try:
        # 1. Crear room
        import time
        timestamp = str(int(time.time()))
        room_name = f"manual-call-{timestamp[-6:]}"
        
        print(f"📋 Creando room: {room_name}")
        room = await lk_api.room.create_room(
            api.CreateRoomRequest(
                name=room_name,
                metadata=json.dumps(metadata)
            )
        )
        print(f"✅ Room creado: {room.name}")
        
        # 2. Crear participante SIP primero
        print(f"📞 Creando participante SIP...")
        sip_participant = await lk_api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                sip_trunk_id=os.getenv("SIP_OUTBOUND_TRUNK_ID"),
                sip_call_to=metadata['dial_info']['phone_number'],
                room_name=room.name,
                participant_identity=f"sip_{metadata['dial_info']['phone_number'].replace('+', '')}"
            )
        )
        print(f"✅ SIP participant creado: {sip_participant.participant_identity}")
        
        # 3. Simular JobContext y ejecutar entrypoint manualmente
        print(f"🤖 Iniciando agente manualmente...")
        
        # Crear un mock JobContext simple
        class MockJobContext:
            def __init__(self, room_name, metadata):
                from livekit import rtc
                self.room = type('Room', (), {
                    'name': room_name,
                    'metadata': json.dumps(metadata)
                })()
                self._metadata = metadata
                
            async def wait_for_participant(self):
                # Simular espera por participante
                await asyncio.sleep(5)
                # Retornar mock participant
                return type('Participant', (), {
                    'identity': f"sip_{metadata['dial_info']['phone_number'].replace('+', '')}"
                })()
                
            def shutdown(self):
                pass
        
        # Ejecutar el entrypoint en background
        mock_ctx = MockJobContext(room.name, metadata)
        
        # NO await aquí - queremos que corra en paralelo
        task = asyncio.create_task(entrypoint(mock_ctx))
        
        print(f"✅ Agente iniciado en background")
        print(f"📞 Llamada debería estar sonando...")
        print(f"⏳ Esperando 30 segundos...")
        
        # Esperar un tiempo para que la llamada se procese
        await asyncio.sleep(30)
        
        print(f"🏁 Proceso completado")
        
        return room.name
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(manual_outbound_call())
    if result:
        print(f"\n🎯 Llamada manual completada!")
        print(f"   Room: {result}")
    else:
        print(f"\n❌ Error en llamada manual")