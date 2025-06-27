#!/usr/bin/env python3
"""
Script para crear un job explícito que active el bot
"""

import asyncio
import json
from dotenv import load_dotenv
from livekit import api
import os

load_dotenv(dotenv_path=".env.local")

async def create_job():
    """Crear job explícito para activar el worker"""
    
    lk_api = api.LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET")
    )
    
    room_name = "call-573153041548"
    
    # Metadata para el bot
    metadata = {
        "dial_info": {
            "phone_number": "+573153041548",
            "transfer_to": "+18632190153"
        },
        "prospect_info": {
            "company_name": "Empresa Test",
            "contact_name": "Contacto Prueba"
        }
    }
    
    try:
        # First create the room
        room = await lk_api.room.create_room(
            api.CreateRoomRequest(
                name=room_name,
                metadata=json.dumps(metadata)
            )
        )
        print(f"✅ Room creado: {room.name}")
        
        # Crear job con agente específico
        job = await lk_api.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                room=room_name,
                agent_name="tdx-sdr-bot",
                metadata=json.dumps(metadata)
            )
        )
        
        print(f"✅ Job creado: {job.job.id}")
        print(f"📞 Agente: {job.agent.name}")
        print(f"🏠 Room: {room_name}")
        print(f"📋 Estado: {job.job.state}")
        
        return job.job.id
        
    except Exception as e:
        print(f"❌ Error creando job: {e}")
        return None

if __name__ == "__main__":
    job_id = asyncio.run(create_job())
    if job_id:
        print(f"\n🎯 Job {job_id} creado. Verificando logs en Render...")
    else:
        print("\n❌ No se pudo crear el job.")