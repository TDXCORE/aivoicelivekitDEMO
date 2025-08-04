#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test completo del flujo corregido con ConversationGuard
"""

import sys
from datetime import datetime

# Agregar la ruta del proyecto
sys.path.append('.')

async def test_complete_fixed_flow():
    """Test completo del flujo corregido"""
    try:
        from src.agents.whatsapp_agent import TDXWhatsAppAgentV2
        
        print("=== TEST FLUJO COMPLETO CORREGIDO ===")
        print("Simulando conversación real con ConversationGuard")
        print()
        
        # Crear instancia del bot
        bot = TDXWhatsAppAgentV2(
            contact_name="Freddy Rincones",
            company_name="Su empresa",
            prospect_info={'email': None, 'phone': None},
            conversation_id=886
        )
        
        # Simular conversación completa paso a paso
        conversation_steps = [
            "quiero automatizacion para finanzas",
            "si claro agendemos",
            "freddy, freddyrincones@gmail.com",
            "freddy rincones 3153041548"
        ]
        
        print("--- SIMULANDO CONVERSACIÓN COMPLETA ---")
        
        for i, user_message in enumerate(conversation_steps, 1):
            print(f"\n{'='*50}")
            print(f"PASO {i}: Usuario dice '{user_message}'")
            
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
            print(f"all_data_complete: {bot.collected_data['all_data_complete']}")
            
            # Generar respuesta usando fallback (simula el flujo real)
            intent_result = type('Intent', (), {'category': 'tdx_service', 'industry': 'finanzas'})()
            service_result = {'service': 'AI_AUTOMATION', 'confidence': 0.8}
            
            respuesta_inicial = bot._generate_fallback_response(user_message, intent_result, service_result)
            
            # Aplicar ConversationGuard (esto es lo que pasa en el flujo real)
            respuesta_final = bot.conversation_guard.check_for_loops(
                respuesta_inicial,
                str(bot.conversation_id),
                bot.conversation_log
            )
            
            print(f"RESPUESTA INICIAL: {respuesta_inicial[:100]}...")
            print(f"RESPUESTA FINAL (después de ConversationGuard): {respuesta_final[:100]}...")
            
            # Verificar si muestra opciones de calendario
            muestra_opciones = 'opción 1' in respuesta_final.lower() and 'opción 2' in respuesta_final.lower()
            print(f"¿Muestra opciones de calendario? {'✅ SÍ' if muestra_opciones else '❌ NO'}")
            
            # Agregar respuesta del bot al log
            bot.conversation_log.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'assistant_message',
                'content': respuesta_final
            })
            
            if muestra_opciones:
                print("🎉 ¡ÉXITO! Opciones de calendario mostradas correctamente")
                break
        
        # Verificación final
        print(f"\n{'='*60}")
        print("VERIFICACIÓN FINAL DEL FLUJO:")
        print(f"✅ Email detectado: {bot.collected_data['email']}")
        print(f"✅ Teléfono detectado: {bot.collected_data['phone']}")
        print(f"✅ Servicio detectado: {bot.collected_data['service_interest']}")
        print(f"✅ Datos completos: {bot.collected_data['all_data_complete']}")
        print(f"✅ Opciones mostradas: {bot.collected_data['calendar_options_shown']}")
        
        # Test específico: ¿Se activó el CASO 2B?
        caso_2b_activado = (
            bot.collected_data['email'] and 
            bot.collected_data['phone'] and 
            bot.collected_data['name'] and 
            bot.collected_data.get('service_interest') and
            bot.collected_data['calendar_options_shown']
        )
        
        print(f"\n🎯 CASO 2B ACTIVADO: {'✅ SÍ' if caso_2b_activado else '❌ NO'}")
        
        # Verificar que ConversationGuard no interfirió incorrectamente
        guard_stats = bot.conversation_guard.get_conversation_stats(str(bot.conversation_id))
        print(f"\n📊 ESTADÍSTICAS CONVERSATIONGUARD:")
        print(f"   - Patrones rastreados: {guard_stats['patterns_tracked']}")
        print(f"   - Respuestas repetidas: {guard_stats['repeated_responses']}")
        print(f"   - Estado: {guard_stats['status']}")
        
        return caso_2b_activado
        
    except Exception as e:
        print(f"Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sync_wrapper():
    """Wrapper síncrono para el test asíncrono"""
    import asyncio
    return asyncio.run(test_complete_fixed_flow())

if __name__ == "__main__":
    print("Ejecutando test completo del flujo corregido...\n")
    
    success = test_sync_wrapper()
    
    print(f"\n🎯 RESULTADO FINAL: {'✅ FLUJO CORREGIDO EXITOSAMENTE' if success else '❌ FLUJO AÚN TIENE PROBLEMAS'}")
    
    if success:
        print("\n🚀 CORRECCIONES IMPLEMENTADAS:")
        print("   1. ✅ CASO 2B agregado para mostrar opciones cuando se completan datos")
        print("   2. ✅ ConversationGuard configurado para NO interferir con opciones de calendario")
        print("   3. ✅ Detección de datos mejorada y centralizada")
        print("   4. ✅ Flujo de agendamiento optimizado")
    else:
        print("\n❌ PROBLEMAS PENDIENTES:")
        print("   - Revisar lógica de detección de datos completos")
        print("   - Verificar condiciones del CASO 2B")
        print("   - Analizar interferencia de ConversationGuard")
