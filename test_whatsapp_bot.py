#!/usr/bin/env python3
"""
Script de testing rápido para WhatsApp Bot
Para verificar que las nuevas funcionalidades funcionan correctamente
"""

import asyncio
import os
import sys
from datetime import datetime

# Configurar path para imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from whatsapp_bot import TDXWhatsAppBot

async def test_schedule_keywords():
    """Test de keywords de agendamiento automático"""
    print("🧪 TESTING WHATSAPP BOT - KEYWORDS DE AGENDAMIENTO")
    print("=" * 60)
    
    # Configurar datos de prueba
    contact_name = "Freddy Test"
    company_name = "Test Company"
    prospect_info = {
        'email': 'test@example.com',
        'phone': '+1234567890',
        'source': 'whatsapp_test',
        'chatwoot_id': 12345,
        'company_name': company_name,
        'contact_name': contact_name
    }
    conversation_id = 99999
    
    # Crear instancia del bot
    try:
        bot = TDXWhatsAppBot(
            contact_name=contact_name,
            company_name=company_name,
            prospect_info=prospect_info,
            conversation_id=conversation_id
        )
        print(f"✅ Bot creado exitosamente para {contact_name}")
    except Exception as e:
        print(f"❌ Error creando bot: {e}")
        return
    
    # Test cases para keywords de agendamiento
    test_messages = [
        "hola",
        "quiero agendar",
        "me gustaria programar una reunion",
        "cuando tienes disponibilidad?",
        "necesito una cita",
        "quiero hablar con un ejecutivo"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n📨 TEST {i}: '{message}'")
        print("-" * 40)
        
        try:
            # Verificar detección de keywords de agendamiento
            schedule_result = await bot.check_automatic_schedule_keywords(message)
            if schedule_result:
                print(f"🎯 SCHEDULE KEYWORD DETECTED!")
                print(f"📅 Response: {schedule_result[:100]}...")
                continue
            
            # Verificar detección de keywords de transferencia
            transfer_result = await bot.check_automatic_transfer_keywords(message)
            if transfer_result:
                print(f"👥 TRANSFER KEYWORD DETECTED!")
                print(f"🔄 Response: {transfer_result[:100]}...")
                continue
            
            # Si no hay detección automática, generar respuesta normal
            print("💬 Generando respuesta normal con OpenAI...")
            print("⚠️  Nota: Esta parte requiere API key de OpenAI configurada")
            
        except Exception as e:
            print(f"❌ Error procesando mensaje: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 TESTING COMPLETADO")
    print("\n📋 RESULTADOS ESPERADOS:")
    print("- 'quiero agendar' → Debería activar check_availability_whatsapp")
    print("- 'programar una reunion' → Debería activar check_availability_whatsapp") 
    print("- 'cuando tienes disponibilidad' → Debería activar check_availability_whatsapp")
    print("- 'necesito una cita' → Debería activar check_availability_whatsapp")
    print("- 'quiero hablar con un ejecutivo' → Debería activar transfer_to_human_whatsapp")

async def test_tools_configuration():
    """Test de configuración de herramientas"""
    print("\n🔧 TESTING TOOLS CONFIGURATION")
    print("=" * 60)
    
    bot = TDXWhatsAppBot(
        contact_name="Test User",
        company_name="Test Company", 
        prospect_info={'email': 'test@test.com'},
        conversation_id=99999
    )
    
    tools = bot.get_whatsapp_tools()
    
    expected_tools = [
        "schedule_meeting_whatsapp",
        "check_availability_whatsapp", 
        "transfer_to_human_whatsapp",
        "collect_email_whatsapp",
        "qualify_prospect_whatsapp"
    ]
    
    print(f"📊 Total tools configured: {len(tools)}")
    
    for tool in tools:
        tool_name = tool["function"]["name"]
        print(f"✅ {tool_name}")
        
    # Verificar que todas las herramientas esperadas estén presentes
    configured_tools = [tool["function"]["name"] for tool in tools]
    missing_tools = [tool for tool in expected_tools if tool not in configured_tools]
    
    if missing_tools:
        print(f"❌ MISSING TOOLS: {missing_tools}")
    else:
        print("✅ All expected tools are configured!")

def main():
    """Función principal de testing"""
    print("🚀 INICIANDO TESTS DEL WHATSAPP BOT HOMOLOGADO")
    print("=" * 60)
    
    # Verificar que las variables de entorno estén configuradas
    required_env_vars = [
        'VITE_CHATWOOT_ACCOUNT_ID',
        'VITE_CHATWOOT_API_TOKEN', 
        'OPENAI_API_KEY'
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  WARNING: Missing environment variables: {missing_vars}")
        print("   Some tests may not work completely without these.")
        print()
    
    # Ejecutar tests
    asyncio.run(test_tools_configuration())
    asyncio.run(test_schedule_keywords())

if __name__ == "__main__":
    main()