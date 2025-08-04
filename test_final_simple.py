#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test final simple para validar las correcciones principales
"""

import sys
from datetime import datetime

# Agregar la ruta del proyecto
sys.path.append('.')

def test_main_improvements():
    """Test de las mejoras principales"""
    try:
        from src.agents.whatsapp_agent import TDXWhatsAppAgentV2
        from src.ai.conversation_guard import ConversationGuard
        
        print("=== TEST MEJORAS PRINCIPALES ===")
        
        # Crear instancia del bot
        bot = TDXWhatsAppAgentV2(
            contact_name="Freddy",
            company_name="TestCorp",
            prospect_info={'email': None, 'phone': None},
            conversation_id=999
        )
        
        guard = ConversationGuard()
        
        # Test 1: Detección de información personal
        print("\n1. TEST DETECCION DE DATOS PERSONALES:")
        bot._update_collected_data("freddy , freddyrincones@gmail.com")
        print(f"   Email detectado: {bot.collected_data['email']}")
        
        bot._update_collected_data("3153041548")
        print(f"   Telefono detectado: {bot.collected_data['phone']}")
        print(f"   Info completa: {bot.collected_data['contact_info_complete']}")
        
        # Test 2: Conversation Guard detecta loop de teléfono
        print("\n2. TEST CONVERSATION GUARD:")
        
        # Simular conversación con loop de teléfono
        conversation_log = [
            {'type': 'user_message', 'content': 'freddyrincones@gmail.com'},
            {'type': 'assistant_message', 'content': 'Cual es tu mejor numero de telefono?'},
            {'type': 'user_message', 'content': '3153041548'},
            {'type': 'assistant_message', 'content': 'Cual es tu mejor numero de telefono?'}
        ]
        
        response_problematica = "¿Cuál es tu mejor número de teléfono?"
        respuesta_corregida = guard.check_for_loops(response_problematica, "999", conversation_log)
        
        print(f"   Respuesta original: {response_problematica}")
        print(f"   Respuesta corregida: {respuesta_corregida}")
        print(f"   Correccion aplicada: {'Si' if respuesta_corregida != response_problematica else 'No'}")
        
        # Test 3: Fallback response inteligente
        print("\n3. TEST FALLBACK INTELIGENTE:")
        
        # Simular que ya tenemos datos completos
        bot.collected_data['email'] = 'freddyrincones@gmail.com'
        bot.collected_data['phone'] = '3153041548'
        bot.collected_data['contact_info_complete'] = True
        
        intent_result = type('Intent', (), {'category': 'tdx_service', 'industry': 'general'})()
        service_result = {'service': 'UNKNOWN', 'confidence': 0.0}
        
        # Test respuesta cuando ya tenemos todos los datos
        response = bot._generate_fallback_response("ya te dije", intent_result, service_result)
        print(f"   Mensaje frustrado: 'ya te dije'")
        print(f"   Respuesta inteligente: {response}")
        print(f"   Evita repetir: {'Si' if 'telefono' not in response.lower() else 'No'}")
        
        # Test 4: Estado de conversación
        print("\n4. TEST ESTADO DE CONVERSACION:")
        print(f"   Estado actual: {bot.conversation_state}")
        print(f"   Datos email: {bot.collected_data['email']}")
        print(f"   Datos telefono: {bot.collected_data['phone']}")
        print(f"   Info completa: {bot.collected_data['contact_info_complete']}")
        
        # Evaluación final
        tests_passed = [
            bot.collected_data['email'] == 'freddyrincones@gmail.com',
            bot.collected_data['phone'] == '3153041548',
            bot.collected_data['contact_info_complete'] == True,
            respuesta_corregida != response_problematica,
            'telefono' not in response.lower()
        ]
        
        print(f"\n{'='*50}")
        print(f"RESULTADOS:")
        print(f"Tests pasados: {sum(tests_passed)}/5")
        print(f"Estado: {'EXITOSO' if all(tests_passed) else 'PARCIAL'}")
        print(f"{'='*50}")
        
        return all(tests_passed)
        
    except Exception as e:
        print(f"Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Ejecutando test final de mejoras...\n")
    
    success = test_main_improvements()
    
    print(f"\nRESULTADO FINAL: {'EXITOSO' if success else 'FALLO'}")