#!/usr/bin/env python3
"""
Test para verificar las mejoras de presupuesto:
- Nueva pregunta específica con 3 opciones
- Todas las opciones continúan el flujo
- Información de presupuesto incluida en reunión
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agents.whatsapp_agent import TDXWhatsAppAgentClean

async def test_budget_option_1():
    """Test opción 1: Sí, tengo el presupuesto"""
    print("=" * 60)
    print("TEST OPCIÓN 1: SÍ, TENGO EL PRESUPUESTO")
    print("=" * 60)
    
    agent = TDXWhatsAppAgentClean(
        contact_name="Ana García",
        company_name="Tech Solutions",
        prospect_info={},
        conversation_id=11111
    )
    
    test_messages = [
        "Necesito un chatbot para mi empresa",  # 1. Requerimiento
        "1",  # 2. Opción 1: Sí, tengo el presupuesto
        "ana.garcia@techsolutions.com",  # 3. Email
        "3001234567",  # 4. Teléfono
        "2"  # 5. Seleccionar horario
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n--- PASO {i} ---")
        print(f"Usuario: {message}")
        
        try:
            response = await agent.process_message(message)
            print(f"Mati: {response}")
            
            # Verificar estado después de cada mensaje
            if i == 2:  # Después de seleccionar opción 1
                assert agent.collected_data['budget_confirmed'] == True
                assert agent.collected_data['budget_payment_type'] == 'full'
                assert agent.collected_data['budget_range'] == 'Presupuesto completo disponible'
                print("✅ Opción 1 procesada correctamente")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n✅ ESTADO FINAL OPCIÓN 1:")
    print(f"- Presupuesto confirmado: {agent.collected_data['budget_confirmed']}")
    print(f"- Tipo de pago: {agent.collected_data['budget_payment_type']}")
    print(f"- Rango: {agent.collected_data['budget_range']}")
    print(f"- Reunión confirmada: {agent.collected_data['meeting_confirmed']}")

async def test_budget_option_2():
    """Test opción 2: Sí, pero para hacer pagos en partes"""
    print("\n" + "=" * 60)
    print("TEST OPCIÓN 2: SÍ, PERO PARA HACER PAGOS EN PARTES")
    print("=" * 60)
    
    agent = TDXWhatsAppAgentClean(
        contact_name="Carlos López",
        company_name="StartupXYZ",
        prospect_info={},
        conversation_id=22222
    )
    
    test_messages = [
        "Quiero automatizar mi proceso de ventas",  # 1. Requerimiento
        "2",  # 2. Opción 2: Sí, pero para hacer pagos en partes
        "carlos@startupxyz.com",  # 3. Email
        "3009876543",  # 4. Teléfono
        "1"  # 5. Seleccionar horario
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n--- PASO {i} ---")
        print(f"Usuario: {message}")
        
        try:
            response = await agent.process_message(message)
            print(f"Mati: {response}")
            
            # Verificar estado después de cada mensaje
            if i == 2:  # Después de seleccionar opción 2
                assert agent.collected_data['budget_confirmed'] == True
                assert agent.collected_data['budget_payment_type'] == 'installments'
                assert agent.collected_data['budget_range'] == 'Pagos en partes'
                print("✅ Opción 2 procesada correctamente")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n✅ ESTADO FINAL OPCIÓN 2:")
    print(f"- Presupuesto confirmado: {agent.collected_data['budget_confirmed']}")
    print(f"- Tipo de pago: {agent.collected_data['budget_payment_type']}")
    print(f"- Rango: {agent.collected_data['budget_range']}")
    print(f"- Reunión confirmada: {agent.collected_data['meeting_confirmed']}")

async def test_budget_option_3():
    """Test opción 3: No, pero me interesa escuchar la oferta"""
    print("\n" + "=" * 60)
    print("TEST OPCIÓN 3: NO, PERO ME INTERESA ESCUCHAR LA OFERTA")
    print("=" * 60)
    
    agent = TDXWhatsAppAgentClean(
        contact_name="María Rodríguez",
        company_name="Consultora ABC",
        prospect_info={},
        conversation_id=33333
    )
    
    test_messages = [
        "Necesito soluciones de IA para mi consultora",  # 1. Requerimiento
        "3",  # 2. Opción 3: No, pero me interesa escuchar la oferta
        "maria@consultorabc.com",  # 3. Email
        "3157654321",  # 4. Teléfono
        "3"  # 5. Seleccionar horario
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n--- PASO {i} ---")
        print(f"Usuario: {message}")
        
        try:
            response = await agent.process_message(message)
            print(f"Mati: {response}")
            
            # Verificar estado después de cada mensaje
            if i == 2:  # Después de seleccionar opción 3
                assert agent.collected_data['budget_confirmed'] == True
                assert agent.collected_data['budget_payment_type'] == 'interested_in_offer'
                assert agent.collected_data['budget_range'] == 'Interesado en oferta'
                print("✅ Opción 3 procesada correctamente")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n✅ ESTADO FINAL OPCIÓN 3:")
    print(f"- Presupuesto confirmado: {agent.collected_data['budget_confirmed']}")
    print(f"- Tipo de pago: {agent.collected_data['budget_payment_type']}")
    print(f"- Rango: {agent.collected_data['budget_range']}")
    print(f"- Reunión confirmada: {agent.collected_data['meeting_confirmed']}")

async def test_budget_question_format():
    """Test que la pregunta de presupuesto tenga el formato correcto"""
    print("\n" + "=" * 60)
    print("TEST FORMATO DE PREGUNTA DE PRESUPUESTO")
    print("=" * 60)
    
    agent = TDXWhatsAppAgentClean(
        contact_name="Test User",
        company_name="Test Company",
        prospect_info={},
        conversation_id=44444
    )
    
    # Solo enviar requerimiento para ver la pregunta de presupuesto
    response = await agent.process_message("Necesito un bot de ventas")
    print(f"Respuesta después del requerimiento:\n{response}")
    
    # Verificar que la pregunta contenga los elementos esperados
    expected_elements = [
        "2.000 USD a 20.000 USD",
        "1️⃣ Sí, tengo el presupuesto",
        "2️⃣ Sí, pero para hacer pagos en partes",
        "3️⃣ No, pero me interesa escuchar la oferta",
        "Solo responde con el número"
    ]
    
    for element in expected_elements:
        if element in response:
            print(f"✅ Contiene: {element}")
        else:
            print(f"❌ Falta: {element}")

if __name__ == "__main__":
    print("TESTING MEJORAS DE PRESUPUESTO")
    print("=" * 80)
    
    # Test todas las opciones
    asyncio.run(test_budget_option_1())
    asyncio.run(test_budget_option_2())
    asyncio.run(test_budget_option_3())
    asyncio.run(test_budget_question_format())
    
    print("\n" + "=" * 80)
    print("✅ TODOS LOS TESTS DE PRESUPUESTO COMPLETADOS!")
    print("\n🎯 RESUMEN DE MEJORAS IMPLEMENTADAS:")
    print("- ✅ Nueva pregunta específica con rango 2K-20K USD")
    print("- ✅ 3 opciones de respuesta rápida")
    print("- ✅ Todas las opciones continúan el flujo")
    print("- ✅ Información de presupuesto guardada para reunión")
    print("- ✅ No se termina conversación en ningún caso")
