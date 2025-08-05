#!/usr/bin/env python3
"""
Test simple para validar que las mejoras funcionan correctamente
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agents.whatsapp_agent import TDXWhatsAppAgentClean

async def test_conversation_flow():
    """Test del flujo de conversación corregido"""
    print("TESTING FLUJO DE CONVERSACION CORREGIDO")
    print("=" * 50)
    
    agent = TDXWhatsAppAgentClean(
        contact_name="Freddy Rincones",
        company_name="",
        prospect_info={},
        conversation_id=12345
    )
    
    # Conversación de test
    messages = [
        "soluciones de AI",        # 1. Requerimiento
        "si",                     # 2. Confirma presupuesto
        "quiero ir a la luna",    # 3. Off-topic
        "si"                      # 4. Confirma de nuevo
    ]
    
    for i, message in enumerate(messages, 1):
        print(f"\n--- PASO {i} ---")
        print(f"Usuario: {message}")
        
        try:
            response = await agent.process_message(message)
            print(f"Mati: {response}")
            
            # Estado después de cada mensaje
            print(f"Requerimiento: {agent.collected_data.get('service_interest')}")
            print(f"Presupuesto OK: {agent.collected_data.get('budget_confirmed')}")
            
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n" + "=" * 50)
    print("RESULTADO FINAL:")
    
    final_state = agent.collected_data
    
    # Validaciones
    has_requirement = bool(final_state.get('service_interest'))
    has_budget = bool(final_state.get('budget_confirmed'))
    
    print(f"Requerimiento capturado: {has_requirement} ({final_state.get('service_interest')})")
    print(f"Presupuesto confirmado: {has_budget}")
    
    if has_requirement and has_budget:
        print("\n✓ EXITO: El agente captó información clave")
        print("✓ PROGRESO: Listo para capturar datos de contacto")
    else:
        print("\n✗ FALLO: El agente no progresó correctamente")
        print("✗ PROBLEMA: Quedó en loop o no capturó datos")

async def test_empathy_and_redirection():
    """Test de empatía y redirección"""
    print("\n" + "=" * 50)  
    print("TESTING EMPATHY Y REDIRECCION")
    print("=" * 50)
    
    agent = TDXWhatsAppAgentClean(
        contact_name="Cliente Nuevo",
        company_name="",
        prospect_info={},
        conversation_id=99999
    )
    
    # Test de redirección empática
    off_topic_messages = [
        "quiero ir a la luna",
        "me gusta el fútbol", 
        "chatbot para ventas"
    ]
    
    for i, message in enumerate(off_topic_messages, 1):
        print(f"\n--- TEST {i} ---")
        print(f"Usuario: {message}")
        
        try:
            response = await agent.process_message(message)
            print(f"Mati: {response}")
            
            # Verificar si redirige hacia IA
            is_ai_related = any(word in response.lower() for word in ['ia', 'tdx', 'solucion'])
            print(f"Redirige a IA: {'SI' if is_ai_related else 'NO'}")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    # Test principal
    asyncio.run(test_conversation_flow())
    
    # Test de empatía  
    asyncio.run(test_empathy_and_redirection())
    
    print("\n" + "=" * 50)
    print("VALIDACIONES COMPLETADAS")
    print("Revisa que:")
    print("1. El agente captura requerimientos correctamente")
    print("2. Confirma presupuesto sin loops")
    print("3. Redirige temas off-topic empáticamente")
    print("4. Progresa hacia captura de datos")