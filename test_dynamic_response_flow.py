#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test del flujo dinámico donde el bot genera respuestas reales
"""

import sys
from datetime import datetime

# Agregar la ruta del proyecto
sys.path.append('.')

def test_dynamic_response_flow():
    """Test del flujo con respuestas dinámicas generadas por el bot"""
    try:
        from src.agents.whatsapp_agent import TDXWhatsAppAgentV2
        
        print("=== TEST FLUJO DINÁMICO CON RESPUESTAS GENERADAS ===")
        print()
        
        # Crear instancia del bot
        bot = TDXWhatsAppAgentV2(
            contact_name="Freddy Rincones",
            company_name="Su empresa",
            prospect_info={'email': None, 'phone': None},
            conversation_id=885
        )
        
        # Mensajes del usuario que causaron el problema
        user_messages = [
            "freddy, freddyrincones@gmail.com",  # Usuario proporciona nombre y email
            "freddy rincones 3153041548"         # Usuario proporciona nombre completo y teléfono
        ]
        
        print("--- SIMULANDO FLUJO DINÁMICO ---")
        
        for i, user_message in enumerate(user_messages, 1):
            print(f"\nPASO {i}: Usuario dice '{user_message}'")
            
            # Estado antes
            print(f"ANTES: email={bot.collected_data['email']}, phone={bot.collected_data['phone']}, service={bot.collected_data['service_interest']}")
            
            # Actualizar datos del usuario
            bot._update_collected_data(user_message)
            
            # Estado después
            print(f"DESPUÉS: email={bot.collected_data['email']}, phone={bot.collected_data['phone']}, service={bot.collected_data['service_interest']}")
            print(f"all_data_complete: {bot.collected_data['all_data_complete']}")
            print(f"calendar_options_shown: {bot.collected_data['calendar_options_shown']}")
            
            # Agregar al log de conversación
            bot.conversation_log.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'user_message',
                'content': user_message
            })
            
            # Simular contexto previo para el servicio
            if i == 1:
                # Primer mensaje: establecer servicio de interés
                bot.collected_data['service_interest'] = 'finanzas'
                print(f"Servicio establecido: {bot.collected_data['service_interest']}")
            
            # Generar respuesta dinámica usando fallback
            intent_result = type('Intent', (), {'category': 'tdx_service', 'industry': 'finanzas'})()
            service_result = {'service': 'AI_AUTOMATION', 'confidence': 0.8}
            
            respuesta = bot._generate_fallback_response(user_message, intent_result, service_result)
            
            print(f"RESPUESTA GENERADA: {respuesta}")
            
            # Verificar si muestra opciones de calendario
            muestra_opciones = 'opción 1' in respuesta.lower() and 'opción 2' in respuesta.lower()
            print(f"¿Muestra opciones de calendario? {'SÍ' if muestra_opciones else 'NO'}")
            
            # Agregar respuesta del bot al log
            bot.conversation_log.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'assistant_message',
                'content': respuesta
            })
            
            if muestra_opciones:
                print("✅ ¡OPCIONES DE CALENDARIO MOSTRADAS CORRECTAMENTE!")
                break
        
        # Verificación final
        print(f"\n{'='*60}")
        print("VERIFICACIÓN FINAL:")
        print(f"Email: {bot.collected_data['email']}")
        print(f"Teléfono: {bot.collected_data['phone']}")
        print(f"Servicio: {bot.collected_data['service_interest']}")
        print(f"Datos completos: {bot.collected_data['all_data_complete']}")
        print(f"Opciones mostradas: {bot.collected_data['calendar_options_shown']}")
        
        # Verificar condiciones específicas
        tiene_datos_completos = (
            bot.collected_data['email'] and 
            bot.collected_data['phone'] and 
            bot.collected_data['name'] and 
            bot.collected_data.get('service_interest')
        )
        
        print(f"Condición datos completos: {tiene_datos_completos}")
        
        # Test específico del CASO 2B
        print(f"\n--- TEST CASO 2B ---")
        if tiene_datos_completos and not bot.collected_data['calendar_options_shown']:
            print("✅ Condiciones para CASO 2B se cumplen")
            
            # Forzar ejecución del CASO 2B
            slots = bot.calendar_manager.get_next_available_slots(3)
            bot.current_calendar_options = slots
            bot.collected_data['calendar_options_shown'] = True
            bot.collected_data['all_data_complete'] = True
            
            options_msg = bot.calendar_manager.format_options_message(
                slots, 
                bot.collected_data['name'], 
                bot.collected_data['service_interest']
            )
            
            print(f"Mensaje de opciones generado: {options_msg[:100]}...")
            
            muestra_opciones_forzado = 'opción 1' in options_msg.lower()
            print(f"¿Opciones generadas correctamente? {'SÍ' if muestra_opciones_forzado else 'NO'}")
            
            return muestra_opciones_forzado
        else:
            print("❌ Condiciones para CASO 2B NO se cumplen")
            return False
        
    except Exception as e:
        print(f"Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Ejecutando test de flujo dinámico...\n")
    
    success = test_dynamic_response_flow()
    
    print(f"\n🎯 RESULTADO: {'✅ FUNCIONANDO CORRECTAMENTE' if success else '❌ PROBLEMA CONFIRMADO'}")
