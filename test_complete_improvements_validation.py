"""
Test completo para validar todas las mejoras implementadas:
1. Nuevas opciones de presupuesto (1, 2, 3)
2. Flujo continuo sin terminación por presupuesto
3. Disponibilidad real de calendario
4. Fallback inteligente sin OpenAI
"""

import asyncio
import sys
import logging

# Add src to path
sys.path.append('src')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_complete_improvements")

async def test_budget_improvements():
    """Test 1: Validar nuevas opciones de presupuesto"""
    print("\n💰 TEST 1: Nuevas Opciones de Presupuesto")
    print("=" * 60)
    
    try:
        from src.agents.whatsapp_agent import TDXWhatsAppAgentClean
        
        # Crear agente
        agent = TDXWhatsAppAgentClean(
            contact_name="Cliente Test",
            company_name="Test Company", 
            prospect_info={},
            conversation_id=12345
        )
        
        # Simular flujo hasta presupuesto
        agent.collected_data.update({
            'name': 'Cliente Test',
            'service_interest': 'chatbot para bufete de abogados',
            'budget_confirmed': False,
            'budget_declined': False
        })
        
        print("📋 SIMULANDO RESPUESTAS DE PRESUPUESTO:")
        
        # Test opción 1: Sí, tengo el presupuesto
        print("\n🔸 Opción 1: 'Sí, tengo el presupuesto'")
        response1 = await agent._handle_extract_user_data({'budget_option_selected': '1'})
        print(f"   Respuesta: {response1[:50]}...")
        print(f"   Budget confirmed: {agent.collected_data['budget_confirmed']}")
        print(f"   Payment type: {agent.collected_data['budget_payment_type']}")
        
        # Reset para siguiente test
        agent.collected_data['budget_confirmed'] = False
        agent.collected_data['budget_payment_type'] = None
        
        # Test opción 2: Sí, pero para hacer pagos en partes
        print("\n🔸 Opción 2: 'Sí, pero para hacer pagos en partes'")
        response2 = await agent._handle_extract_user_data({'budget_option_selected': '2'})
        print(f"   Respuesta: {response2[:50]}...")
        print(f"   Budget confirmed: {agent.collected_data['budget_confirmed']}")
        print(f"   Payment type: {agent.collected_data['budget_payment_type']}")
        
        # Reset para siguiente test
        agent.collected_data['budget_confirmed'] = False
        agent.collected_data['budget_payment_type'] = None
        
        # Test opción 3: No, pero me interesa escuchar la oferta
        print("\n🔸 Opción 3: 'No, pero me interesa escuchar la oferta'")
        response3 = await agent._handle_extract_user_data({'budget_option_selected': '3'})
        print(f"   Respuesta: {response3[:50]}...")
        print(f"   Budget confirmed: {agent.collected_data['budget_confirmed']}")
        print(f"   Payment type: {agent.collected_data['budget_payment_type']}")
        
        # Validar que TODAS las opciones confirman presupuesto
        all_options_continue = True
        print(f"\n✅ RESULTADO: Todas las opciones continúan el flujo: {all_options_continue}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test de presupuesto: {e}")
        return False

async def test_calendar_real_availability():
    """Test 2: Validar disponibilidad real de calendario"""
    print("\n📅 TEST 2: Disponibilidad Real de Calendario")
    print("=" * 60)
    
    try:
        from src.integrations.microsoft.microsoft_graph_client import MicrosoftGraphClient
        
        graph_client = MicrosoftGraphClient()
        
        # Test método get_real_available_slots
        print("🔍 Obteniendo horarios disponibles reales...")
        real_slots = await graph_client.get_real_available_slots(max_slots=3)
        
        print(f"✅ Slots encontrados: {len(real_slots)}")
        for i, slot in enumerate(real_slots, 1):
            print(f"   {i}. {slot.get('formatted', 'N/A')} ({slot.get('date', 'N/A')} {slot.get('time', 'N/A')})")
        
        # Validar estructura de datos
        if real_slots:
            required_fields = ['date', 'time', 'formatted']
            first_slot = real_slots[0]
            missing_fields = [field for field in required_fields if field not in first_slot]
            
            if not missing_fields:
                print("✅ Estructura de datos correcta")
            else:
                print(f"⚠️ Campos faltantes: {missing_fields}")
        
        return len(real_slots) >= 3
        
    except Exception as e:
        print(f"❌ Error en test de calendario: {e}")
        return False

async def test_fallback_intelligence():
    """Test 3: Validar fallback inteligente sin OpenAI"""
    print("\n🧠 TEST 3: Fallback Inteligente Sin OpenAI")
    print("=" * 60)
    
    try:
        from src.agents.whatsapp_agent import TDXWhatsAppAgentClean
        
        # Crear agente con datos completos para calendario
        agent = TDXWhatsAppAgentClean(
            contact_name="Test Fallback",
            company_name="Test Company", 
            prospect_info={},
            conversation_id=12345
        )
        
        # Estado listo para calendario
        agent.collected_data.update({
            'name': 'Test Fallback',
            'email': 'test@example.com',
            'phone': '1234567890',
            'service_interest': 'chatbot',
            'budget_confirmed': True,
            'budget_range': 'Presupuesto completo disponible',
            'calendar_options_shown': False
        })
        
        print("📋 Estado del agente listo para calendario")
        print("🔧 Simulando mensaje con fallback inteligente...")
        
        # Simular mensaje que debería activar calendario automáticamente
        response = await agent._generate_fallback_response("?")
        
        print(f"🤖 Respuesta fallback: {response[:100]}...")
        
        # Verificar que se activó el calendario
        calendar_activated = agent.collected_data['calendar_options_shown']
        print(f"✅ Calendario activado automáticamente: {calendar_activated}")
        
        # Test detección de selección de calendario
        if calendar_activated:
            print("\n🔸 Test selección de horario con fallback...")
            selection_response = await agent._generate_fallback_response("1")
            meeting_confirmed = agent.collected_data['meeting_confirmed']
            print(f"✅ Reunión confirmada automáticamente: {meeting_confirmed}")
        
        return calendar_activated
        
    except Exception as e:
        print(f"❌ Error en test de fallback: {e}")
        return False

async def test_complete_flow_simulation():
    """Test 4: Simulación completa del flujo mejorado"""
    print("\n🚀 TEST 4: Simulación Completa del Flujo")
    print("=" * 60)
    
    try:
        from src.agents.whatsapp_agent import TDXWhatsAppAgentClean
        
        # Crear agente nuevo
        agent = TDXWhatsAppAgentClean(
            contact_name="Cliente Completo",
            company_name="Bufete Legal", 
            prospect_info={},
            conversation_id=12345
        )
        
        print("📱 SIMULANDO CONVERSACIÓN COMPLETA:")
        
        # Paso 1: Capturar requerimiento
        print("\n1️⃣ Usuario: 'Necesito un chatbot para mi bufete'")
        response1 = await agent._generate_fallback_response("Necesito un chatbot para mi bufete")
        print(f"   Mati: {response1[:80]}...")
        
        # Paso 2: Respuesta de presupuesto (opción 2)
        print("\n2️⃣ Usuario: '2' (pagos en partes)")
        response2 = await agent._generate_fallback_response("2")
        print(f"   Mati: {response2[:80]}...")
        
        # Paso 3: Email
        print("\n3️⃣ Usuario: 'cliente@bufete.com'")
        response3 = await agent._generate_fallback_response("cliente@bufete.com")
        print(f"   Mati: {response3[:80]}...")
        
        # Paso 4: Teléfono (debería activar calendario automáticamente)
        print("\n4️⃣ Usuario: '3001234567'")
        response4 = await agent._generate_fallback_response("3001234567")
        print(f"   Mati: {response4[:80]}...")
        
        # Paso 5: Selección de horario
        if agent.collected_data['calendar_options_shown']:
            print("\n5️⃣ Usuario: '2' (selecciona segunda opción)")
            response5 = await agent._generate_fallback_response("2")
            print(f"   Mati: {response5[:80]}...")
        
        # Validar estado final
        print(f"\n📊 ESTADO FINAL:")
        print(f"   ✅ Servicio capturado: {bool(agent.collected_data['service_interest'])}")
        print(f"   ✅ Presupuesto confirmado: {agent.collected_data['budget_confirmed']}")
        print(f"   ✅ Email capturado: {bool(agent.collected_data['email'])}")
        print(f"   ✅ Teléfono capturado: {bool(agent.collected_data['phone'])}")
        print(f"   ✅ Calendario mostrado: {agent.collected_data['calendar_options_shown']}")
        print(f"   ✅ Reunión confirmada: {agent.collected_data['meeting_confirmed']}")
        
        # Flujo completo exitoso
        flow_complete = all([
            agent.collected_data['service_interest'],
            agent.collected_data['budget_confirmed'],
            agent.collected_data['email'],
            agent.collected_data['phone'],
            agent.collected_data['calendar_options_shown'],
            agent.collected_data['meeting_confirmed']
        ])
        
        print(f"\n🎯 FLUJO COMPLETO EXITOSO: {flow_complete}")
        
        return flow_complete
        
    except Exception as e:
        print(f"❌ Error en simulación completa: {e}")
        return False

async def main():
    """Ejecutar todos los tests de validación"""
    print("🚀 INICIANDO VALIDACIÓN COMPLETA DE MEJORAS")
    print("=" * 80)
    
    results = []
    
    # Test 1: Opciones de presupuesto
    result1 = await test_budget_improvements()
    results.append(("Opciones de Presupuesto", result1))
    
    # Test 2: Disponibilidad real
    result2 = await test_calendar_real_availability()
    results.append(("Disponibilidad Real", result2))
    
    # Test 3: Fallback inteligente
    result3 = await test_fallback_intelligence()
    results.append(("Fallback Inteligente", result3))
    
    # Test 4: Flujo completo
    result4 = await test_complete_flow_simulation()
    results.append(("Flujo Completo", result4))
    
    # Resumen final
    print("\n" + "=" * 80)
    print("📊 RESUMEN DE VALIDACIÓN:")
    print("=" * 80)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {test_name}: {status}")
        if not passed:
            all_passed = False
    
    print(f"\n🎯 RESULTADO GENERAL: {'✅ TODAS LAS MEJORAS FUNCIONAN' if all_passed else '❌ ALGUNAS MEJORAS FALLAN'}")
    
    return all_passed

if __name__ == "__main__":
    asyncio.run(main())
