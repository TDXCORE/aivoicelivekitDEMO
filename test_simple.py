#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test simple para validar las correcciones del chatbot
"""

import asyncio
import sys
from datetime import datetime

# Agregar la ruta del proyecto
sys.path.append('.')

def test_scheduling_extraction():
    """Test de extracción de información de agendamiento"""
    try:
        from src.agents.whatsapp_agent import TDXWhatsAppAgentV2
        
        # Crear instancia del bot
        bot = TDXWhatsAppAgentV2(
            contact_name="Freddy",
            company_name="Test Company",
            prospect_info={'email': 'test@test.com', 'phone': '+123456789'},
            conversation_id=999
        )
        
        # Test de extracción de información
        test_cases = [
            ("mañana 3pm", "Debe detectar horario"),
            ("si claro seria genial", "Debe detectar confirmacion"),
            ("automatizacion", "Debe detectar servicio"),
            ("finanzas", "Debe detectar industria"),
            ("chatbots", "Debe detectar servicio especifico")
        ]
        
        print("=== TEST DE EXTRACCION DE INFORMACION ===")
        
        for message, expected in test_cases:
            recent_messages = []  # Simular mensajes previos vacíos
            result = bot._extract_scheduling_info(message, recent_messages)
            print(f"Mensaje: '{message}'")
            print(f"Resultado: {result}")
            print(f"Esperado: {expected}")
            print("-" * 50)
        
        return True
        
    except Exception as e:
        print(f"Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_conversation_guard():
    """Test del conversation guard"""
    try:
        from src.ai.conversation_guard import ConversationGuard
        
        guard = ConversationGuard()
        
        # Simular una conversación con loops
        conversation_log = [
            {'type': 'user_message', 'content': 'hola'},
            {'type': 'assistant_message', 'content': 'Hola, ¿en que puedo ayudarte?'},
            {'type': 'user_message', 'content': 'mañana 3pm'},
            {'type': 'assistant_message', 'content': '¿Qué día y hora te conviene?'},
            {'type': 'user_message', 'content': 'mañana 3pm'},
            {'type': 'assistant_message', 'content': '¿Qué día y hora te conviene?'},
        ]
        
        print("\n=== TEST DE CONVERSATION GUARD ===")
        
        # Test con respuesta repetitiva
        response = "¿Qué día y hora te conviene?"
        result = guard.check_for_loops(response, "test123", conversation_log)
        
        print(f"Respuesta original: {response}")
        print(f"Respuesta corregida: {result}")
        print(f"¿Se aplicó corrección?: {'Si' if result != response else 'No'}")
        
        return True
        
    except Exception as e:
        print(f"Error en test guard: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fallback_responses():
    """Test de respuestas fallback"""
    try:
        from src.agents.whatsapp_agent import TDXWhatsAppAgentV2
        
        # Crear instancia del bot
        bot = TDXWhatsAppAgentV2(
            contact_name="Freddy",
            company_name="Test Company", 
            prospect_info={'email': 'test@test.com', 'phone': '+123456789'},
            conversation_id=999
        )
        
        print("\n=== TEST DE RESPUESTAS FALLBACK ===")
        
        # Simular diferentes tipos de mensajes
        test_messages = [
            "mañana 3pm",
            "si claro",
            "automatizacion", 
            "finanzas",
            "podemos agendar"
        ]
        
        for message in test_messages:
            # Crear objetos mock simples
            intent_result = type('Intent', (), {'category': 'tdx_service', 'industry': 'general'})()
            service_result = {'service': 'UNKNOWN', 'confidence': 0.0}
            
            # Agregar mensaje al log
            bot.conversation_log.append({
                'type': 'user_message',
                'content': message,
                'timestamp': datetime.now().isoformat()
            })
            
            response = bot._generate_fallback_response(message, intent_result, service_result)
            
            print(f"Mensaje: '{message}' -> Respuesta: '{response[:60]}...'")
        
        return True
        
    except Exception as e:
        print(f"Error en test fallback: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Ejecutando tests simples...\n")
    
    test1 = test_scheduling_extraction()
    test2 = test_conversation_guard() 
    test3 = test_fallback_responses()
    
    print(f"\n{'='*50}")
    print(f"Resultados:")
    print(f"Test 1 (Extraccion): {'PASS' if test1 else 'FAIL'}")
    print(f"Test 2 (Guard): {'PASS' if test2 else 'FAIL'}")
    print(f"Test 3 (Fallback): {'PASS' if test3 else 'FAIL'}")
    print(f"{'='*50}")
    
    if all([test1, test2, test3]):
        print("TODOS LOS TESTS PASARON!")
    else:
        print("ALGUNOS TESTS FALLARON")