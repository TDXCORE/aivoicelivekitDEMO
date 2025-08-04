#!/usr/bin/env python3
"""
Test script para validar las correcciones del chatbot de WhatsApp
Simula la conversación problemática que se reportó
"""

import asyncio
import json
from datetime import datetime
from src.agents.whatsapp_agent import TDXWhatsAppAgentV2
from src.ai.conversation_guard import ConversationGuard

async def test_conversation_flow():
    """Test del flujo de conversación corregido"""
    print("Iniciando test de conversacion corregida...")
    
    # Crear instancia del bot
    bot = TDXWhatsAppAgentV2(
        contact_name="Freddy Rincones",
        company_name="Cegeka",
        prospect_info={
            'email': 'freddy@cegeka.com',
            'phone': '+57123456789',
            'source': 'whatsapp'
        },
        conversation_id=12345
    )
    
    # Simular la conversación problemática original
    test_messages = [
        "hola",
        "necesito unas automatizaciones para mi empresa",
        "quiero automatizar la conciliacion bancaria", 
        "todos los meses y siempre queda mal",
        "si claro seria genial",
        "automatizacion",
        "finanzas",
        "podemos agendar",
        "quiero agendar una reunion con ustedes",
        "automatizacion",
        "chatbots",
        "mañana 3pm",
        "mañana 3pm",
        "mañana 3pm"
    ]
    
    print("\nSimulando conversacion...")
    responses = []
    
    for i, message in enumerate(test_messages):
        print(f"\nUsuario: {message}")
        
        # Simular proceso del mensaje (sin llamar APIs reales)
        try:
            # El proceso normal llamaría a _generate_ai_response, pero para el test
            # vamos a simular usando solo el fallback response
            intent_result = type('IntentResult', (), {
                'category': 'tdx_service',
                'confidence': 0.8,
                'detected_service': 'AI_CHATBOT' if 'chatbot' in message else None,
                'industry': 'finanzas' if 'finanzas' in message else 'general'
            })()
            
            service_result = {
                'service': 'AI_CHATBOT' if 'chatbot' in message else 'UNKNOWN',
                'confidence': 0.8 if 'automatizar' in message else 0.0,
                'matched_keywords': ['automatizar'] if 'automatizar' in message else []
            }
            
            # Agregar mensaje del usuario al log
            bot.conversation_log.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'user_message',
                'content': message
            })
            
            # Generar respuesta usando fallback (sin OpenAI)
            response = bot._generate_fallback_response(message, intent_result, service_result)
            
            # Aplicar conversation guard
            guard = ConversationGuard()
            final_response = guard.check_for_loops(response, str(bot.conversation_id), bot.conversation_log)
            
            # Agregar respuesta del bot al log
            bot.conversation_log.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'assistant_message',
                'content': final_response
            })
            
            responses.append(final_response)
            print(f"Bot: {final_response}")
            
            # Verificar si se detectaron loops
            if final_response != response:
                print(f"   Conversation Guard aplico correccion")
                
        except Exception as e:
            print(f"Error en mensaje {i+1}: {e}")
            responses.append(f"Error: {e}")
    
    # Analisis de resultados
    print("\n" + "="*60)
    print("ANALISIS DE RESULTADOS")
    print("="*60)
    
    # Verificar repeticiones
    unique_responses = set(responses)
    repetitions = len(responses) - len(unique_responses)
    
    print(f"Total mensajes: {len(test_messages)}")
    print(f"Total respuestas: {len(responses)}")
    print(f"Respuestas unicas: {len(unique_responses)}")
    print(f"Repeticiones detectadas: {repetitions}")
    
    # Verificar si se manejan correctamente los casos especificos
    test_cases = {
        'Reconoce horario especifico': any('3:00 PM' in resp or '3pm' in resp.lower() for resp in responses),
        'Progresa en agendamiento': any('email' in resp.lower() for resp in responses),
        'Reconoce servicio especifico': any('automatizacion' in resp or 'automatización' in resp for resp in responses),
        'Evita loops infinitos': repetitions < 3
    }
    
    print("\nCASOS DE PRUEBA:")
    for test_name, passed in test_cases.items():
        status = "PASS" if passed else "FAIL"
        print(f"   {status} {test_name}")
    
    # Mostrar las ultimas 3 respuestas para verificar el patron
    print("\nULTIMAS 3 RESPUESTAS:")
    for i, resp in enumerate(responses[-3:], start=len(responses)-2):
        print(f"   {i}: {resp}")
    
    # Resultado final
    all_passed = all(test_cases.values())
    print(f"\n{'TODAS LAS PRUEBAS PASARON' if all_passed else 'ALGUNAS PRUEBAS FALLARON'}")
    
    return all_passed, responses

if __name__ == "__main__":
    # Ejecutar el test
    print("Iniciando tests de conversacion corregida...\n")
    
    try:
        success, responses = asyncio.run(test_conversation_flow())
        
        print(f"\n{'='*60}")
        print(f"Test completado {'exitosamente' if success else 'con errores'}")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"\nError durante el test: {e}")
        import traceback
        traceback.print_exc()