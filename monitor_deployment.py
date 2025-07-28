#!/usr/bin/env python3
"""
Monitor deployment status - Windows compatible version
"""

import requests
import time
from datetime import datetime

def check_endpoint():
    """Check if endpoint is working"""
    try:
        response = requests.post("https://aivoicelivekitdemo.onrender.com/webhooks/whatsapp/test", 
                               json={"test": True}, timeout=10)
        return response.status_code != 404
    except:
        return False

def main():
    print("MONITORING RENDER DEPLOYMENT")
    print("=" * 40)
    print("Waiting for WhatsApp webhook endpoint to become available...")
    print("Checking every 30 seconds...")
    print()
    
    attempt = 1
    while True:
        try:
            current_time = datetime.now().strftime('%H:%M:%S')
            is_working = check_endpoint()
            
            if is_working:
                print(f"{current_time} - SUCCESS! Endpoint is now working!")
                print("Your homologated WhatsApp bot is ready!")
                print()
                print("Test with WhatsApp message: 'quiero agendar'")
                break
            else:
                print(f"{current_time} - Still waiting... (attempt {attempt})")
                time.sleep(30)
                attempt += 1
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()