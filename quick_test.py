#!/usr/bin/env python3
"""
Test rápido del WhatsApp Bot - Sin emojis para Windows
"""

import os
from datetime import datetime

def check_basic_config():
    """Verificación básica de configuración"""
    print("QUICK BOT TEST")
    print("=" * 40)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Verificar archivo .env.local
    env_file = ".env.local"
    if os.path.exists(env_file):
        print("PASS: .env.local file exists")
    else:
        print("FAIL: .env.local file missing")
        print("Solution: Copy .env.example to .env.local and configure")
        return False
    
    # Verificar variables críticas
    critical_vars = [
        'VITE_CHATWOOT_ACCOUNT_ID',
        'VITE_CHATWOOT_API_TOKEN', 
        'OPENAI_API_KEY'
    ]
    
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=".env.local")
    
    missing = []
    for var in critical_vars:
        value = os.getenv(var)
        if not value or value == f"YOUR_{var.split('_')[-1]}_HERE":
            missing.append(var)
        else:
            print(f"PASS: {var} configured")
    
    if missing:
        print(f"FAIL: Missing variables: {missing}")
        print()
        print("NEXT STEPS:")
        print("1. Edit .env.local file")
        print("2. Replace placeholder values with real credentials")
        print("3. Run this test again")
        return False
    
    return True

def test_keyword_logic():
    """Test básico de lógica de keywords"""
    print("\nKEYWORD DETECTION TEST")
    print("=" * 40)
    
    # Schedule keywords
    schedule_keywords = ["agendar", "reunion", "cita", "disponibilidad"]
    transfer_keywords = ["ejecutivo", "humano", "vendedor", "agente"]
    
    test_messages = [
        ("quiero agendar", "schedule"),
        ("necesito una reunion", "schedule"),
        ("quiero hablar con un ejecutivo", "transfer"),
        ("hola", "none")
    ]
    
    for message, expected in test_messages:
        message_lower = message.lower()
        
        is_schedule = any(kw in message_lower for kw in schedule_keywords)
        is_transfer = any(kw in message_lower for kw in transfer_keywords)
        
        if is_schedule:
            detected = "schedule"
        elif is_transfer:
            detected = "transfer"
        else:
            detected = "none"
        
        status = "PASS" if detected == expected else "FAIL"
        print(f"{status}: '{message}' -> {detected}")
    
    return True

def show_instructions():
    """Mostrar instrucciones para continuar"""
    print("\nNEXT STEPS TO TEST THE BOT:")
    print("=" * 40)
    print("1. Configure .env.local with your real credentials")
    print("2. Start the server: python webhook_receiver.py")
    print("3. Send WhatsApp message: 'quiero agendar'")
    print("4. Bot should respond with calendar availability")
    print()
    print("EXPECTED BEHAVIOR:")
    print("- 'quiero agendar' -> Shows calendar options")
    print("- 'quiero hablar con ejecutivo' -> Transfers to human")
    print("- 'hola' -> Aggressive sales greeting")

def main():
    """Función principal"""
    try:
        config_ok = check_basic_config()
        test_keyword_logic()
        
        if config_ok:
            print("\nSUMMARY: Configuration looks good!")
            print("The bot should work correctly now.")
        else:
            print("\nSUMMARY: Configuration needed!")
            print("Please configure .env.local first.")
        
        show_instructions()
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you're in the correct directory with all files.")

if __name__ == "__main__":
    main()