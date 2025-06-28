#!/usr/bin/env python3
"""
Test script for Microsoft Graph integration
"""
import asyncio
import os
from dotenv import load_dotenv
from microsoft_graph_client import graph_client

load_dotenv(dotenv_path=".env.local")

async def test_graph_integration():
    """Test Microsoft Graph API integration"""
    
    print("🧪 Testing Microsoft Graph Integration")
    print("=" * 50)
    
    # Check environment variables
    print("\n1. Checking Environment Variables:")
    client_id = os.getenv("MICROSOFT_GRAPH_CLIENT_ID")
    client_secret = os.getenv("MICROSOFT_GRAPH_CLIENT_SECRET")
    tenant_id = os.getenv("MICROSOFT_GRAPH_TENANT_ID")
    
    print(f"   MICROSOFT_GRAPH_CLIENT_ID: {'✅ Set' if client_id else '❌ Missing'}")
    print(f"   MICROSOFT_GRAPH_CLIENT_SECRET: {'✅ Set' if client_secret else '❌ Missing'}")
    print(f"   MICROSOFT_GRAPH_TENANT_ID: {'✅ Set' if tenant_id else '❌ Missing'}")
    
    if not all([client_id, client_secret, tenant_id]):
        print("\n⚠️  Microsoft Graph credentials not found in environment.")
        print("   The system will use mock data for testing.")
        print("   In production, ensure these variables are set:")
        print("   - MICROSOFT_GRAPH_CLIENT_ID")
        print("   - MICROSOFT_GRAPH_CLIENT_SECRET") 
        print("   - MICROSOFT_GRAPH_TENANT_ID")
    
    # Test availability checking
    print("\n2. Testing Availability Checking:")
    try:
        from datetime import datetime, timedelta
        start_date = datetime.now() + timedelta(days=1)
        end_date = start_date + timedelta(days=7)
        
        availability = await graph_client.check_availability(start_date, end_date)
        print(f"   ✅ Availability check successful")
        print(f"   📅 Found {len(availability)} available slots:")
        
        for i, slot in enumerate(availability, 1):
            print(f"      {i}. {slot['formatted']}")
    
    except Exception as e:
        print(f"   ❌ Availability check failed: {e}")
    
    # Test meeting creation
    print("\n3. Testing Meeting Creation:")
    try:
        result = await graph_client.create_meeting(
            attendee_email="test@example.com",
            meeting_date="2024-01-15",
            meeting_time="2:00 PM",
            contact_name="Test Contact",
            company_name="Test Company"
        )
        
        print(f"   ✅ Meeting creation successful")
        print(f"   🆔 Meeting ID: {result.get('meeting_id', 'N/A')}")
        print(f"   📧 Attendee: {result.get('attendee_email', 'N/A')}")
        print(f"   📅 Date: {result.get('meeting_date', 'N/A')}")
        print(f"   🕐 Time: {result.get('meeting_time', 'N/A')}")
        print(f"   🔗 Teams Link: {result.get('meeting_link', 'N/A')}")
        
        if result.get('fallback_used'):
            print("   ⚠️  Note: Used fallback mock data (Graph API not available)")
    
    except Exception as e:
        print(f"   ❌ Meeting creation failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Integration test completed!")
    
    if all([client_id, client_secret, tenant_id]):
        print("✅ All credentials are set - should work with real Microsoft Graph API")
    else:
        print("⚠️  Missing credentials - currently using mock data")
        print("   Set the Microsoft Graph environment variables for full functionality")

if __name__ == "__main__":
    asyncio.run(test_graph_integration())