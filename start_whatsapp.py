#!/usr/bin/env python3
"""
WhatsApp Bot Service Launcher
Inicia el servicio de WhatsApp bot que incluye el webhook receiver extendido
"""

import asyncio
import uvicorn
import os
import sys
import logging
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import aiohttp
import openai

# Cargar variables de entorno
load_dotenv(dotenv_path=".env.local")

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("whatsapp-service")

# Global clients para reutilización
http_session: aiohttp.ClientSession = None
openai_client: openai.AsyncOpenAI = None

@asynccontextmanager
async def lifespan(app):
    """Lifespan management para conexiones persistentes"""
    global http_session, openai_client
    
    logger.info("🚀 Starting WhatsApp Bot Service...")
    
    # Validar variables de entorno críticas
    required_vars = [
        'CHATWOOT_ACCOUNT_ID',
        'CHATWOOT_API_TOKEN', 
        'CHATWOOT_BOT_WEBHOOK_TOKEN',
        'OPENAI_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {missing_vars}")
        logger.error("Please configure these variables in .env.local")
        sys.exit(1)
    
    # Startup - crear clients globales
    try:
        http_session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=100, limit_per_host=30)
        )
        
        openai_client = openai.AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Hacer disponibles globalmente para los módulos
        import __main__
        __main__.http_session = http_session
        __main__.openai_client = openai_client
        
        logger.info("✅ Global clients initialized successfully")
        
        # Validar conexión a Chatwoot
        try:
            from whatsapp_security import WhatsAppWebhookSecurity
            security = WhatsAppWebhookSecurity()
            if not security.validate_environment():
                logger.error("❌ Chatwoot environment validation failed")
                sys.exit(1)
            logger.info("✅ Chatwoot environment validated")
        except Exception as e:
            logger.error(f"❌ Failed to validate environment: {e}")
            sys.exit(1)
        
        # Verificar que WhatsApp está habilitado
        whatsapp_enabled = os.getenv('WHATSAPP_BOT_ENABLED', 'false').lower() == 'true'
        if not whatsapp_enabled:
            logger.warning("⚠️ WhatsApp bot is disabled. Set WHATSAPP_BOT_ENABLED=true to enable")
        else:
            logger.info("✅ WhatsApp bot service enabled")
        
        logger.info("🎯 WhatsApp Bot Service ready to accept connections")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize service: {e}")
        sys.exit(1)
    
    yield
    
    # Shutdown - cleanup
    logger.info("🔄 Shutting down WhatsApp Bot Service...")
    try:
        if http_session:
            await http_session.close()
        logger.info("✅ Global clients cleaned up successfully")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

async def start_whatsapp_service():
    """Iniciar el servicio WhatsApp con el webhook receiver extendido"""
    
    # Importar la app extendida que incluye endpoints de WhatsApp
    from webhook_receiver import app
    
    # Configurar lifespan
    app.router.lifespan_context = lifespan
    
    port = int(os.getenv('PORT', 8000))
    host = os.getenv('HOST', '0.0.0.0')
    
    logger.info(f"🌐 WhatsApp Bot Service starting on {host}:{port}")
    logger.info(f"📱 WhatsApp webhook: http://{host}:{port}/webhooks/whatsapp/<token>")
    logger.info(f"🔍 Voice webhook: http://{host}:{port}/webhooks/chatwoot/<token>")
    logger.info(f"💚 Health check: http://{host}:{port}/health")
    logger.info(f"📊 WhatsApp health: http://{host}:{port}/health/whatsapp")
    logger.info(f"📈 WhatsApp metrics: http://{host}:{port}/admin/whatsapp/metrics")
    
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level="info",
        access_log=True,
        lifespan="on"
    )
    
    server = uvicorn.Server(config)
    await server.serve()

def main():
    """Función principal"""
    try:
        # Verificar Python version
        if sys.version_info < (3, 8):
            logger.error("❌ Python 3.8+ required")
            sys.exit(1)
        
        # Verificar que los módulos de WhatsApp están disponibles
        try:
            import whatsapp_bot
            import whatsapp_client
            import whatsapp_security
            import whatsapp_webhook
            import whatsapp_metrics
            logger.info("✅ All WhatsApp modules loaded successfully")
        except ImportError as e:
            logger.error(f"❌ Failed to import WhatsApp modules: {e}")
            logger.error("Please ensure all WhatsApp bot files are present")
            sys.exit(1)
        
        # Iniciar servicio
        logger.info("🎬 Launching WhatsApp Bot Service...")
        asyncio.run(start_whatsapp_service())
        
    except KeyboardInterrupt:
        logger.info("👋 WhatsApp Bot Service stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()