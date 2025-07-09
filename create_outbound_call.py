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
    
    try:
    
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
    finally:
        # Close LiveKit API client to prevent unclosed session warnings
        if hasattr(lk_api, 'close'):
            await lk_api.close()
        elif hasattr(lk_api, '_session') and hasattr(lk_api._session, 'close'):
            await lk_api._session.close()

async def create_outbound_call_from_webhook(contact_data):
    """Crear llamada outbound desde webhook de Chatwoot"""
    
    lk_api = api.LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET")
    )
    
    try:
    
    # Extraer datos del contacto
    phone_number = contact_data.get("phone")
    contact_name = contact_data.get("name", "Prospecto")
    contact_email = contact_data.get("email")
    custom_attrs = contact_data.get("custom_attributes", {})
    
    # Limpiar nombre para evitar problemas
    if contact_name == "there" or not contact_name:
        contact_name = "Prospecto"
    
    # DEBUG: Log datos recibidos
    print(f"🔍 DEBUG - Contact data received:")
    print(f"   Name: '{contact_name}'")
    print(f"   Email: '{contact_email}'")
    print(f"   Phone: '{phone_number}'")
    print(f"   Custom attrs: {custom_attrs}")
    print(f"   Has email: {contact_data.get('has_email', False)}")
    
    # Crear metadata optimizada para webhook
    metadata = {
        "phone_number": phone_number,
        "dial_info": {
            "phone_number": phone_number,
            "transfer_to": "+18632190153"
        },
        "prospect_info": {
            "company_name": custom_attrs.get("company", "Su empresa"),
            "contact_name": contact_name,
            "email": contact_email,
            "has_email": contact_data.get("has_email", False),
            "chatwoot_id": contact_data.get("id"),
            "source": custom_attrs.get("source", "landing_page")
        },
        "call_direction": "outbound",
        "source": "chatwoot_webhook"
    }
    
    print(f"🎯 DEBUG - Final metadata:")
    print(f"   prospect_info: {metadata['prospect_info']}")
    
    try:
        # Crear room único para la llamada
        random_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        room_name = f"webhook-{contact_data.get('id', 'unknown')}-{random_suffix}"
        
        print(f"📋 Creando llamada desde webhook de Chatwoot...")
        print(f"👤 Contacto: {contact_name}")
        print(f"📞 Número: {phone_number}")
        print(f"📧 Email: {contact_email if contact_email else 'No proporcionado'}")
        print(f"🏠 Room: {room_name}")
        
        # Crear dispatch para el agente
        dispatch = await lk_api.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name="tdx-sdr-bot",
                room=room_name,
                metadata=json.dumps(metadata)
            )
        )
        
        print(f"✅ Dispatch creado desde webhook!")
        print(f"📋 Dispatch ID: {dispatch}")
        print(f"🏠 Room: {room_name}")
        print(f"🤖 Agente: tdx-sdr-bot")
        
        print(f"\n🎯 ¡Llamada outbound iniciada desde webhook!")
        print(f"   El agente llamará a {contact_name} ({phone_number})")
        print(f"   Personalización: {'Con email' if contact_email else 'Sin email'}")
        
        return room_name
        
    except Exception as e:
        print(f"❌ Error creando llamada desde webhook: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        # Close LiveKit API client to prevent unclosed session warnings
        if hasattr(lk_api, 'close'):
            await lk_api.close()
        elif hasattr(lk_api, '_session') and hasattr(lk_api._session, 'close'):
            await lk_api._session.close()

if __name__ == "__main__":
    result = asyncio.run(create_outbound_call())
    if result:
        print(f"\n🎉 ¡Llamada outbound configurada!")
        print(f"   Room: {result}")
        print(f"   Monitorea los logs de Render para ver el progreso")
    else:
        print(f"\n❌ Error configurando llamada outbound")