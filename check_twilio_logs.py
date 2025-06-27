#!/usr/bin/env python3
"""
Script para verificar logs de Twilio y conexión SIP
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from livekit import api

load_dotenv(dotenv_path=".env.local")

async def check_twilio_integration():
    """Verificar integración con Twilio"""
    
    lk_api = api.LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET")
    )
    
    print("🔍 VERIFICANDO INTEGRACIÓN TWILIO ↔ LIVEKIT")
    print("=" * 60)
    
    # 1. Verificar el trunk específico
    trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID")
    print(f"\n📞 1. VERIFICANDO TRUNK: {trunk_id}")
    try:
        # Listar todos los trunks y encontrar el nuestro
        trunks = await lk_api.sip.list_sip_outbound_trunk()
        trunk = None
        for t in trunks.items:
            if t.sip_trunk_id == trunk_id:
                trunk = t
                break
        
        if trunk:
            print(f"   ✅ Trunk encontrado:")
            print(f"       Nombre: {trunk.name}")
            print(f"       Dirección: {trunk.address}")
            print(f"       Números: {trunk.numbers}")
            print(f"       Usuario: {trunk.auth_username}")
            print(f"       Transporte: {trunk.transport}")
            
            # Verificar que la dirección SIP sea correcta para Twilio
            if "twilio.com" not in trunk.address:
                print(f"   ⚠️  ADVERTENCIA: Dirección SIP no parece ser de Twilio")
            else:
                print(f"   ✅ Dirección SIP correcta para Twilio")
        else:
            print(f"   ❌ Trunk {trunk_id} no encontrado")
            print(f"   📋 Trunks disponibles:")
            for t in trunks.items:
                print(f"       - {t.sip_trunk_id}: {t.name}")
            return
            
    except Exception as e:
        print(f"   ❌ Error obteniendo trunk: {e}")
        return
    
    # 2. Verificar participantes SIP recientes
    print(f"\n👥 2. PARTICIPANTES SIP ACTIVOS/RECIENTES:")
    try:
        participants = await lk_api.sip.list_sip_participant()
        if participants.items:
            print(f"   ✅ Encontrados {len(participants.items)} participantes:")
            for p in participants.items:
                print(f"   📞 {p.participant_identity}")
                print(f"       Room: {p.room_name}")
                print(f"       Estado: {p.participant_state}")
                print(f"       Call ID: {p.sip_call_id}")
        else:
            print(f"   ⚠️  No hay participantes SIP activos")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 3. Verificar rooms de llamadas recientes
    print(f"\n🏠 3. ROOMS DE LLAMADAS (últimos 10):")
    try:
        rooms = await lk_api.room.list_rooms()
        call_rooms = [r for r in rooms.rooms if r.name.startswith("call-")]
        if call_rooms:
            for room in call_rooms[:10]:  # Últimos 10
                print(f"   📞 {room.name}")
                print(f"       Participantes: {room.num_participants}")
                print(f"       Creado: {room.creation_time}")
                
                # Obtener detalles del room
                try:
                    room_info = await lk_api.room.get_participant_info(
                        room=room.name
                    )
                    print(f"       Metadatos: {room.metadata[:100] if room.metadata else 'Sin metadata'}")
                except:
                    pass
                print()
        else:
            print(f"   ⚠️  No se encontraron rooms de llamadas")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 4. Crear una llamada de prueba y monitorear
    print(f"\n🧪 4. PRUEBA DE LLAMADA CON MONITOREO:")
    test_number = "+573153041548"
    
    try:
        # Crear room
        timestamp = str(int(datetime.now().timestamp()))
        room_name = f"call-test-{timestamp[-4:]}"
        
        metadata = {
            "dial_info": {"phone_number": test_number},
            "prospect_info": {"company_name": "Test", "contact_name": "Debug"}
        }
        
        print(f"   📋 Creando room: {room_name}")
        room = await lk_api.room.create_room(
            api.CreateRoomRequest(
                name=room_name,
                metadata=json.dumps(metadata)
            )
        )
        print(f"   ✅ Room creado: {room.name}")
        
        # Crear participante SIP
        print(f"   📞 Creando participante SIP...")
        sip_participant = await lk_api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                sip_trunk_id=trunk_id,
                sip_call_to=f"tel:{test_number}",
                room_name=room.name,
                participant_identity=f"sip_{test_number.replace('+', '')}"
            )
        )
        print(f"   ✅ Participante SIP creado: {sip_participant.participant_identity}")
        
        # Esperar y verificar estado
        print(f"   ⏳ Esperando 10 segundos para verificar conexión...")
        await asyncio.sleep(10)
        
        # Verificar estado del participante
        try:
            participants_after = await lk_api.sip.list_sip_participant()
            our_participant = None
            for p in participants_after.items:
                if p.room_name == room.name:
                    our_participant = p
                    break
            
            if our_participant:
                print(f"   📊 Estado del participante:")
                print(f"       Identity: {our_participant.participant_identity}")
                print(f"       Estado: {our_participant.participant_state}")
                print(f"       Call ID: {our_participant.sip_call_id}")
            else:
                print(f"   ❌ Participante no encontrado después de 10 segundos")
                
        except Exception as e:
            print(f"   ❌ Error verificando estado: {e}")
            
        # Limpiar - eliminar room
        try:
            await lk_api.room.delete_room(api.DeleteRoomRequest(room=room.name))
            print(f"   🧹 Room de prueba eliminado")
        except:
            pass
            
    except Exception as e:
        print(f"   ❌ Error en prueba: {e}")
    
    print(f"\n" + "=" * 60)
    print("🎯 DIAGNÓSTICO COMPLETADO")
    print("\n💡 POSIBLES PROBLEMAS:")
    print("   1. Credenciales SIP incorrectas en Twilio")
    print("   2. LiveKit no puede conectar a aivoicetdx.pstn.twilio.com")
    print("   3. Número no autorizado en trunk de Twilio")
    print("   4. Problema de red/firewall entre LiveKit y Twilio")

if __name__ == "__main__":
    asyncio.run(check_twilio_integration())