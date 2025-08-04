#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test del problema actual en producción - 4 de agosto 2025
"""

import sys
from datetime import datetime

# Agregar la ruta del proyecto
sys.path.append('.')

def test_current_production_issue():
    """Test del problema exacto que está ocurriendo ahora en producción"""
    try:
        from src.agents.whatsapp_agent import TDXWhatsAppAgentV2
        from src.ai.conversation_guard import ConversationGuard
        
        print("=== TEST PROBLEMA ACTUAL PRODUCCIÓN ===")
        print("Reproduciendo conversación exacta del 4 de agosto 2025:")
        print()
        
        # Crear instancia del bot
        bot = TDXWhatsAppAgentV2(
            contact_name="Freddy",
            company_name="Su empresa",
            prospect_info={'email': None, 'phone': None},
            conversation_id=123
        )
        
        guard = ConversationGuard()
        
        # Conversación exacta que está fallando en producción
        conversation_steps = [
            ("epa", "user"),
            ("¡Hola Freddy! ¿En qué puedo ayudarte hoy? 😊👋", "bot"),
            ("quiero AI", "user"),
            ("¡Perfecto, Freddy! Contamos con soluciones de IA empresarial que pueden ayudarte a optimizar tus procesos. ¿En qué área de tu empresa estás buscando implementar la IA? 🚀🤖", "bot"),
            ("automatizar conciliacon bancaria en el area de finanzas?", "user"),
            ("¡Claro, Freddy! Nuestra solución de IA puede ayudarte a automatizar la conciliación bancaria en tu área de finanzas. ¿Te gustaría agendar una demo para conocer más detalles? 🚀🤖", "bot"),
            ("si claro", "user"),
            ("¡Perfecto, Freddy! ¿Podrías proporcionarme tu nombre completo y correo electrónico para agendar la demo de automatización en finanzas? 🚀📧", "bot"),
            ("freddy , freddyrincones@gmail.com", "user"),
            ("Te contacto directamente. ¿Cuál es tu mejor número de teléfono?", "bot"),
            ("3153041548", "user"),
        ]
        
        print("--- REPRODUCIENDO CONVERSACIÓN ---")
        
        # Simular la conversación paso a paso
        for i, (message, sender) in enumerate(conversation_steps):
            print(f"[Paso {i+1}] {sender.upper()}: {message}")
            
            if sender == "user":
                # Actualizar datos del usuario
                bot._update_collected_data(message)
                
                # Agregar al log de conversación
                bot.conversation_log.append({
                    'timestamp': datetime.now().isoformat(),
                    'type': 'user_message',
                    'content': message
                })
            else:
                # Agregar respuesta del bot al log
                bot.conversation_log.append({
                    'timestamp': datetime.now().isoformat(),
                    'type': 'assistant_message',
                    'content': message
                })
        
        print("\n--- ESTADO DESPUÉS DE PROPORCIONAR TELÉFONO ---")
        print(f"Nombre: {bot.collected_data['name']}")
        print(f"Email: {bot.collected_data['email']}")
        print(f"Teléfono: {bot.collected_data['phone']}")
        print(f"Servicio de interés: {bot.collected_data['service_interest']}")
        print(f"Demo confirmada: {bot.collected_data['demo_confirmed']}")
        print(f"Datos completos: {bot.collected_data['all_data_complete']}")
        print(f"Opciones calendario mostradas: {bot.collected_data['calendar_options_shown']}")
        
        print("\n--- PROBANDO RESPUESTA DESPUÉS DEL TELÉFONO ---")
        
        # Simular que el usuario acaba de dar el teléfono
        intent_result = type('Intent', (), {'category': 'tdx_service', 'industry': 'finanzas'})()
        service_result = {'service': 'AI_CHATBOT', 'confidence': 0.8}
        
        # Generar respuesta que debería mostrar opciones de calendario
        respuesta_esperada = bot._generate_fallback_response("3153041548", intent_result, service_result)
        print(f"Respuesta generada: {respuesta_esperada[:200]}...")
        
        # Verificar si muestra opciones de calendario
        muestra_opciones = 'opción 1' in respuesta_esperada.lower() and 'opción 2' in respuesta_esperada.lower()
        print(f"¿Muestra opciones de calendario? {'SÍ' if muestra_opciones else 'NO'}")
        
        # Verificar si sigue preguntando por teléfono
        pregunta_telefono = 'teléfono' in respuesta_esperada.lower() or 'telefono' in respuesta_esperada.lower()
        print(f"¿Sigue preguntando por teléfono? {'SÍ' if pregunta_telefono else 'NO'}")
        
        # Probar ConversationGuard con la respuesta problemática
        print("\n--- PROBANDO CONVERSATION GUARD ---")
        respuesta_problematica = "Te contacto directamente. ¿Cuál es tu mejor número de teléfono?"
        respuesta_corregida = guard.check_for_loops(
            respuesta_problematica, 
            "123", 
            bot.conversation_log
        )
        
        print(f"Respuesta original: {respuesta_problematica}")
        print(f"Respuesta corregida: {respuesta_corregida}")
        correccion_aplicada = respuesta_corregida != respuesta_problematica
        print(f"¿Se aplicó corrección? {'SÍ' if correccion_aplicada else 'NO'}")
        
        # Evaluación final
        tests_passed = [
            bot.collected_data['email'] == 'freddyrincones@gmail.com',
            bot.collected_data['phone'] == '3153041548',
            bot.collected_data['service_interest'] == 'automatización',
            muestra_opciones,
            not pregunta_telefono,
            correccion_aplicada
        ]
        
        print(f"\n{'='*60}")
        print(f"DIAGNÓSTICO:")
        print(f"✅ Email detectado: {'PASS' if bot.collected_data['email'] == 'freddyrincones@gmail.com' else 'FAIL'}")
        print(f"✅ Teléfono detectado: {'PASS' if bot.collected_data['phone'] == '3153041548' else 'FAIL'}")
        print(f"✅ Servicio detectado: {'PASS' if bot.collected_data['service_interest'] == 'automatización' else 'FAIL'}")
        print(f"✅ Muestra opciones calendario: {'PASS' if muestra_opciones else 'FAIL'}")
        print(f"✅ No pregunta teléfono: {'PASS' if not pregunta_telefono else 'FAIL'}")
        print(f"✅ ConversationGuard funciona: {'PASS' if correccion_aplicada else 'FAIL'}")
        print(f"\nTests pasados: {sum(tests_passed)}/6")
        print(f"Estado: {'EXITOSO' if all(tests_passed) else 'FALLO'}")
        print(f"{'='*60}")
        
        return all(tests_passed)
        
    except Exception as e:
        print(f"Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Ejecutando test del problema actual en producción...\n")
    
    success = test_current_production_issue()
    
    print(f"\n🎯 RESULTADO: {'✅ FUNCIONANDO CORRECTAMENTE' if success else '❌ PROBLEMA PERSISTE - REQUIERE CORRECCIÓN'}")
