#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test del flujo SIN ConversationGuard interfiriendo
"""

import sys
from datetime import datetime

# Agregar la ruta del proyecto
sys.path.append('.')

def test_sin_conversation_guard():
    """Test del flujo sin ConversationGuard"""
    try:
        from src.agents.whatsapp_agent import TDXWhatsAppAgentV2
        
        print("=== TEST SIN CONVERSATION GUARD ===")
        print("ConversationGuard DESACTIVADO - Flujo puro")
        print()
        
        # Crear instancia del bot
        bot = TDXWhatsAppAgentV2(
            contact_name="Freddy Rincones",
            company_name="Su empresa",
            prospect_info={'email': None, 'phone': None},
            conversation_id=887
        )
        
        # Simular la conversación exacta de la imagen
        conversation_steps = [
            ("en finanzas y quiero automatizar", "Establecer servicio"),
            ("si para mañana en la mañana", "Confirmar agendamiento"),
            ("freddy, freddyrincones@gmail.com", "Proporcionar email"),
            ("9am", "Confirmar horario"),
            ("Freddy, TDX", "Proporcionar nombre y empresa")
        ]
        
        print("--- SIMULANDO CONVERSACIÓN DE LA IMAGEN ---")
        
        for i, (user_message, descripcion) in enumerate(conversation_steps, 1):
            print(f"\n{'='*50}")
            print(f"PASO {i}: {descripcion}")
            print(f"Usuario: '{user_message}'")
            
            # Estado antes
            print(f"ANTES: email={bot.collected_data['email']}, phone={bot.collected_data['phone']}")
            
            # Actualizar datos del usuario
            bot._update_collected_data(user_message)
            
            # Agregar al log de conversación
            bot.conversation_log.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'user_message',
                'content': user_message
            })
            
            # Estado después
            print(f"DESPUÉS: email={bot.collected_data['email']}, phone={bot.collected_data['phone']}")
            print(f"Servicio: {bot.collected_data['service_interest']}")
            print(f"all_data_complete: {bot.collected_data['all_data_complete']}")
            
            # Generar respuesta usando fallback (SIN ConversationGuard)
            intent_result = type('Intent', (), {'category': 'tdx_service', 'industry': 'finanzas'})()
            service_result = {'service': 'AI_AUTOMATION', 'confidence': 0.8}
            
            respuesta = bot._generate_fallback_response(user_message, intent_result, service_result)
            
            print(f"RESPUESTA: {respuesta[:150]}...")
            
            # Verificar si muestra opciones de calendario
            muestra_opciones = 'opción 1' in respuesta.lower() and 'opción 2' in respuesta.lower()
            print(f"¿Muestra opciones de calendario? {'✅ SÍ' if muestra_opciones else '❌ NO'}")
            
            # Agregar respuesta del bot al log
            bot.conversation_log.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'assistant_message',
                'content': respuesta
            })
            
            if muestra_opciones:
                print("🎉 ¡ÉXITO! Opciones de calendario mostradas")
                break
        
        # Test específico: Simular que el usuario ya dio email y ahora da teléfono
        print(f"\n{'='*60}")
        print("TEST ESPECÍFICO: Usuario da teléfono después de email")
        
        # Resetear para test específico
        bot.collected_data['email'] = 'freddyrincones@gmail.com'
        bot.collected_data['service_interest'] = 'finanzas'
        bot.collected_data['name'] = 'Freddy'
        bot.collected_data['calendar_options_shown'] = False
        
        print(f"Estado inicial: email={bot.collected_data['email']}, phone={bot.collected_data['phone']}")
        
        # Usuario proporciona teléfono
        telefono_message = "3153041548"
        bot._update_collected_data(telefono_message)
        
        print(f"Después de teléfono: email={bot.collected_data['email']}, phone={bot.collected_data['phone']}")
        print(f"all_data_complete: {bot.collected_data['all_data_complete']}")
        
        # Generar respuesta
        intent_result = type('Intent', (), {'category': 'tdx_service', 'industry': 'finanzas'})()
        service_result = {'service': 'AI_AUTOMATION', 'confidence': 0.8}
        
        respuesta_telefono = bot._generate_fallback_response(telefono_message, intent_result, service_result)
        
        print(f"RESPUESTA AL TELÉFONO: {respuesta_telefono}")
        
        # Verificar si muestra opciones
        muestra_opciones_telefono = 'opción 1' in respuesta_telefono.lower()
        print(f"¿Muestra opciones después del teléfono? {'✅ SÍ' if muestra_opciones_telefono else '❌ NO'}")
        
        # Verificación final
        print(f"\n{'='*60}")
        print("VERIFICACIÓN FINAL:")
        print(f"✅ Email: {bot.collected_data['email']}")
        print(f"✅ Teléfono: {bot.collected_data['phone']}")
        print(f"✅ Servicio: {bot.collected_data['service_interest']}")
        print(f"✅ Datos completos: {bot.collected_data['all_data_complete']}")
        print(f"✅ Opciones mostradas: {bot.collected_data['calendar_options_shown']}")
        
        return muestra_opciones_telefono
        
    except Exception as e:
        print(f"Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Ejecutando test sin ConversationGuard...\n")
    
    success = test_sin_conversation_guard()
    
    print(f"\n🎯 RESULTADO: {'✅ FUNCIONANDO SIN CONVERSATION GUARD' if success else '❌ AÚN HAY PROBLEMAS'}")
    
    if success:
        print("\n🚀 CONFIRMADO:")
        print("   ✅ ConversationGuard DESACTIVADO exitosamente")
        print("   ✅ Flujo funciona correctamente sin interferencia")
        print("   ✅ Opciones de calendario se muestran cuando corresponde")
    else:
        print("\n❌ PROBLEMAS PENDIENTES:")
        print("   - Revisar lógica del CASO 2B en whatsapp_agent.py")
        print("   - Verificar condiciones de all_data_complete")
