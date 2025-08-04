#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test del nuevo problema en producción - 5:21 PM del 4 de agosto 2025
Conversación termina prematuramente sin pedir teléfono ni mostrar calendario
"""

import sys
from datetime import datetime

# Agregar la ruta del proyecto
sys.path.append('.')

def test_new_production_issue():
    """Test del nuevo problema que está ocurriendo en producción"""
    try:
        from src.agents.whatsapp_agent import TDXWhatsAppAgentV2
        from src.ai.conversation_guard import ConversationGuard
        
        print("=== TEST NUEVO PROBLEMA EN PRODUCCIÓN ===")
        print("Conversación del 4 de agosto 2025, 5:21-5:22 PM:")
        print()
        
        # Crear instancia del bot
        bot = TDXWhatsAppAgentV2(
            contact_name="Freddy Rincones",
            company_name="Su empresa",
            prospect_info={'email': None, 'phone': None},
            conversation_id=881  # Nuevo ID para esta conversación
        )
        
        guard = ConversationGuard()
        
        # Conversación EXACTA que está fallando ahora
        conversation_steps = [
            ("epale", "user"),
            ("¡Hola Freddy! ¿En qué puedo ayudarte hoy? 😊", "bot"),
            ("quiero servicios de ia", "user"),
            ("¡Perfecto, Freddy! En TDX ofrecemos soluciones de IA para optimizar tu empresa. ¿En qué área específica estás buscando implementar inteligencia artificial? 🚀", "bot"),
            ("en finanzas", "user"),
            ("¡Perfecto, Freddy! En TDX contamos con soluciones de IA para optimizar tus procesos financieros. ¿Podrías proporcionarme tu nombre y dirección de correo electrónico para agendar una reunión y profundizar en tus necesidades? 🚀", "bot"),
            ("Freddy, Freddyrincones@gmail.com", "user"),
            ("¡Gracias, Freddy! ¿Podrías indicarme en qué horario te gustaría agendar nuestra reunión para hablar sobre soluciones de IA en finanzas? 🚀", "bot"),
            ("mañana en la mañana", "user"),
            ("Perfecto, Freddy. ¿Podrías proporcionarme tu nombre completo para agendar nuestra reunión sobre soluciones de IA en finanzas? 🚀", "bot"),  # PROBLEMA: repite pregunta por nombre
            ("freddy", "user"),
            ("Perfecto. Ya tenemos todo listo. Te contactaremos pronto para coordinar la demo de automatización.", "bot"),  # PROBLEMA: termina prematuramente
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
        
        print("\n--- ESTADO DESPUÉS DE LA CONVERSACIÓN ---")
        print(f"Nombre: {bot.collected_data['name']}")
        print(f"Email: {bot.collected_data['email']}")
        print(f"Teléfono: {bot.collected_data['phone']}")
        print(f"Servicio de interés: {bot.collected_data['service_interest']}")
        print(f"Demo confirmada: {bot.collected_data['demo_confirmed']}")
        print(f"Datos completos: {bot.collected_data['all_data_complete']}")
        
        print("\n--- ANALIZANDO EL PROBLEMA ---")
        
        # El problema es que la conversación termina sin:
        # 1. Pedir el número de teléfono
        # 2. Mostrar opciones de calendario
        
        telefono_solicitado = bot.collected_data['phone'] is not None
        print(f"¿Se solicitó teléfono? {'SÍ' if telefono_solicitado else 'NO'}")
        
        # Verificar si el ConversationGuard está interfiriendo
        respuesta_problematica = "¿Podrías proporcionarme tu número de teléfono para completar el agendamiento?"
        
        respuesta_corregida = guard.check_for_loops(
            respuesta_problematica, 
            "881",
            bot.conversation_log
        )
        
        print(f"Respuesta que debería generar: {respuesta_problematica}")
        print(f"Respuesta después de ConversationGuard: {respuesta_corregida}")
        
        guard_interfiere = respuesta_corregida != respuesta_problematica
        print(f"¿ConversationGuard interfiere? {'SÍ' if guard_interfiere else 'NO'}")
        
        # Verificar si debería mostrar opciones de calendario
        if telefono_solicitado:
            # Simular que el usuario proporciona teléfono
            bot.collected_data['phone'] = '3153041548'
            bot.collected_data['all_data_complete'] = True
            
            # Generar respuesta que debería mostrar calendario
            intent_result = type('Intent', (), {'category': 'tdx_service', 'industry': 'finanzas'})()
            service_result = {'service': 'AI_AUTOMATION', 'confidence': 0.8}
            
            respuesta_calendario = bot._generate_fallback_response("3153041548", intent_result, service_result)
            print(f"Respuesta con calendario: {respuesta_calendario[:150]}...")
            
            muestra_opciones = 'opción 1' in respuesta_calendario.lower() and 'opción 2' in respuesta_calendario.lower()
            print(f"¿Muestra opciones calendario? {'SÍ' if muestra_opciones else 'NO'}")
        
        # Evaluación del problema
        problemas_identificados = []
        
        if not telefono_solicitado:
            problemas_identificados.append("No se solicita número de teléfono")
        
        if guard_interfiere:
            problemas_identificados.append("ConversationGuard interfiere prematuramente")
        
        if bot.collected_data['all_data_complete'] and not telefono_solicitado:
            problemas_identificados.append("Datos marcados como completos sin teléfono")
        
        print(f"\n{'='*70}")
        print(f"DIAGNÓSTICO DEL PROBLEMA:")
        print(f"✅ Email detectado: {'PASS' if bot.collected_data['email'] and 'freddyrincones@gmail.com' in bot.collected_data['email'].lower() else 'FAIL'}")
        print(f"   Email actual: {bot.collected_data['email']}")
        print(f"❌ Teléfono solicitado: {'PASS' if telefono_solicitado else 'FAIL'}")
        print(f"❌ Flujo completo: {'PASS' if telefono_solicitado else 'FAIL'}")
        print(f"❌ ConversationGuard apropiado: {'PASS' if not guard_interfiere else 'FAIL'}")
        
        print(f"\nProblemas identificados:")
        for i, problema in enumerate(problemas_identificados, 1):
            print(f"{i}. {problema}")
        
        print(f"\nEstado: {'PROBLEMA IDENTIFICADO' if problemas_identificados else 'FUNCIONANDO'}")
        print(f"{'='*70}")
        
        return len(problemas_identificados) == 0
        
    except Exception as e:
        print(f"Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Ejecutando test del nuevo problema en producción...\n")
    
    success = test_new_production_issue()
    
    print(f"\n🎯 RESULTADO: {'✅ FUNCIONANDO CORRECTAMENTE' if success else '❌ PROBLEMA CONFIRMADO'}")
    
    if not success:
        print("\n⚠️  Se requiere corrección del ConversationGuard para evitar terminación prematura.")
        print("El bot debe continuar pidiendo teléfono y mostrar opciones de calendario.")
