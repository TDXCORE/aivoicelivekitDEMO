"""
Test para diagnosticar el problema del flujo de calendario
"""

import asyncio
import sys
import logging

# Add src to path
sys.path.append('src')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_calendar_debug")

async def test_calendar_flow_issue():
    """Simular el flujo exacto que está fallando"""
    print("\n🔧 DIAGNÓSTICO: Flujo de calendario no se activa")
    print("=" * 60)
    
    try:
        from src.agents.whatsapp_agent import TDXWhatsAppAgentClean
        
        # Crear agente con datos iniciales
        agent = TDXWhatsAppAgentClean(
            contact_name="Test User",
            company_name="Test Company", 
            prospect_info={},
            conversation_id=12345
        )
        
        # Simular el estado exacto del problema
        agent.collected_data = {
            'name': 'Test User',
            'email': 'freddyrincones@gmail.com',
            'phone': '3153041548',
            'company': 'Test Company',
            'service_interest': 'chatbot para un bufete de abogados',
            'budget_confirmed': True,
            'budget_declined': False,
            'budget_range': 'Presupuesto completo disponible',
            'budget_option_selected': '1',
            'budget_payment_type': 'full',
            'calendar_options_shown': False,  # ESTE ES EL PROBLEMA
            'selected_time_slot': None,
            'meeting_confirmed': False,
            'conversation_ended': False
        }
        
        print("📋 ESTADO ACTUAL DEL AGENTE:")
        for key, value in agent.collected_data.items():
            print(f"   {key}: {value}")
        
        # Verificar condiciones para mostrar calendario
        ready_for_calendar = all([
            agent.collected_data['email'],
            agent.collected_data['phone'], 
            agent.collected_data['service_interest'],
            agent.collected_data['budget_confirmed'],
            not agent.collected_data['calendar_options_shown']
        ])
        
        print(f"\n🔍 CONDICIONES PARA CALENDARIO:")
        print(f"   Email: {bool(agent.collected_data['email'])}")
        print(f"   Phone: {bool(agent.collected_data['phone'])}")
        print(f"   Service: {bool(agent.collected_data['service_interest'])}")
        print(f"   Budget: {agent.collected_data['budget_confirmed']}")
        print(f"   Calendar not shown: {not agent.collected_data['calendar_options_shown']}")
        print(f"   READY FOR CALENDAR: {ready_for_calendar}")
        
        # Determinar siguiente paso
        next_step = agent._determine_next_conversation_step()
        print(f"\n🎯 SIGUIENTE PASO: {next_step}")
        
        # Simular mensaje que debería activar calendario
        print(f"\n📱 SIMULANDO MENSAJE: '?'")
        response = await agent.process_message("?")
        print(f"🤖 RESPUESTA: {response}")
        
        # Verificar si se activó el calendario
        if agent.collected_data['calendar_options_shown']:
            print("✅ CALENDARIO ACTIVADO CORRECTAMENTE")
        else:
            print("❌ CALENDARIO NO SE ACTIVÓ - PROBLEMA DETECTADO")
            
            # Forzar activación manual para test
            print("\n🔧 FORZANDO ACTIVACIÓN MANUAL...")
            calendar_response = await agent._handle_show_calendar_options({
                'service_type': agent.collected_data['service_interest']
            })
            print(f"📅 RESPUESTA CALENDARIO: {calendar_response}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en diagnóstico: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Ejecutar diagnóstico"""
    print("🚀 INICIANDO DIAGNÓSTICO DE FLUJO DE CALENDARIO")
    
    success = await test_calendar_flow_issue()
    
    if success:
        print("\n✅ DIAGNÓSTICO COMPLETADO")
    else:
        print("\n❌ DIAGNÓSTICO FALLÓ")

if __name__ == "__main__":
    asyncio.run(main())
