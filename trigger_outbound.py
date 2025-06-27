#!/usr/bin/env python3
"""
Script para forzar dispatch de agente a room de llamada outbound
"""

import asyncio
import json
import os
import requests
from dotenv import load_dotenv
from livekit import api

load_dotenv(dotenv_path=".env.local")

async def trigger_outbound_call():
    """Crear llamada outbound Y forzar dispatch del agente"""
    
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
        "call_direction": "outbound"  # Explicit outbound
    }
    
    try:
        # 1. Crear room simple
        import time
        timestamp = str(int(time.time()))
        room_name = f"outbound-call-{timestamp[-6:]}"
        
        print(f"📋 Creando room: {room_name}")
        room = await lk_api.room.create_room(
            api.CreateRoomRequest(
                name=room_name,
                metadata=json.dumps(metadata)
            )
        )
        print(f"✅ Room creado: {room.name}")
        
        # 2. Forzar dispatch via webhook de Render
        print(f"🤖 Forzando dispatch del agente...")
        webhook_url = f"https://aivoicelivekitdemo.onrender.com/webhook"
        
        dispatch_payload = {
            "room_name": room.name,
            "metadata": metadata,
            "action": "start_agent"
        }
        
        try:
            response = requests.post(webhook_url, json=dispatch_payload, timeout=10)
            print(f"📡 Webhook response: {response.status_code}")
        except Exception as webhook_error:
            print(f"⚠️  Webhook failed: {webhook_error}")
        
        # 3. Esperar un momento para que el agente se conecte
        print(f"⏳ Esperando 5 segundos para que agente se conecte...")
        await asyncio.sleep(5)
        
        # 4. Crear participante SIP
        print(f"📞 Creando participante SIP...")
        sip_participant = await lk_api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                sip_trunk_id=os.getenv("SIP_OUTBOUND_TRUNK_ID"),
                sip_call_to=metadata['dial_info']['phone_number'],
                room_name=room.name,
                participant_identity=f"sip_{metadata['dial_info']['phone_number'].replace('+', '')}"
            )
        )
        
        print(f"✅ Llamada iniciada!")
        print(f"📞 SIP Participant: {sip_participant.participant_identity}")
        print(f"📞 Call ID: {sip_participant.sip_call_id}")
        print(f"📞 Marcando a {metadata['dial_info']['phone_number']}")
        print(f"🏠 Room: {room.name}")
        
        return room.name
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    result = asyncio.run(trigger_outbound_call())
    if result:
        print(f"\n🎯 ¡Llamada creada exitosamente!")
        print(f"   Room: {result}")
        print(f"   El agente debería estar procesando la llamada")
    else:
        print(f"\n❌ Error creando llamada")