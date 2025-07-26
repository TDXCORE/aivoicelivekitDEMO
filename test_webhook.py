#!/usr/bin/env python3
"""
Test directo del webhook de WhatsApp en producción
"""

import requests
import json

def test_webhook():
    """Test del webhook de WhatsApp en producción"""
    
    # URL exacta de tu webhook
    webhook_url = "https://aivoicelivekitdemo.onrender.com/webhooks/whatsapp/f2H4MJcwQ8joe4IRheTZOQf5zCvpzi64N3QkMXc_PVs"
    
    # Payload de test simulando mensaje de Chatwoot
    test_payload = {
        "event": "message_created",
        "conversation": {
            "id": 12345,
            "status": "pending"
        },
        "message": {
            "content": "quiero agendar",
            "message_type": "incoming"
        },
        "contact": {
            "id": 67890,
            "name": "Test User",
            "phone_number": "+1234567890",
            "email": "test@example.com"
        },
        "account": {
            "id": 1
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Chatwoot/1.0"
    }
    
    print("TESTING WEBHOOK ENDPOINT")
    print("=" * 40)
    print(f"URL: {webhook_url}")
    print(f"Payload: {json.dumps(test_payload, indent=2)}")
    print()
    
    try:
        response = requests.post(
            webhook_url,
            json=test_payload,
            headers=headers,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("\nSUCCESS: Webhook responded correctly")
            try:
                response_json = response.json()
                print(f"Parsed Response: {json.dumps(response_json, indent=2)}")
            except:
                print("Response is not JSON")
        else:
            print(f"\nERROR: Webhook returned status {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("ERROR: Request timed out")
    except requests.exceptions.ConnectionError:
        print("ERROR: Connection failed")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_webhook()