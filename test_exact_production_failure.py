#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test del escenario EXACTO que está fallando en producción - 4 de agosto 2025, 5:15 PM
"""

import sys
from datetime import datetime

# Agregar la ruta del proyecto
sys.path.append('.')

def test_exact_production_failure():
    """Test del escenario exacto que falló en producción"""
    try:
        from src.agents.whatsapp_agent import TDXWhatsAppAgentV2
        from src.ai.conversation_guard import ConversationGuard
        
        print("=== TEST ESCENARIO EXACTO DE PRODUCCIÓN ===")
        print("Conversación del 4 de agosto 2025, 4:29-4:32 PM:")
        print()
        
        # Crear instancia del bot
        bot = TDXWhatsAppAgentV2(
            contact_name="Freddy Rincones",
            company_name="Su empresa",
            prospect_info={'email': None, 'phone': None},
            conversation_id=880  # ID real de la conversación que falló
        )
        
        guard = ConversationGuard()
        
        # Conversación EXACTA que falló en producción
        conversation_steps = [
            ("Hola", "user"),
            ("¡Hola! ¿En qué puedo ayudarte hoy? 😊", "bot"),
            ("Quiero IA", "user"),
            ("¡Claro! En TDX ofrecemos soluciones de IA para potenciar tu empresa. ¿Te gustaría saber más sobre algún servicio en particular? 😊🚀", "bot"),
            ("Automatizar ventas", "user"),
            ("¡Perfecto! En TDX contamos con soluciones de IA para automatizar tus ventas. ¿Te gustaría agendar una demo para conocer más detalles? 😊🚀", "bot"),
            ("Si claro", "user"),
            ("¡Perfecto! ¿Podrías proporcionarme tu nombre y correo electrónico para agendar la demo de automatización de ventas? 😉🚀", "bot"),
            ("Freddy , freddyrincones@gmail.com", "user"),
            ("Te contacto directamente. ¿Cuál es tu mejor número de teléfono?", "bot"),
            ("3153041548", "user"),
            ("¡Gracias por proporcionar tu número! ¿Podrías confirmarme tu nombre y correo electrónico para agendar la demo de automatización de ventas? 😉🚀", "bot"),
            ("Freddy , freddyrincones@gmail.com", "user"),
            ("¡Hola Freddy! ¿Estás listo para agendar la demo de automatización de ventas? 😊🚀 ¿Tienes alguna preferencia de horario?", "bot"),
            ("Mañana ?", "user"),
            ("Te contacto directamente. ¿Cuál es tu mejor número de teléfono?", "bot"),  # AQUÍ ESTÁ EL PROBLEMA
        ]
        
        print("--- REPRODUCIENDO CONVERSACIÓN EXACTA ---")
        
        # Simular la conversación paso a paso
        for i, (message, sender) in enumerate(conversation_steps):
            print(f"[{i+1:2d}] {sender.upper()}: {message}")
            
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
        
        print("\n--- ESTADO DESPUÉS DE LA CONVERSACIÓN PROBLEMÁTICA ---")
        print(f"Nombre: {bot.collected_data['name']}")
        print(f"Email: {bot.collected_data['email']}")
        print(f"Teléfono: {bot.collected_data['phone']}")
        print(f"Servicio de interés: {bot.collected_data['service_interest']}")
        print(f"Demo confirmada: {bot.collected_data['demo_confirmed']}")
        print(f"Datos completos: {bot.collected_data['all_data_complete']}")
        
        print("\n--- PROBANDO CONVERSATION GUARD CON RESPUESTA PROBLEMÁTICA ---")
        
        # Probar la respuesta exacta que está causando el loop
        respuesta_problematica = "Te contacto directamente. ¿Cuál es tu mejor número de teléfono?"
        
        # Aplicar ConversationGuard
        respuesta_corregida = guard.check_for_loops(
            respuesta_problematica, 
            "880",  # ID real de la conversación
            bot.conversation_log
        )
        
        print(f"Respuesta original: {respuesta_problematica}")
        print(f"Respuesta corregida: {respuesta_corregida}")
        
        # Verificar si se aplicó la corrección
        correccion_aplicada = respuesta_corregida != respuesta_problematica
        print(f"¿Se aplicó corrección? {'SÍ' if correccion_aplicada else 'NO'}")
        
        # Verificar que la corrección no vuelve a preguntar por teléfono
        no_pregunta_telefono = 'teléfono' not in respuesta_corregida.lower() and 'telefono' not in respuesta_corregida.lower()
        print(f"¿No pregunta teléfono? {'SÍ' if no_pregunta_telefono else 'NO'}")
        
        # Verificar que la respuesta es apropiada
        respuesta_apropiada = any(keyword in respuesta_corregida.lower() for keyword in [
            'perfecto', 'gracias', 'contactaremos', 'demo', 'pronto'
        ])
        print(f"¿Respuesta apropiada? {'SÍ' if respuesta_apropiada else 'NO'}")
        
        print("\n--- PROBANDO FLUJO CORRECTO DESPUÉS DE CORRECCIÓN ---")
        
        # Simular que el usuario responde después de la corrección
        if correccion_aplicada:
            # El usuario debería recibir una respuesta que no pregunta por teléfono
            # y el flujo debería continuar normalmente
            
            # Simular respuesta del usuario
            bot.conversation_log.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'user_message',
                'content': 'ok perfecto'
            })
            
            # Generar respuesta que debería mostrar opciones de calendario
            intent_result = type('Intent', (), {'category': 'tdx_service', 'industry': 'ventas'})()
            service_result = {'service': 'AI_CHATBOT', 'confidence': 0.8}
            
            respuesta_siguiente = bot._generate_fallback_response("ok perfecto", intent_result, service_result)
            print(f"Respuesta siguiente: {respuesta_siguiente[:150]}...")
            
            # Verificar si muestra opciones de calendario
            muestra_opciones = 'opción 1' in respuesta_siguiente.lower() and 'opción 2' in respuesta_siguiente.lower()
            print(f"¿Muestra opciones calendario? {'SÍ' if muestra_opciones else 'NO'}")
        
        # Evaluación final
        tests_passed = [
            bot.collected_data['email'] == 'freddyrincones@gmail.com',
            bot.collected_data['phone'] == '3153041548',
            bot.collected_data['service_interest'] == 'automatización',
            correccion_aplicada,
            no_pregunta_telefono,
            respuesta_apropiada
        ]
        
        print(f"\n{'='*70}")
        print(f"DIAGNÓSTICO FINAL:")
        print(f"✅ Email detectado correctamente: {'PASS' if bot.collected_data['email'] == 'freddyrincones@gmail.com' else 'FAIL'}")
        print(f"✅ Teléfono detectado correctamente: {'PASS' if bot.collected_data['phone'] == '3153041548' else 'FAIL'}")
        print(f"✅ Servicio detectado correctamente: {'PASS' if bot.collected_data['service_interest'] == 'automatización' else 'FAIL'}")
        print(f"✅ ConversationGuard aplica corrección: {'PASS' if correccion_aplicada else 'FAIL'}")
        print(f"✅ No repite pregunta de teléfono: {'PASS' if no_pregunta_telefono else 'FAIL'}")
        print(f"✅ Respuesta apropiada: {'PASS' if respuesta_apropiada else 'FAIL'}")
        print(f"\nTests pasados: {sum(tests_passed)}/6")
        print(f"Estado: {'EXITOSO' if all(tests_passed) else 'FALLO'}")
        print(f"{'='*70}")
        
        return all(tests_passed)
        
    except Exception as e:
        print(f"Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Ejecutando test del escenario exacto que falló en producción...\n")
    
    success = test_exact_production_failure()
    
    print(f"\n🎯 RESULTADO FINAL: {'✅ CORRECCIÓN EXITOSA' if success else '❌ PROBLEMA PERSISTE'}")
    
    if success:
        print("\n🚀 La corrección está lista para despliegue en producción.")
        print("El ConversationGuard ahora detecta y corrige el loop correctamente.")
    else:
        print("\n⚠️  Se requieren correcciones adicionales antes del despliegue.")
