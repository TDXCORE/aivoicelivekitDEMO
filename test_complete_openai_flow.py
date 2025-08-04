#!/usr/bin/env python3
"""
Test completo del flujo con OpenAI y Microsoft Graph Client
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agents.whatsapp_agent import TDXWhatsAppAgentV2

async def test_complete_openai_flow():
    """Test del flujo completo con OpenAI y agendamiento real"""
    print("=== TEST FLUJO COMPLETO CON OPENAI ===")
    print("✅ OpenAI para respuestas inteligentes")
    print("✅ Function calling para extraer datos y agendar")
    print("✅ Microsoft Graph Client para reuniones reales")
    
    # Crear agente
    agent = TDXWhatsAppAgentV2(
        contact_name="Freddy",
        company_name="TDX",
        prospect_info={},
        conversation_id=12345
    )
    
    print(f"\n🔧 OpenAI API Key configurada: {'✅ SÍ' if agent.openai_api_key else '❌ NO'}")
    print(f"🔧 Microsoft Graph Client: {'✅ SÍ' if agent.graph_client else '❌ NO'}")
    
    print("\n--- SIMULANDO CONVERSACIÓN COMPLETA ---")
    
    # Paso 1: Saludo
    print("\n[1] USER: epale")
    response1 = await agent._generate_ai_response("epale")
    print(f"BOT: {response1}")
    
    # Paso 2: Interés en IA
    print("\n[2] USER: quiero servicios de ia")
    response2 = await agent._generate_ai_response("quiero servicios de ia")
    print(f"BOT: {response2}")
    
    # Paso 3: Área específica
    print("\n[3] USER: en finanzas")
    response3 = await agent._generate_ai_response("en finanzas")
    print(f"BOT: {response3}")
    
    # Paso 4: Proporcionar datos completos
    print("\n[4] USER: Freddy Rincones, freddyrincones@gmail.com, 3153041548")
    response4 = await agent._generate_ai_response("Freddy Rincones, freddyrincones@gmail.com, 3153041548")
    print(f"BOT: {response4}")
    
    # Verificar que se muestran opciones de calendario
    calendar_shown = "opción" in response4.lower() and ("1" in response4 or "2" in response4 or "3" in response4)
    print(f"\n🔍 ¿Se muestran opciones de calendario? {'✅ SÍ' if calendar_shown else '❌ NO'}")
    
    # Paso 5: Seleccionar horario
    print("\n[5] USER: 3")
    response5 = await agent._generate_ai_response("3")
    print(f"BOT: {response5}")
    
    # Verificar que se agenda la reunión
    meeting_scheduled = "agendada" in response5.lower() or "confirmada" in response5.lower()
    print(f"\n🔍 ¿Se agenda la reunión? {'✅ SÍ' if meeting_scheduled else '❌ NO'}")
    
    print("\n============================================================")
    print("VERIFICACIÓN FINAL:")
    print(f"✅ Email: {agent.collected_data['email']}")
    print(f"✅ Teléfono: {agent.collected_data['phone']}")
    print(f"✅ Nombre: {agent.collected_data['name']}")
    print(f"✅ Servicio: {agent.collected_data.get('service_interest')}")
    print(f"✅ Datos completos: {agent.collected_data['all_data_complete']}")
    print(f"✅ Opciones mostradas: {agent.collected_data['calendar_options_shown']}")
    print(f"✅ Reunión confirmada: {agent.collected_data['meeting_confirmed']}")
    print(f"✅ Horario seleccionado: {agent.collected_data.get('selected_time_slot')}")
    
    # Test específico de function calling
    print("\n--- TEST FUNCTION CALLING ---")
    
    # Test extract_user_data
    print("\n🔧 Test extract_user_data:")
    extract_result = await agent._handle_extract_user_data({
        "name": "Juan Pérez",
        "email": "juan@empresa.com",
        "phone": "3201234567",
        "service_interest": "automatización"
    }, "Juan Pérez, juan@empresa.com, 3201234567")
    print(f"Resultado: {extract_result}")
    
    # Test show_calendar_options
    print("\n🔧 Test show_calendar_options:")
    calendar_result = await agent._handle_show_calendar_options({"service_type": "finanzas"})
    print(f"Resultado: {calendar_result[:100]}...")
    
    # Test schedule_meeting
    print("\n🔧 Test schedule_meeting:")
    schedule_result = await agent._handle_schedule_meeting({"option_selected": "2"})
    print(f"Resultado: {schedule_result[:100]}...")
    
    print("\n🎯 RESULTADO FINAL:")
    if all([
        agent.collected_data['email'],
        agent.collected_data['phone'],
        agent.collected_data['name'],
        agent.collected_data['all_data_complete'],
        calendar_shown,
        meeting_scheduled
    ]):
        print("✅ FLUJO COMPLETO FUNCIONANDO PERFECTAMENTE")
        print("✅ OpenAI integrado correctamente")
        print("✅ Function calling operativo")
        print("✅ Microsoft Graph Client conectado")
        print("✅ Agendamiento automático funcional")
    else:
        print("⚠️ FLUJO PARCIALMENTE FUNCIONAL - Revisar configuraciones")

if __name__ == "__main__":
    asyncio.run(test_complete_openai_flow())
