#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test del escenario específico que estaba fallando en producción
"""

import sys
from datetime import datetime

# Agregar la ruta del proyecto
sys.path.append('.')

def test_production_scenario():
    """Test del escenario exacto que falló en producción"""
    try:
        from src.agents.whatsapp_agent import TDXWhatsAppAgentV2
        from src.ai.conversation_guard import ConversationGuard
        
        print("=== TEST ESCENARIO PRODUCCIÓN ===")
        print("Simulando la conversación exacta que falló:")
        print()
        
        # Crear instancia del bot
        bot = TDXWhatsAppAgentV2(
            contact_name="Freddy",
            company_name="TestCorp",
            prospect_info={'email': None, 'phone': None},
            conversation_id=999
        )
        
        guard = ConversationGuard()
        
        # Conversación exacta que falló en producción
        conversation_steps = [
            ("¡Perfecto, Freddy! Nuestro servicio de AI_CHATBOT es ideal para automatizar tu proceso de conciliación bancaria. ¿Podemos agendar una demo para mostrarte cómo funciona? Por favor, confírmame tu nombre y email para coordinar. 🚀", "bot"),
            ("ok, freddy, freddyrincones@gmail.com", "user"),
            ("¡Gracias, Freddy! ¿Podrías confirmarme tu número de teléfono para completar la información de agendamiento? 📞", "bot"),
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
        
        print("\n--- PROBANDO RESPUESTA PROBLEMÁTICA ---")
        
        # Esta era la respuesta problemática que causaba el loop
        respuesta_problematica = "¿Cuál es tu mejor número de teléfono?"
        
        print(f"Respuesta original: {respuesta_problematica}")
        
        # Aplicar ConversationGuard
        respuesta_corregida = guard.check_for_loops(
            respuesta_problematica, 
            "999", 
            bot.conversation_log
        )
        
        print(f"Respuesta corregida: {respuesta_corregida}")
        
        # Verificar que se aplicó la corrección
        correccion_aplicada = respuesta_corregida != respuesta_problematica
        print(f"Corrección aplicada: {'SÍ' if correccion_aplicada else 'NO'}")
        
        # Verificar que la nueva respuesta no pregunta por teléfono
        no_pregunta_telefono = 'teléfono' not in respuesta_corregida.lower() and 'telefono' not in respuesta_corregida.lower()
        print(f"No pregunta teléfono: {'SÍ' if no_pregunta_telefono else 'NO'}")
        
        # Verificar estado de datos
        print(f"\n--- ESTADO DE DATOS ---")
        print(f"Email detectado: {bot.collected_data['email']}")
        print(f"Teléfono detectado: {bot.collected_data['phone']}")
        print(f"Datos completos: {bot.collected_data['all_data_complete']}")
        
        # Ahora probar el flujo correcto - debe mostrar opciones de calendario
        print(f"\n--- PROBANDO FLUJO CORRECTO ---")
        
        # Simular que el usuario da el teléfono
        intent_result = type('Intent', (), {'category': 'tdx_service', 'industry': 'general'})()
        service_result = {'service': 'AI_CHATBOT', 'confidence': 0.8}
        
        # Generar respuesta correcta
        respuesta_correcta = bot._generate_fallback_response("3153041548", intent_result, service_result)
        print(f"Respuesta correcta esperada: {respuesta_correcta[:100]}...")
        
        # Verificar que muestra opciones de calendario
        muestra_opciones = 'opción 1' in respuesta_correcta.lower() and 'opción 2' in respuesta_correcta.lower()
        print(f"Muestra opciones de calendario: {'SÍ' if muestra_opciones else 'NO'}")
        
        # Evaluación final
        tests_passed = [
            correccion_aplicada,
            no_pregunta_telefono,
            bot.collected_data['email'] == 'freddyrincones@gmail.com',
            bot.collected_data['phone'] == '3153041548',
            bot.collected_data['all_data_complete'],
            muestra_opciones
        ]
        
        print(f"\n{'='*60}")
        print(f"RESULTADOS FINALES:")
        print(f"✅ ConversationGuard detecta loop: {'PASS' if correccion_aplicada else 'FAIL'}")
        print(f"✅ No repite pregunta teléfono: {'PASS' if no_pregunta_telefono else 'FAIL'}")
        print(f"✅ Email detectado correctamente: {'PASS' if bot.collected_data['email'] == 'freddyrincones@gmail.com' else 'FAIL'}")
        print(f"✅ Teléfono detectado correctamente: {'PASS' if bot.collected_data['phone'] == '3153041548' else 'FAIL'}")
        print(f"✅ Datos marcados como completos: {'PASS' if bot.collected_data['all_data_complete'] else 'FAIL'}")
        print(f"✅ Muestra opciones de calendario: {'PASS' if muestra_opciones else 'FAIL'}")
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
    print("Ejecutando test del escenario de producción...\n")
    
    success = test_production_scenario()
    
    print(f"\n🎯 RESULTADO FINAL: {'✅ EXITOSO - PROBLEMA RESUELTO' if success else '❌ FALLO - REVISAR IMPLEMENTACIÓN'}")
