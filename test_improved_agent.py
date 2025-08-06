"""
Test simple para verificar las mejoras del agente WhatsApp
"""
import asyncio
import sys
import os

# Add the src directory to the Python path
sys.path.append('src')

from testing.test_integration import TestAgentWrapper

async def test_improved_agent():
    print('TESTING AGENTE MEJORADO')
    print('=' * 50)
    
    # Crear wrapper de testing
    agent = TestAgentWrapper('TestUser', 'Test Company')
    
    # Test 1: Filtro de temas no relacionados
    print('\nTEST 1: Filtro de temas no relacionados')
    response = await agent.send_message('Como esta el clima hoy?')
    print(f'Usuario: Como esta el clima hoy?')
    print(f'Bot: {response}')
    
    # Reset para test limpio
    agent.reset_conversation()
    
    # Test 2: Flujo completo con base de conocimiento
    print('\nTEST 2: Flujo con base de conocimiento')
    
    # Paso 1: Solicitar servicio
    response = await agent.send_message('Necesito servicios de ai')
    print(f'Usuario: Necesito servicios de ai')
    print(f'Bot: {response}')
    
    # Paso 2: Responder volumen
    response = await agent.send_message('Como 100 usuarios')
    print(f'Usuario: Como 100 usuarios')
    print(f'Bot: {response}')
    
    # Paso 3: Confirmar presupuesto
    response = await agent.send_message('1')
    print(f'Usuario: 1')
    print(f'Bot: {response}')
    
    # Paso 4: Proporcionar email
    response = await agent.send_message('test@example.com')
    print(f'Usuario: test@example.com')
    print(f'Bot: {response}')
    
    # Paso 5: Proporcionar telefono
    response = await agent.send_message('3153041548')
    print(f'Usuario: 3153041548')
    print(f'Bot: {response}')
    
    # Paso 6: Seleccionar horario
    response = await agent.send_message('1')
    print(f'Usuario: 1')
    print(f'Bot: {response}')
    
    # Mostrar resumen final
    print('\nRESUMEN DEL TEST:')
    summary = agent.get_test_summary()
    print(f'Duracion: {summary["duration"]}')
    print(f'Mensajes totales: {summary["message_count"]}')
    print(f'Etapa final: {summary["conversation_stage"]}')
    print(f'Datos recopilados: {summary["data_collection_progress"]}')
    
    print('\nTEST COMPLETADO')

if __name__ == "__main__":
    asyncio.run(test_improved_agent())
