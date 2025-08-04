#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test específico para el caso problemático reportado por el usuario
"""

import asyncio
import sys
from datetime import datetime

# Agregar la ruta del proyecto
sys.path.append('.')

def test_specific_conversation():
    """Test del caso específico problemático"""
    try:
        from src.agents.whatsapp_agent import TDXWhatsAppAgentV2
        from src.ai.conversation_guard import ConversationGuard
        
        print("=== TEST CASO ESPECÍFICO ===")
        
        # Crear instancia del bot
        bot = TDXWhatsAppAgentV2(
            contact_name="Freddy Rincones",
            company_name="Empresa",
            prospect_info={'email': None, 'phone': None, 'source': 'whatsapp'},
            conversation_id=999
        )
        
        guard = ConversationGuard()
        
        # Conversación exacta del problema reportado
        test_messages = [
            "hola",
            "mas informacion", 
            "si automatizacion",
            "si claro",
            "freddy , freddyrincones@gmail.com",
            "3153041548",
            "ya te dije"
        ]
        
        expected_behaviors = [
            "Debe saludar",
            "Debe dar información sobre TDX",
            "Debe confirmar interés en automatización",
            "Debe pedir datos personales",
            "Debe confirmar email y pedir teléfono",
            "Debe confirmar que tiene todos los datos - NO pedir teléfono otra vez",
            "Debe reconocer frustración y disculparse"
        ]
        
        responses = []
        
        for i, (message, expected) in enumerate(zip(test_messages, expected_behaviors)):
            print(f"\n--- Intercambio {i+1} ---")
            print(f"Usuario: {message}")
            print(f"Esperado: {expected}")
            
            # Actualizar log de conversación
            bot.conversation_log.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'user_message',
                'content': message
            })
            
            # Procesar mensaje
            try:
                # Crear objetos mock
                intent_result = type('Intent', (), {
                    'category': 'greeting' if i == 0 else 'tdx_service',
                    'industry': 'general'
                })()
                
                service_result = {
                    'service': 'AI_CHATBOT' if 'automatizacion' in message else 'UNKNOWN',
                    'confidence': 0.8 if 'automatizacion' in message else 0.0
                }
                
                # Actualizar datos recopilados
                bot._update_collected_data(message)
                
                # Generar respuesta
                response = bot._generate_fallback_response(message, intent_result, service_result)
                
                # Aplicar conversation guard
                final_response = guard.check_for_loops(response, str(bot.conversation_id), bot.conversation_log)
                
                # Agregar respuesta al log
                bot.conversation_log.append({
                    'timestamp': datetime.now().isoformat(),
                    'type': 'assistant_message',
                    'content': final_response
                })
                
                responses.append(final_response)
                print(f"Bot: {final_response}")
                
                # Mostrar estado interno
                print(f"Estado datos: Email={bot.collected_data['email']}, Phone={bot.collected_data['phone']}")
                print(f"Estado conversación: {bot.conversation_state}")
                
                if final_response != response:
                    print(f"   >> Conversation Guard aplicó corrección")
                
            except Exception as e:
                print(f"Error: {e}")
                responses.append(f"Error: {e}")
        
        # Análisis de resultados
        print(f"\n{'='*60}")
        print("ANÁLISIS DE RESULTADOS")
        print(f"{'='*60}")
        
        # Verificar problemas específicos del caso
        problem_checks = {
            'No repite pregunta por teléfono': responses[5] != responses[4] and 'teléfono' not in responses[5].lower(),
            'Reconoce frustración': 'disculpa' in responses[6].lower() or 'razón' in responses[6].lower(),
            'Progresa correctamente': not any('en qué puedo ayudarte' in resp.lower() for resp in responses[3:]),
            'Detecta email correctamente': bot.collected_data['email'] == 'freddyrincones@gmail.com',
            'Detecta teléfono correctamente': bot.collected_data['phone'] == '3153041548',
            'Estado final correcto': bot.collected_data['contact_info_complete']
        }
        
        print("\nVERIFICACIONES:")
        for check, passed in problem_checks.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"   {status} {check}")
        
        print(f"\nRESPUESTA PROBLEMÁTICA ORIGINAL (intercambio 6):")
        print(f"   Antes: 'Te contacto directamente. ¿Cuál es tu mejor número de teléfono?'")
        print(f"   Ahora: '{responses[5]}'")
        
        print(f"\nRESPUESTA PROBLEMÁTICA ORIGINAL (intercambio 7):")
        print(f"   Antes: 'Perfecto, Freddy. Cuéntame, ¿en qué puedo ayudarte hoy?'")
        print(f"   Ahora: '{responses[6]}'")
        
        all_passed = all(problem_checks.values())
        print(f"\n{'✓ TODAS LAS CORRECCIONES FUNCIONAN' if all_passed else '✗ ALGUNAS CORRECCIONES FALLARON'}")
        
        return all_passed
        
    except Exception as e:
        print(f"Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Ejecutando test del caso específico...\n")
    
    success = test_specific_conversation()
    
    print(f"\n{'='*60}")
    print(f"{'RESULTADO: EXITOSO' if success else 'RESULTADO: FALLÓ'}")
    print(f"{'='*60}")