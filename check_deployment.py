#!/usr/bin/env python3
"""
Script para verificar que el deployment de Render esté actualizado
"""

import requests
import time
import json

def check_deployment_status():
    """Verificar si Render tiene la versión correcta desplegada"""
    
    print("CHECKING RENDER DEPLOYMENT STATUS")
    print("=" * 50)
    
    # 1. Verificar health endpoint
    try:
        print("1. Checking general health...")
        health_response = requests.get("https://aivoicelivekitdemo.onrender.com/health", timeout=10)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"   ✅ General health: {health_data.get('status')}")
            print(f"   WhatsApp enabled: {health_data.get('integrations', {}).get('whatsapp_enabled')}")
        else:
            print(f"   ❌ Health check failed: {health_response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False
    
    # 2. Verificar WhatsApp health específico
    try:
        print("\n2. Checking WhatsApp health...")
        whatsapp_response = requests.get("https://aivoicelivekitdemo.onrender.com/health/whatsapp", timeout=10)
        if whatsapp_response.status_code == 200:
            print("   ✅ WhatsApp health endpoint exists")
        else:
            print(f"   ❌ WhatsApp health failed: {whatsapp_response.status_code}")
    except Exception as e:
        print(f"   ❌ WhatsApp health error: {e}")
    
    # 3. Test directo del webhook endpoint (debe devolver error de validación, no 404)
    try:
        print("\n3. Testing webhook endpoint...")
        webhook_url = "https://aivoicelivekitdemo.onrender.com/webhooks/whatsapp/test-token"
        
        # Payload mínimo para test
        test_payload = {"test": "endpoint"}
        
        webhook_response = requests.post(webhook_url, json=test_payload, timeout=10)
        
        if webhook_response.status_code == 404:
            print("   ❌ ENDPOINT NOT FOUND (404) - Render needs redeploy!")
            return False
        elif webhook_response.status_code in [401, 403, 400, 422, 500]:
            print(f"   ✅ Endpoint exists (got {webhook_response.status_code} - validation error, not 404)")
            return True
        else:
            print(f"   ✅ Endpoint responds: {webhook_response.status_code}")
            return True
            
    except Exception as e:
        print(f"   ❌ Webhook test error: {e}")
        return False

def wait_for_deployment():
    """Esperar hasta que el deployment esté listo"""
    
    print("\nWAITING FOR RENDER DEPLOYMENT...")
    print("=" * 50)
    print("Checking every 30 seconds...")
    print("Press Ctrl+C to stop")
    print()
    
    attempt = 1
    while True:
        try:
            print(f"Attempt {attempt}:")
            
            is_deployed = check_deployment_status()
            
            if is_deployed:
                print("\n🎉 SUCCESS! Deployment is ready!")
                print("\nNow test with WhatsApp:")
                print("Send message: 'quiero agendar'")
                print("Expected: Calendar availability options")
                break
            else:
                print(f"\n⏳ Still waiting... (attempt {attempt})")
                print("Next check in 30 seconds...")
                time.sleep(30)
                attempt += 1
                
        except KeyboardInterrupt:
            print("\n\n⚠️ Monitoring stopped by user")
            break
        except Exception as e:
            print(f"\n❌ Monitoring error: {e}")
            time.sleep(30)
            attempt += 1

def main():
    """Función principal"""
    print("RENDER DEPLOYMENT CHECKER")
    print("=" * 50)
    print("This script verifies that your homologated WhatsApp bot")
    print("is properly deployed on Render.")
    print()
    
    # Check actual status first
    current_status = check_deployment_status()
    
    if current_status:
        print("\n✅ DEPLOYMENT IS READY!")
        print("\nYour homologated WhatsApp bot should now work correctly.")
        print("\nTest it by sending: 'quiero agendar'")
    else:
        print("\n❌ DEPLOYMENT NOT READY")
        print("\nNEXT STEPS:")
        print("1. Go to https://dashboard.render.com")
        print("2. Find your 'aivoicelivekitdemo' service")
        print("3. Click 'Manual Deploy' → 'Deploy latest commit'")
        print("4. Wait for deployment to complete")
        print("5. Run this script again")
        print()
        
        choice = input("Do you want to wait and monitor for deployment? (y/n): ")
        if choice.lower() == 'y':
            wait_for_deployment()

if __name__ == "__main__":
    main()