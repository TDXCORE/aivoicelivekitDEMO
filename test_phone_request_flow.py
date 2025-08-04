#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test específico para verificar que el bot pida teléfono después del email
"""

import sys
from datetime import datetime

# Agregar la ruta del proyecto
sys.path.append('.')

def test_phone_request_flow():
    """Test específico para el flujo de solicitud de teléfono"""
    try:
        from src.agents.whatsapp_agent import TDXWhatsAppAgentV2
        
        print("=== TEST FLUJO SOLICITUD DE TELÉFONO ===")
        print()
        
        # Crear instancia del bot
        bot = TDXWhatsAppAgentV2(
            contact_name="Freddy Rincones",
            company_name="Su empresa",
            prospect_info={'email': None, 'phone': None},
            conversation_id=882
        )
        
        # Simular que ya tenemos email pero no teléfono
        bot.collected_data['email'] = 'freddyrincones@gmail.com'
        bot.collected_data['name'] = 'Freddy'
        bot.collected_data['service_interest'] = 'finanzas'
        
        print("--- ESTADO INICIAL ---")
        print(f"Email: {bot.collected_data['email']}")
        print(f"Teléfono: {bot.collected_data['phone']}")
        print(f"Nombre: {bot.collected_data['name']}")
        print(f"Servicio: {bot.collected_data['service_interest']}")
        
        # Simular conversación previa
        bot.conversation_log = [
            {'timestamp': datetime.now().isoformat(), 'type': 'user_message', 'content': 'quiero servicios de ia'},
            {'timestamp': datetime.now().isoformat(), 'type': 'assistant_message', 'content': '¿En qué área específica?'},
            {'timestamp': datetime.now().isoformat(), 'type': 'user_message', 'content': 'en finanzas'},
            {'timestamp': datetime.now().isoformat(), 'type': 'assistant_message', 'content': '¿Podrías proporcionarme tu nombre y email?'},
            {'timestamp': datetime.now().isoformat(), 'type': 'user_message', 'content': 'Freddy, freddyrincones@gmail.com'},
        ]
        
        print("\n--- GENERANDO RESPUESTA FALLBACK ---")
        
        # Crear objetos mock para intent y service
        intent_result = type('Intent', (), {'category': 'tdx_service', 'industry': 'finanzas'})()
        service_result = {'service': 'AI_AUTOMATION', 'confidence': 0.8}
        
        # Generar respuesta fallback (esto es lo que debería pedir teléfono)
        respuesta = bot._generate_fallback_response("ok", intent_result, service_result)
        
        print(f"Respuesta generada: {respuesta}")
        
        # Verificar si la respuesta pide teléfono
        pide_telefono = 'teléfono' in respuesta.lower() or 'telefono' in respuesta.lower()
        print(f"¿Pide teléfono? {'SÍ' if pide_telefono else 'NO'}")
        
        # Verificar condiciones específicas
        print("\n--- VERIFICANDO CONDICIONES ---")
        print(f"collected_data['email']: {bot.collected_data['email']}")
        print(f"collected_data['phone']: {bot.collected_data['phone']}")
        print(f"Condición (email and not phone): {bool(bot.collected_data['email'] and not bot.collected_data['phone'])}")
        
        # Probar directamente la condición del CASO 3
        if bot.collected_data['email'] and not bot.collected_data['phone']:
            respuesta_directa = "Excelente, Freddy. Para completar el agendamiento, ¿me podrías proporcionar tu número de teléfono?"
            print(f"Respuesta directa del CASO 3: {respuesta_directa}")
            print("✅ CASO 3 debería activarse")
        else:
            print("❌ CASO 3 NO se activa")
        
        # Verificar si hay otros casos que se activan antes
        print("\n--- VERIFICANDO OTROS CASOS ---")
        
        # CASO 1: Usuario seleccionó horario
        print(f"selected_time_slot: {bot.collected_data.get('selected_time_slot')}")
        
        # CASO 2: Todos los datos completos
        print(f"all_data_complete: {bot.collected_data['all_data_complete']}")
        print(f"calendar_options_shown: {bot.collected_data['calendar_options_shown']}")
        
        # CASO 3: Respondiendo a opciones de calendario
        print(f"current_calendar_options: {len(bot.current_calendar_options) if bot.current_calendar_options else 0}")
        
        print(f"\n{'='*60}")
        print(f"RESULTADO: {'✅ FUNCIONANDO' if pide_telefono else '❌ PROBLEMA'}")
        print(f"{'='*60}")
        
        return pide_telefono
        
    except Exception as e:
        print(f"Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Ejecutando test específico de solicitud de teléfono...\n")
    
    success = test_phone_request_flow()
    
    print(f"\n🎯 RESULTADO: {'✅ FUNCIONANDO CORRECTAMENTE' if success else '❌ PROBLEMA CONFIRMADO'}")
