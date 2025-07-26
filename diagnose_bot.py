#!/usr/bin/env python3
"""
Script de diagnóstico para el WhatsApp Bot
Verifica configuración y funcionalidad paso a paso
"""

import os
import sys
import json
from datetime import datetime

def check_environment():
    """Verificar variables de entorno críticas"""
    print("CHECKING ENVIRONMENT VARIABLES")
    print("=" * 50)
    
    critical_vars = [
        'VITE_CHATWOOT_ACCOUNT_ID',
        'VITE_CHATWOOT_API_TOKEN',
        'OPENAI_API_KEY',
        'CHATWOOT_BOT_AGENT_ID',
        'CHATWOOT_WHATSAPP_INBOX_ID'
    ]
    
    optional_vars = [
        'WHATSAPP_BOT_ENABLED',
        'WHATSAPP_AGGRESSIVE_MODE',
        'WHATSAPP_RATE_LIMIT_SECONDS',
        'USE_TELNYX_INSTEAD_OF_LIVEKIT'
    ]
    
    missing_critical = []
    
    print("CRITICAL VARIABLES:")
    for var in critical_vars:
        value = os.getenv(var)
        if value:
            # Show first 10 chars for security
            display_value = value[:10] + "..." if len(value) > 10 else value
            print(f"  {var}: {display_value}")
        else:
            print(f"  {var}: MISSING")
            missing_critical.append(var)
    
    print("\nOPTIONAL VARIABLES:")
    for var in optional_vars:
        value = os.getenv(var)
        print(f"  {var}: {value or 'NOT SET'}")
    
    if missing_critical:
        print(f"\n❌ MISSING CRITICAL VARIABLES: {missing_critical}")
        return False
    else:
        print("\n✅ All critical variables are configured")
        return True

def test_imports():
    """Verificar que todas las dependencias se puedan importar"""
    print("\nTESTING IMPORTS")
    print("=" * 50)
    
    imports_to_test = [
        ('openai', 'OpenAI API'),
        ('fastapi', 'FastAPI framework'),
        ('aiohttp', 'Async HTTP client'),
        ('whatsapp_bot', 'WhatsApp Bot module'),
        ('whatsapp_client', 'WhatsApp Client module'),
        ('microsoft_graph_client', 'Microsoft Graph client')
    ]
    
    failed_imports = []
    
    for module_name, description in imports_to_test:
        try:
            __import__(module_name)
            print(f"  ✅ {description}: OK")
        except ImportError as e:
            print(f"  ❌ {description}: FAILED - {e}")
            failed_imports.append(module_name)
    
    if failed_imports:
        print(f"\n❌ FAILED IMPORTS: {failed_imports}")
        return False
    else:
        print("\n✅ All imports successful")
        return True

def test_bot_creation():
    """Verificar que se pueda crear una instancia del bot"""
    print("\nTESTING BOT CREATION")
    print("=" * 50)
    
    try:
        from whatsapp_bot import TDXWhatsAppBot
        
        # Datos de prueba
        bot = TDXWhatsAppBot(
            contact_name="Test User",
            company_name="Test Company",
            prospect_info={
                'email': 'test@example.com',
                'phone': '+1234567890',
                'source': 'test'
            },
            conversation_id=99999
        )
        
        print("  ✅ Bot instance created successfully")
        
        # Verificar herramientas
        tools = bot.get_whatsapp_tools()
        print(f"  ✅ Tools configured: {len(tools)}")
        
        tool_names = [tool['function']['name'] for tool in tools]
        expected_tools = [
            'schedule_meeting_whatsapp',
            'check_availability_whatsapp',
            'transfer_to_human_whatsapp', 
            'collect_email_whatsapp',
            'qualify_prospect_whatsapp'
        ]
        
        missing_tools = [tool for tool in expected_tools if tool not in tool_names]
        if missing_tools:
            print(f"  ❌ Missing tools: {missing_tools}")
            return False
        else:
            print("  ✅ All expected tools present")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Bot creation failed: {e}")
        return False

def test_keyword_detection():
    """Verificar detección de keywords"""
    print("\nTESTING KEYWORD DETECTION")
    print("=" * 50)
    
    try:
        from whatsapp_bot import TDXWhatsAppBot
        
        bot = TDXWhatsAppBot(
            contact_name="Test User",
            company_name="Test Company", 
            prospect_info={'email': 'test@test.com'},
            conversation_id=99999
        )
        
        # Test cases
        test_cases = [
            ("quiero agendar", "schedule", True),
            ("necesito una reunion", "schedule", True),
            ("quiero hablar con un ejecutivo", "transfer", True),
            ("necesito un humano", "transfer", True),
            ("hola como estas", "none", False)
        ]
        
        print("  Testing schedule keyword detection:")
        for message, expected_type, should_detect in test_cases:
            if expected_type == "schedule":
                # Simulate schedule detection logic
                SCHEDULE_KEYWORDS = [
                    "agendar", "agenda", "agendo", "programar", "programa",
                    "reunion", "cita", "meeting", "encuentro",
                    "disponibilidad", "horario", "hora", "cuando",
                    "reservar", "apartar", "calendario", "fecha"
                ]
                
                message_lower = message.lower()
                detected = any(keyword in message_lower for keyword in SCHEDULE_KEYWORDS)
                
                if detected == should_detect:
                    print(f"    ✅ '{message}' -> {detected}")
                else:
                    print(f"    ❌ '{message}' -> {detected} (expected {should_detect})")
        
        print("  Testing transfer keyword detection:")
        for message, expected_type, should_detect in test_cases:
            if expected_type == "transfer":
                # Simulate transfer detection logic
                TRANSFER_KEYWORDS = [
                    "ejecutivo", "vendedor", "asesor", "consultor", "especialista",
                    "hablar con alguien", "persona real", "humano", "representante", "agente",
                    "gerente", "director", "supervisor", "jefe",
                    "experto", "tecnico", "ingeniero",
                    "quiero hablar con", "me conecta con", "transfiere", "transferir",
                    "no quiero bot", "quiero persona", "alguien mas"
                ]
                
                message_lower = message.lower()
                detected = any(keyword in message_lower for keyword in TRANSFER_KEYWORDS)
                
                if detected == should_detect:
                    print(f"    ✅ '{message}' -> {detected}")
                else:
                    print(f"    ❌ '{message}' -> {detected} (expected {should_detect})")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Keyword detection test failed: {e}")
        return False

def main():
    """Función principal de diagnóstico"""
    print("WHATSAPP BOT DIAGNOSTIC TOOL")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Ejecutar todas las verificaciones
    checks = [
        ("Environment Variables", check_environment),
        ("Module Imports", test_imports),
        ("Bot Creation", test_bot_creation),
        ("Keyword Detection", test_keyword_detection)
    ]
    
    results = {}
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results[check_name] = result
        except Exception as e:
            print(f"Error in {check_name}: {e}")
            results[check_name] = False
    
    # Resumen final
    print("\nDIAGNOSTIC SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for check_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name}: {status}")
        if not result:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 ALL CHECKS PASSED - Bot should work correctly")
        print("\nNext steps:")
        print("1. Start webhook receiver: python webhook_receiver.py")
        print("2. Test with WhatsApp message: 'quiero agendar'")
        print("3. Check logs for automatic keyword detection")
    else:
        print("⚠️  SOME CHECKS FAILED - Review issues above")
        print("\nCommon solutions:")
        print("1. Set missing environment variables in .env.local")
        print("2. Install missing dependencies: pip install -r requirements.txt")
        print("3. Check file permissions and paths")

if __name__ == "__main__":
    main()