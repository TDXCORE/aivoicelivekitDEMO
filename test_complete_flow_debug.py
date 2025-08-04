#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test completo paso a paso para debuggear el flujo exacto
"""

import sys
from datetime import datetime

# Agregar la ruta del proyecto
sys.path.append('.')

def test_complete_flow_debug():
    """Test paso a paso del flujo completo"""
    try:
        from src.agents.whatsapp_agent import TDXWhatsAppAgentV2
        
        print("=== TEST FLUJO COMPLETO PASO A PASO ===")
        print()
        
        # Crear instancia del bot
        bot = TDXWhatsAppAgentV2(
            contact_name="Freddy Rincones",
            company_name="Su empresa",
            prospect_info={'email': None, 'phone': None},
            conversation_id=883
        )
        
        # Simular la conversación paso a paso
        steps = [
            "Freddy, Freddyrincones@gmail.com",  # Usuario proporciona nombre y email
            "mañana en la mañana",               # Usuario proporciona horario
            "freddy"                             # Usuario repite nombre
        ]
        
        for i, user_message in enumerate(steps, 1):
            print(f"\n--- PASO {i}: Usuario dice '{user_message}' ---")
            
            # Actualizar datos del usuario
            print("Antes de actualizar datos:")
            print(f"  Email: {bot.collected_data['email']}")
            print(f"  Teléfono: {bot.collected_data['phone']}")
            print(f"  Nombre: {bot.collected_data['name']}")
            
            bot._update_collected_data(user_message)
            
            print("Después de actualizar datos:")
            print(f"  Email: {bot.collected_data['email']}")
            print(f"  Teléfono: {bot.collected_data['phone']}")
            print(f"  Nombre: {bot.collected_data['name']}")
            print(f"  Servicio: {bot.collected_data['service_interest']}")
            print(f"  Datos completos: {bot.collected_data['all_data_complete']}")
            
            # Agregar al log de conversación
            bot.conversation_log.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'user_message',
                'content': user_message
            })
            
            # Generar respuesta del bot
            intent_result = type('Intent', (), {'category': 'tdx_service', 'industry': 'finanzas'})()
            service_result = {'service': 'AI_AUTOMATION', 'confidence': 0.8}
            
            respuesta = bot._generate_fallback_response(user_message, intent_result, service_result)
            
            print(f"Respuesta del bot: {respuesta}")
            
            # Agregar respuesta del bot al log
            bot.conversation_log.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'assistant_message',
                'content': respuesta
            })
            
            # Verificar si pide teléfono
            pide_telefono = 'teléfono' in respuesta.lower() or 'telefono' in respuesta.lower()
            print(f"¿Pide teléfono? {'SÍ' if pide_telefono else 'NO'}")
            
            # Verificar condiciones específicas para el CASO 3
            print(f"Condición CASO 3 (email and not phone): {bool(bot.collected_data['email'] and not bot.collected_data['phone'])}")
            
            if pide_telefono:
                print("✅ ¡TELÉFONO SOLICITADO CORRECTAMENTE!")
                break
            elif i == len(steps):
                print("❌ PROBLEMA: No se solicitó teléfono en ningún paso")
        
        print(f"\n{'='*70}")
        print("RESUMEN FINAL:")
        print(f"Email detectado: {bot.collected_data['email']}")
        print(f"Teléfono detectado: {bot.collected_data['phone']}")
        print(f"Nombre detectado: {bot.collected_data['name']}")
        print(f"Servicio detectado: {bot.collected_data['service_interest']}")
        print(f"Datos completos: {bot.collected_data['all_data_complete']}")
        print(f"{'='*70}")
        
        # Verificar si el problema está en que no se detecta el servicio de interés
        if not bot.collected_data['service_interest']:
            print("⚠️  POSIBLE PROBLEMA: No se detectó servicio de interés")
            print("Esto podría afectar la lógica de all_data_complete")
            
            # Forzar servicio de interés y probar de nuevo
            bot.collected_data['service_interest'] = 'finanzas'
            bot.collected_data['all_data_complete'] = bool(
                bot.collected_data['email'] and
                bot.collected_data['phone'] and
                bot.collected_data['name'] and
                bot.collected_data.get('service_interest')
            )
            
            print(f"Después de forzar servicio 'finanzas':")
            print(f"  Datos completos: {bot.collected_data['all_data_complete']}")
            
            # Probar respuesta de nuevo
            respuesta_final = bot._generate_fallback_response("test", intent_result, service_result)
            pide_telefono_final = 'teléfono' in respuesta_final.lower() or 'telefono' in respuesta_final.lower()
            
            print(f"Respuesta final: {respuesta_final}")
            print(f"¿Pide teléfono ahora? {'SÍ' if pide_telefono_final else 'NO'}")
            
            return pide_telefono_final
        
        return False
        
    except Exception as e:
        print(f"Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Ejecutando test completo paso a paso...\n")
    
    success = test_complete_flow_debug()
    
    print(f"\n🎯 RESULTADO: {'✅ FUNCIONANDO CORRECTAMENTE' if success else '❌ PROBLEMA CONFIRMADO'}")
