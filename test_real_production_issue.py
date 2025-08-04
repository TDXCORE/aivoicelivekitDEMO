#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de la conversación REAL de producción que está fallando
Reproducir exactamente lo que pasó el 4 de agosto a las 5:33 PM
"""

import sys
from datetime import datetime

# Agregar la ruta del proyecto
sys.path.append('.')

def test_real_production_issue():
    """Test de la conversación real que está fallando"""
    try:
        from src.agents.whatsapp_agent import TDXWhatsAppAgentV2
        
        print("=== TEST CONVERSACIÓN REAL DE PRODUCCIÓN ===")
        print("4 de agosto 2025, 5:33-5:34 PM")
        print()
        
        # Crear instancia del bot
        bot = TDXWhatsAppAgentV2(
            contact_name="Freddy Rincones",
            company_name="Su empresa",
            prospect_info={'email': None, 'phone': None},
            conversation_id=884
        )
        
        # Conversación EXACTA que falló en producción
        conversation_steps = [
            ("eoale", "user"),
            ("¡Hola Freddy! ¿En qué puedo ayudarte hoy? 😊", "bot"),
            ("quiero AI", "user"),
            ("¡Perfecto, Freddy! En TDX ofrecemos soluciones de IA para mejorar la eficiencia de tu empresa. ¿En qué área específica te gustaría implementar la inteligencia artificial? 😉", "bot"),
            ("automatizacion para mi area de finanzas", "user"),
            ("¡Excelente elección, Freddy! Con nuestra solución de IA, automatizaremos procesos en tu área de finanzas para aumentar la eficiencia. ¿Podemos agendar una llamada para discutir más detalles? 🚀", "bot"),
            ("si claro agendemos", "user"),
            ("¡Perfecto, Freddy! Para agendar la llamada, necesito tu nombre y dirección de correo electrónico. ¿Podrías proporcionármelos por favor? 😉", "bot"),
            ("freddy, freddyrincones@gmail.com", "user"),
            ("¡Gracias, Freddy! ¿Cuál es tu nombre completo y número de teléfono para completar la información de agendamiento? 📝📞", "bot"),  # PROBLEMA: Ya tenía el email pero lo "olvidó"
            ("freddy rincones 3153041548", "user"),
            ("¡Gracias, Freddy! ¿Podrías proporcionarme tu dirección de correo electrónico para completar el agendamiento? 📧", "bot"),  # PROBLEMA: Vuelve a pedir email que ya tenía
            ("Freddyrincones@gmail.com", "user"),
            ("¡Perfecto! Ya tengo todos tus datos. Te contactaremos pronto para agendar la demo. ¡Gracias por tu interés!", "bot")  # PROBLEMA: No muestra opciones de calendario
        ]
        
        print("--- REPRODUCIENDO CONVERSACIÓN EXACTA ---")
        
        # Simular la conversación paso a paso
        for i, (message, sender) in enumerate(conversation_steps):
            print(f"[{i+1:2d}] {sender.upper()}: {message}")
            
            if sender == "user":
                # Actualizar datos del usuario
                print(f"    ANTES: email={bot.collected_data['email']}, phone={bot.collected_data['phone']}")
                bot._update_collected_data(message)
                print(f"    DESPUÉS: email={bot.collected_data['email']}, phone={bot.collected_data['phone']}")
                
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
        
        print("\n--- ANÁLISIS DEL PROBLEMA ---")
        print(f"Estado final:")
        print(f"  Email: {bot.collected_data['email']}")
        print(f"  Teléfono: {bot.collected_data['phone']}")
        print(f"  Nombre: {bot.collected_data['name']}")
        print(f"  Servicio: {bot.collected_data['service_interest']}")
        print(f"  Datos completos: {bot.collected_data['all_data_complete']}")
        print(f"  Opciones mostradas: {bot.collected_data['calendar_options_shown']}")
        
        # Identificar problemas específicos
        problemas = []
        
        # Problema 1: Email se "perdió" entre mensajes 8 y 10
        if bot.collected_data['email']:
            print(f"\n✅ Email detectado correctamente: {bot.collected_data['email']}")
        else:
            problemas.append("Email no detectado")
        
        # Problema 2: Teléfono se detectó
        if bot.collected_data['phone']:
            print(f"✅ Teléfono detectado correctamente: {bot.collected_data['phone']}")
        else:
            problemas.append("Teléfono no detectado")
        
        # Problema 3: No se mostraron opciones de calendario
        if not bot.collected_data['calendar_options_shown']:
            problemas.append("No se mostraron opciones de calendario")
        
        # Problema 4: Datos completos pero no se activó el flujo
        if bot.collected_data['email'] and bot.collected_data['phone'] and not bot.collected_data['all_data_complete']:
            problemas.append("Datos completos pero all_data_complete = False")
        
        print(f"\n{'='*60}")
        print("PROBLEMAS IDENTIFICADOS:")
        for i, problema in enumerate(problemas, 1):
            print(f"{i}. {problema}")
        
        print(f"\nESTADO: {'❌ PROBLEMA CONFIRMADO' if problemas else '✅ FUNCIONANDO'}")
        print(f"{'='*60}")
        
        return len(problemas) == 0
        
    except Exception as e:
        print(f"Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Ejecutando test de conversación real de producción...\n")
    
    success = test_real_production_issue()
    
    print(f"\n🎯 RESULTADO: {'✅ FUNCIONANDO CORRECTAMENTE' if success else '❌ PROBLEMA CONFIRMADO'}")
