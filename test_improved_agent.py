#!/usr/bin/env python3
"""
Test para verificar las mejoras del agente WhatsApp:
- Flujo directo y empático
- Máximo 6-10 palabras por frase
- Flujo correcto: requerimiento → presupuesto → datos → reunión
- Resumen detallado en invitación
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agents.whatsapp_agent import TDXWhatsAppAgentClean

async def test_improved_flow():
    """Test del flujo mejorado completo"""
    print("TESTING IMPROVED WHATSAPP AGENT")
    print("=" * 60)
    
    # Inicializar agente
    agent = TDXWhatsAppAgentClean(
        contact_name="Emma Castillo",
        company_name="Marketing Pro",
        prospect_info={},
        conversation_id=12345
    )
    
    # Test conversación simulada paso a paso
    test_messages = [
        "Necesito un bot para ventas 24/7",  # 1. Requerimiento
        "Si",  # 2. Confirmar presupuesto
        "Emma Castillo eamc081908@gmail.com",  # 3. Datos
        "54362329",  # 4. Teléfono
        "1"  # 5. Seleccionar horario
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n--- PASO {i} ---")
        print(f"Usuario: {message}")
        
        try:
            response = await agent.process_message(message)
            print(f"Mati: {response}")
            
            # Verificar estado después de cada mensaje
            print(f"Estado: {agent.collected_data}")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETADO")
    
    # Verificar que se completó el flujo
    final_state = agent.collected_data
    print(f"\nESTADO FINAL:")
    print(f"- Requerimiento: {final_state.get('service_interest')}")
    print(f"- Presupuesto confirmado: {final_state.get('budget_confirmed')}")
    print(f"- Email: {final_state.get('email')}")
    print(f"- Teléfono: {final_state.get('phone')}")
    print(f"- Reunión confirmada: {final_state.get('meeting_confirmed')}")

async def test_direct_responses():
    """Test de respuestas directas (6-10 palabras)"""
    print("\nTESTING DIRECT RESPONSES")
    print("=" * 40)
    
    agent = TDXWhatsAppAgentClean(
        contact_name="Test User",
        company_name="Test Company",
        prospect_info={},
        conversation_id=99999
    )
    
    # Test mensajes específicos
    test_cases = [
        "Hola",
        "Necesito automatización",
        "¿Cuánto cuesta?",
        "Si tengo presupuesto",
        "test@email.com"
    ]
    
    for message in test_cases:
        print(f"\nUsuario: {message}")
        try:
            response = await agent.process_message(message)
            word_count = len(response.split())
            print(f"Mati: {response}")
            print(f"Palabras: {word_count} {'OK' if word_count <= 10 else 'DEMASIADO LARGO'}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    # Test completo
    asyncio.run(test_improved_flow())
    
    # Test respuestas directas
    asyncio.run(test_direct_responses())
    
    print("\nALL TESTS COMPLETED!")