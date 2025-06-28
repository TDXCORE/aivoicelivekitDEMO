#!/usr/bin/env python3
"""
Crear llamada outbound usando dispatch explícito según documentación LiveKit
"""

import asyncio
import json
import os
import random
import string
from dotenv import load_dotenv
from livekit import api

load_dotenv(dotenv_path=".env.local")

async def create_outbound_call():
    """Crear llamada outbound con dispatch explícito"""
    
    lk_api = api.LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET")
    )
    
    # Datos de la llamada
    phone_number = "+573108777663"
    
    # Metadata según documentación LiveKit
    metadata = {
        "phone_number": phone_number,
        "dial_info": {
            "phone_number": phone_number,
            "transfer_to": "+18632190153"
        },
        "prospect_info": {
            "company_name": "Empresa Test Colombia",
            "contact_name": "Contacto Prueba"
        },
        "call_direction": "outbound"
    }
    
    try:
        # 1. Crear room único para la llamada
        random_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        room_name = f"outbound-{random_suffix}"
        
        print(f"📋 Creando dispatch para llamada outbound...")
        print(f"📞 Número: {phone_number}")
        print(f"🏠 Room: {room_name}")
        
        # 2. Crear dispatch explícito según documentación LiveKit
        dispatch = await lk_api.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name="tdx-sdr-bot",  # Debe coincidir con agent_name en agent.py
                room=room_name,
                metadata=json.dumps(metadata)
            )
        )
        
        print(f"✅ Dispatch creado exitosamente!")
        print(f"📋 Dispatch: {dispatch}")
        print(f"🏠 Room: {room_name}")
        print(f"🤖 Agente: tdx-sdr-bot")
        
        print(f"\n🎯 ¡Llamada outbound iniciada!")
        print(f"   El agente se conectará al room y creará la llamada SIP")
        print(f"   Deberías recibir la llamada en {phone_number}")
        
        return room_name
        
    except Exception as e:
        print(f"❌ Error creando dispatch: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(create_outbound_call())
    if result:
        print(f"\n🎉 ¡Llamada outbound configurada!")
        print(f"   Room: {result}")
        print(f"   Monitorea los logs de Render para ver el progreso")
    else:
        print(f"\n❌ Error configurando llamada outbound")