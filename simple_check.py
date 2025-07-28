#!/usr/bin/env python3
"""
Check simple del estado sin emojis para Windows
"""

import requests

def simple_check():
    print("SIMPLE DEPLOYMENT CHECK")
    print("=" * 40)
    
    # 1. Health check
    try:
        response = requests.get("https://aivoicelivekitdemo.onrender.com/health", timeout=10)
        print(f"Health status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"WhatsApp enabled: {data.get('integrations', {}).get('whatsapp_enabled')}")
    except Exception as e:
        print(f"Health error: {e}")
    
    # 2. Webhook check
    try:
        response = requests.post("https://aivoicelivekitdemo.onrender.com/webhooks/whatsapp/test", 
                               json={"test": True}, timeout=10)
        print(f"Webhook status: {response.status_code}")
        
        if response.status_code == 404:
            print("PROBLEM: Endpoint not found - Render needs redeploy")
        else:
            print("SUCCESS: Endpoint exists (may return validation error, but not 404)")
            
    except Exception as e:
        print(f"Webhook error: {e}")
    
    print("\nNEXT STEPS:")
    if response.status_code == 404:
        print("1. Go to https://dashboard.render.com")
        print("2. Find 'aivoicelivekitdemo' service")  
        print("3. Click 'Manual Deploy' button")
        print("4. Select 'Deploy latest commit'")
        print("5. Wait for deployment to complete (5-10 minutes)")
        print("6. Run this script again")
    else:
        print("1. Test WhatsApp message: 'quiero agendar'")
        print("2. Should get calendar availability")

if __name__ == "__main__":
    simple_check()