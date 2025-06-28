#!/usr/bin/env python3
"""
Startup script that verifies dependencies before starting the agent
"""
import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_graph_sdk():
    """Verify Microsoft Graph SDK is available"""
    try:
        from msgraph import GraphServiceClient
        from azure.identity import ClientSecretCredential
        logger.info("✅ Microsoft Graph SDK verified successfully")
        return True
    except ImportError as e:
        logger.error(f"❌ Microsoft Graph SDK not available: {e}")
        logger.error("This means calendar integration will use mock data")
        return False

def check_environment_variables():
    """Check if production environment variables are set"""
    graph_vars = [
        "MICROSOFT_GRAPH_CLIENT_ID",
        "MICROSOFT_GRAPH_CLIENT_SECRET", 
        "MICROSOFT_GRAPH_TENANT_ID"
    ]
    
    missing_vars = [var for var in graph_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {missing_vars}")
        logger.warning("Calendar integration will use mock data")
        return False
    else:
        logger.info("✅ All Microsoft Graph environment variables found")
        return True

def main():
    """Main startup function"""
    logger.info("🚀 Starting TDX SDR Agent...")
    
    # Check dependencies
    graph_available = verify_graph_sdk()
    env_vars_available = check_environment_variables()
    
    if graph_available and env_vars_available:
        logger.info("🎯 PRODUCTION MODE: Real Microsoft Graph API will be used")
    else:
        logger.info("🧪 DEVELOPMENT MODE: Mock data will be used for calendar features")
    
    # Start the actual agent
    logger.info("Starting agent.py...")
    
    try:
        # Import and run the agent
        from agent import cli, WorkerOptions, entrypoint
        cli.run_app(
            WorkerOptions(
                entrypoint_fnc=entrypoint,
                agent_name="tdx-sdr-bot",
            )
        )
    except Exception as e:
        logger.error(f"❌ Failed to start agent: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()