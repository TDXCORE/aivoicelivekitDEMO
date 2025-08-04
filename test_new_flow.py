#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test del nuevo flujo de agendamiento mejorado
"""

import sys
from datetime import datetime

# Agregar la ruta del proyecto
sys.path.append('.')

def test_new_scheduling_flow():
    """Test del nuevo flujo de agendamiento con opciones de calendario"""
    try:
        from src.agents.whatsapp_agent import TDXWhatsAppAgentV2
        from src.ai.conversation_guard import ConversationGuard
        from src.ai.calendar_manager import CalendarManager
        
        print("=== TEST NUEVO FLUJO DE AGENDAMIENTO ===")
        
        # Crear instancia del bot
        bot = TDXWhatsAppAgentV2(
            contact_name="Cliente",
            company_name="Empresa",
            prospect_info={'email': None, 'phone': None},
            conversation_id=999
        )
        
        guard = ConversationGuard()
        
        # Flujo de conversación mejorado
        test_conversation = [
            ("hola", "Saludo inicial"),
            ("me interesa automatizar mi empresa", "Interés en servicio"),
            ("si, quiero una demo", "Confirmación de demo"),
            ("Juan Perez, juan@empresa.com, 3201234567, Tech Solutions SAS", "Datos completos"),
            ("2", "Selección de horario opción 2")
        ]
        
        print("\n--- SIMULACION DE CONVERSACION ---")
        
        for i, (message, description) in enumerate(test_conversation):
            print(f"\nPaso {i+1}: {description}")
            print(f"Usuario: {message}")
            
            # Actualizar datos
            bot._update_collected_data(message)
            
            # Agregar al log
            bot.conversation_log.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'user_message',
                'content': message
            })
            
            # Generar respuesta
            intent_result = type('Intent', (), {
                'category': 'greeting' if i == 0 else 'tdx_service',
                'industry': 'general'
            })()
            
            service_result = {
                'service': 'AI_CHATBOT' if 'automatizar' in message else 'UNKNOWN',
                'confidence': 0.8 if 'automatizar' in message else 0.0
            }
            
            response = bot._generate_fallback_response(message, intent_result, service_result)
            final_response = guard.check_for_loops(response, str(bot.conversation_id), bot.conversation_log)
            
            # Agregar respuesta al log
            bot.conversation_log.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'assistant_message',
                'content': final_response
            })
            
            print(f"Bot: {final_response}")
            
            # Mostrar estado de datos
            print(f"Estado datos: {bot.collected_data}")
            print(f"Estado conversacion: {bot.conversation_state}")
            
            if final_response != response:
                print("   >> Conversation Guard aplico correccion")
            
            print("-" * 50)
        
        # Verificaciones finales
        print("\n=== VERIFICACIONES FINALES ===")
        
        checks = {
            'Datos completos detectados': bot.collected_data['all_data_complete'],
            'Email correcto': bot.collected_data['email'] == 'juan@empresa.com',
            'Telefono correcto': bot.collected_data['phone'] == '3201234567',
            'Nombre correcto': bot.collected_data['name'] == 'Juan Perez',
            'Empresa correcta': bot.collected_data['company'] == 'Tech Solutions SAS',
            'Opciones calendario mostradas': bot.collected_data['calendar_options_shown'],
            'Horario seleccionado': bot.collected_data['selected_time_slot'] is not None,
            'Reunion confirmada': bot.collected_data['meeting_confirmed']
        }
        
        for check, passed in checks.items():
            status = "PASS" if passed else "FAIL"
            print(f"   {status}: {check}")
        
        # Test específico del calendario
        print(f"\n=== TEST CALENDARIO ===")
        calendar_mgr = CalendarManager()
        slots = calendar_mgr.get_next_available_slots(3)
        print(f"Slots disponibles generados: {len(slots)}")
        
        if slots:
            options_msg = calendar_mgr.format_options_message(slots, "Juan", "automatizacion")
            print(f"Mensaje opciones: {options_msg[:100]}...")
            
            # Test selección
            selected = calendar_mgr.parse_time_selection("2", slots)
            print(f"Seleccion parseada: {selected.formatted_date if selected else 'None'}")
        
        all_passed = all(checks.values())
        print(f"\nRESULTADO: {'EXITOSO' if all_passed else 'PARCIAL'}")
        
        return all_passed
        
    except Exception as e:
        print(f"Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_parsing():
    """Test específico del parsing de datos completos"""
    try:
        from src.agents.whatsapp_agent import TDXWhatsAppAgentV2
        
        print("\n=== TEST PARSING DE DATOS ===")
        
        bot = TDXWhatsAppAgentV2("Cliente", "Empresa", {}, 999)
        
        test_cases = [
            "Juan Perez, juan@empresa.com, 3201234567, Tech Solutions",
            "Nombre: Maria Garcia, Email: maria@startup.co, Telefono: 3109876543, Empresa: StartupCo",
            "Carlos Rodriguez carlos.r@corp.com 3156789012 Corp International"
        ]
        
        for i, test_case in enumerate(test_cases):
            print(f"\nCaso {i+1}: {test_case}")
            parsed_data = bot._parse_complete_data_message(test_case)
            print(f"Resultado: {parsed_data}")
        
        return True
        
    except Exception as e:
        print(f"Error en test parsing: {e}")
        return False

if __name__ == "__main__":
    print("Ejecutando tests del nuevo flujo de agendamiento...\n")
    
    test1 = test_new_scheduling_flow()
    test2 = test_data_parsing()
    
    print(f"\n{'='*60}")
    print(f"Test flujo completo: {'PASS' if test1 else 'FAIL'}")
    print(f"Test parsing datos: {'PASS' if test2 else 'FAIL'}")
    print(f"{'='*60}")
    
    if test1 and test2:
        print("TODOS LOS TESTS PASARON - NUEVO FLUJO FUNCIONANDO")
    else:
        print("ALGUNOS TESTS FALLARON - REVISAR IMPLEMENTACION")