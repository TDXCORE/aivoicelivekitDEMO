#!/usr/bin/env python3
"""
Test script para verificar que el bot de WhatsApp funcione correctamente
"""

import os
import asyncio
import json
import logging
import requests
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("whatsapp-test")

# Cargar variables de entorno (simular el archivo .env)
os.environ.update({
    'VITE_CHATWOOT_ACCOUNT_ID': '126521',
    'VITE_CHATWOOT_API_TOKEN': 'PNwLGXoDiJ22QKd4AzX9Xxof',
    'CHATWOOT_WHATSAPP_INBOX_ID': '69481',
    'WHATSAPP_BOT_ENABLED': 'true'
})

def test_chatwoot_api():
    """Test básico de la API de Chatwoot"""
    logger.info("🧪 Testing Chatwoot API connection...")
    
    account_id = os.getenv('VITE_CHATWOOT_ACCOUNT_ID')
    api_token = os.getenv('VITE_CHATWOOT_API_TOKEN')
    
    headers = {
        'Content-Type': 'application/json',
        'api_access_token': api_token
    }
    
    # Test de conexión básica
    url = f"https://app.chatwoot.com/api/v1/accounts/{account_id}/conversations"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            logger.info("✅ Chatwoot API connection successful")
            data = response.json()
            logger.info(f"Found {len(data.get('data', {}).get('payload', []))} conversations")
            return True
        else:
            logger.error(f"❌ Chatwoot API error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error connecting to Chatwoot API: {e}")
        return False

def test_webhook_endpoint():
    """Test del endpoint de webhook de WhatsApp"""
    logger.info("🧪 Testing WhatsApp webhook endpoint...")
    
    webhook_token = 'f2H4MJcwQ8joe4IRheTZOQf5zCvpzi64N3QkMXc_PVs'
    webhook_url = f"https://aivoicelivekitdemo.onrender.com/webhooks/whatsapp/{webhook_token}"
    
    # Simular un webhook de Chatwoot
    test_webhook_data = {
        "event": "message_created",
        "message": {
            "id": 12345,
            "content": "hola",
            "message_type": "incoming",
            "created_at": datetime.now().isoformat(),
            "conversation_id": 98765
        },
        "conversation": {
            "id": 98765,
            "status": "open",
            "meta": {
                "sender": {
                    "id": 54321,
                    "name": "Usuario Test",
                    "phone_number": "+573001234567",
                    "email": "test@example.com"
                }
            }
        }
    }
    
    try:
        response = requests.post(webhook_url, json=test_webhook_data, timeout=30)
        
        logger.info(f"🔍 Webhook response status: {response.status_code}")
        logger.info(f"🔍 Webhook response: {response.text}")
        
        if response.status_code == 200:
            logger.info("✅ Webhook endpoint responded successfully")
            return True
        else:
            logger.error(f"❌ Webhook endpoint error: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error calling webhook endpoint: {e}")
        return False

async def test_whatsapp_agent():
    """Test directo del agente de WhatsApp"""
    logger.info("🧪 Testing WhatsApp agent directly...")
    
    try:
        # Importar el agente
        from src.agents.whatsapp_agent import TDXWhatsAppAgentV2
        
        # Crear instancia del agente
        agent = TDXWhatsAppAgentV2(
            contact_name="Usuario Test",
            company_name="Empresa Test",
            prospect_info={
                'email': 'test@example.com',
                'phone': '+573001234567',
                'source': 'whatsapp',
                'chatwoot_id': 54321,
                'company_name': 'Empresa Test',
                'contact_name': 'Usuario Test'
            },
            conversation_id=98765
        )
        
        # Test de generación de respuesta
        response = await agent._generate_response("hola")
        
        if response:
            logger.info(f"✅ Agent generated response: {response[:100]}...")
            return True
        else:
            logger.error("❌ Agent failed to generate response")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing WhatsApp agent: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return False

async def run_all_tests():
    """Ejecutar todos los tests"""
    logger.info("🚀 Starting WhatsApp Bot Tests...")
    
    results = {
        'chatwoot_api': test_chatwoot_api(),
        'whatsapp_agent': await test_whatsapp_agent(),
        'webhook_endpoint': test_webhook_endpoint()
    }
    
    logger.info("\n📊 TEST RESULTS:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n🎉 ALL TESTS PASSED! The WhatsApp bot should be working correctly.")
    else:
        logger.info("\n⚠️ SOME TESTS FAILED. Check the logs above for details.")
    
    return all_passed

if __name__ == "__main__":
    # Ejecutar tests
    asyncio.run(run_all_tests())