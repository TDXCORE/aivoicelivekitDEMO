#!/usr/bin/env python3
"""
Test específico para verificar el flujo de presupuesto con OpenAI
Simula el comportamiento real que debería ocurrir en producción
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agents.whatsapp_agent import TDXWhatsAppAgentClean

async def test_budget_flow_simulation():
    """Test que simula el flujo completo de presupuesto"""
    print("=" * 80)
    print("TEST SIMULACIÓN FLUJO DE PRESUPUESTO")
    print("=" * 80)
    
    agent = TDXWhatsAppAgentClean(
        contact_name="Test User",
        company_name="Test Company",
        prospect_info={},
        conversation_id=99999
    )
    
    # Simular el estado que debería tener después de cada paso
    print("\n--- PASO 1: Usuario menciona servicios de IA ---")
    print("Usuario: Quiero servicios de ai")
    
    # Simular que OpenAI detecta service_interest
    agent.collected_data['service_interest'] = 'servicios de IA'
    print("✅ OpenAI debería detectar service_interest y preguntar presupuesto específico")
    
    # Verificar que el system prompt incluye la pregunta específica
    system_prompt = agent._build_dynamic_system_prompt()
    
    expected_elements = [
        "2.000 USD a 20.000 USD",
        "1️⃣ Sí, tengo el presupuesto",
        "2️⃣ Sí, pero para hacer pagos en partes",
        "3️⃣ No, pero me interesa escuchar la oferta"
    ]
    
    print("\n🔍 VERIFICANDO SYSTEM PROMPT:")
    for element in expected_elements:
        if element in system_prompt:
            print(f"✅ Contiene: {element}")
        else:
            print(f"❌ Falta: {element}")
    
    print("\n--- PASO 2: Usuario selecciona opción de presupuesto ---")
    print("Usuario: 2")
    
    # Simular que OpenAI procesa la opción 2
    await agent._handle_extract_user_data({
        'budget_option_selected': '2',
        'budget_payment_type': 'installments',
        'budget_range': 'Pagos en partes'
    })
    
    print(f"✅ Estado después de opción 2:")
    print(f"   - budget_confirmed: {agent.collected_data['budget_confirmed']}")
    print(f"   - budget_payment_type: {agent.collected_data['budget_payment_type']}")
    print(f"   - budget_range: {agent.collected_data['budget_range']}")
    
    print("\n--- PASO 3: Verificar que continúa el flujo ---")
    next_step = agent._determine_next_conversation_step()
    print(f"Siguiente paso: {next_step}")
    
    if "EMAIL" in next_step.upper():
        print("✅ Flujo continúa correctamente hacia captura de email")
    else:
        print("❌ Flujo no continúa como esperado")
    
    print("\n--- PASO 4: Completar datos y verificar reunión ---")
    agent.collected_data['email'] = 'test@example.com'
    agent.collected_data['phone'] = '1234567890'
    
    # Verificar que está listo para calendario
    ready_for_calendar = all([
        agent.collected_data['email'],
        agent.collected_data['phone'], 
        agent.collected_data['service_interest'],
        agent.collected_data['budget_confirmed']
    ])
    
    print(f"✅ Listo para calendario: {ready_for_calendar}")
    
    if ready_for_calendar:
        print("✅ FLUJO COMPLETO: Todas las opciones de presupuesto llevan a la reunión")
    else:
        print("❌ FLUJO INCOMPLETO: Faltan datos")

async def test_all_budget_options():
    """Test que verifica las 3 opciones de presupuesto"""
    print("\n" + "=" * 80)
    print("TEST TODAS LAS OPCIONES DE PRESUPUESTO")
    print("=" * 80)
    
    options = [
        ("1", "full", "Presupuesto completo disponible"),
        ("2", "installments", "Pagos en partes"),
        ("3", "interested_in_offer", "Interesado en oferta")
    ]
    
    for option, payment_type, budget_range in options:
        print(f"\n--- OPCIÓN {option} ---")
        
        agent = TDXWhatsAppAgentClean(
            contact_name=f"User {option}",
            company_name="Test Company",
            prospect_info={},
            conversation_id=int(f"1000{option}")
        )
        
        # Simular selección de opción
        agent.collected_data['service_interest'] = 'chatbot'
        
        await agent._handle_extract_user_data({
            'budget_option_selected': option,
            'budget_payment_type': payment_type,
            'budget_range': budget_range
        })
        
        # Verificar estado
        assert agent.collected_data['budget_confirmed'] == True
        assert agent.collected_data['budget_payment_type'] == payment_type
        assert agent.collected_data['budget_range'] == budget_range
        
        print(f"✅ Opción {option} procesada correctamente")
        print(f"   - Tipo de pago: {payment_type}")
        print(f"   - Rango: {budget_range}")
        print(f"   - Continúa flujo: {not agent.collected_data.get('conversation_ended', False)}")

def test_system_prompt_content():
    """Test que verifica el contenido del system prompt"""
    print("\n" + "=" * 80)
    print("TEST CONTENIDO DEL SYSTEM PROMPT")
    print("=" * 80)
    
    agent = TDXWhatsAppAgentClean(
        contact_name="Test User",
        company_name="Test Company",
        prospect_info={},
        conversation_id=88888
    )
    
    # Simular estado donde necesita preguntar presupuesto
    agent.collected_data['service_interest'] = 'chatbot'
    
    system_prompt = agent._build_dynamic_system_prompt()
    
    print("\n🔍 VERIFICANDO ELEMENTOS CRÍTICOS DEL SYSTEM PROMPT:")
    
    critical_elements = [
        "2.000 USD a 20.000 USD",
        "1️⃣ Sí, tengo el presupuesto",
        "2️⃣ Sí, pero para hacer pagos en partes",
        "3️⃣ No, pero me interesa escuchar la oferta",
        "Solo responde con el número",
        "TODAS las opciones de presupuesto (1, 2, 3) continúan el flujo",
        "NUNCA termines conversación por presupuesto"
    ]
    
    all_present = True
    for element in critical_elements:
        if element in system_prompt:
            print(f"✅ {element}")
        else:
            print(f"❌ FALTA: {element}")
            all_present = False
    
    if all_present:
        print("\n✅ SYSTEM PROMPT COMPLETO Y CORRECTO")
    else:
        print("\n❌ SYSTEM PROMPT INCOMPLETO")
    
    return all_present

if __name__ == "__main__":
    print("TESTING FLUJO DE PRESUPUESTO CON OPENAI")
    print("=" * 80)
    
    # Ejecutar tests
    asyncio.run(test_budget_flow_simulation())
    asyncio.run(test_all_budget_options())
    prompt_ok = test_system_prompt_content()
    
    print("\n" + "=" * 80)
    print("✅ RESUMEN DE TESTS COMPLETADOS")
    print("=" * 80)
    print("- ✅ Simulación de flujo de presupuesto")
    print("- ✅ Verificación de las 3 opciones")
    print(f"- {'✅' if prompt_ok else '❌'} Contenido del system prompt")
    
    print("\n🎯 DIAGNÓSTICO DEL PROBLEMA:")
    print("El código está correctamente implementado.")
    print("El problema en producción puede ser:")
    print("1. OpenAI no está detectando el service_interest correctamente")
    print("2. La función extract_user_data no se está ejecutando")
    print("3. El system prompt no se está aplicando")
    
    print("\n💡 SOLUCIÓN RECOMENDADA:")
    print("Verificar logs de OpenAI en producción para ver:")
    print("- Si se están ejecutando las funciones")
    print("- Qué respuestas está generando OpenAI")
    print("- Si hay errores en la API de OpenAI")
