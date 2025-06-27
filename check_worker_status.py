#!/usr/bin/env python3
"""
Script para verificar estado del worker y jobs
"""

import asyncio
from dotenv import load_dotenv
from livekit import api
import os

load_dotenv(dotenv_path=".env.local")

async def check_system_status():
    """Verificar estado completo del sistema"""
    
    lk_api = api.LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET")
    )
    
    try:
        print("🔍 VERIFICANDO ESTADO DEL SISTEMA")
        print("=" * 50)
        
        # 1. Listar rooms
        rooms = await lk_api.room.list_rooms(api.ListRoomsRequest())
        print(f"\n🏠 ROOMS ACTIVOS: {len(rooms.rooms)}")
        
        for room in rooms.rooms:
            print(f"   📋 {room.name}")
            print(f"      Participantes: {room.num_participants}")
            print(f"      Metadata: {room.metadata[:100] if room.metadata else 'None'}...")
        
        # 2. Verificar dispatch rules (si existe el endpoint)
        print(f"\n📡 CONFIGURACIÓN SIP:")
        print(f"   Outbound Trunk ID: {os.getenv('SIP_OUTBOUND_TRUNK_ID')}")
        
        # 3. Mostrar configuración del worker
        print(f"\n⚙️ CONFIGURACIÓN WORKER:")
        print(f"   LiveKit URL: {os.getenv('LIVEKIT_URL')}")
        print(f"   API Key: {os.getenv('LIVEKIT_API_KEY')[:10]}...")
        
        # 4. Crear un room simple para probar
        print(f"\n🧪 CREANDO ROOM DE PRUEBA SIMPLE...")
        simple_room = await lk_api.room.create_room(
            api.CreateRoomRequest(name="test-worker-response")
        )
        print(f"   ✅ Room creado: {simple_room.name}")
        
        # Esperar y verificar
        await asyncio.sleep(3)
        
        participants = await lk_api.room.list_participants(
            api.ListParticipantsRequest(room="test-worker-response")
        )
        
        print(f"   📊 Participantes después de 3s: {len(participants.participants)}")
        
        # Limpiar room de prueba
        await lk_api.room.delete_room(
            api.DeleteRoomRequest(room="test-worker-response")
        )
        print(f"   🧹 Room de prueba eliminado")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_system_status())