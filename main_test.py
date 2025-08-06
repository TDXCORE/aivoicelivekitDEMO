#!/usr/bin/env python3
"""
TDX Chatbot Test Server
Servidor independiente para testing del chatbot sin afectar producción
"""

import sys
import os
import logging
import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import test router
from testing.test_router import test_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_server.log')
    ]
)

logger = logging.getLogger("test-server")

# Create FastAPI test application
app = FastAPI(
    title="TDX Chatbot Test Server",
    description="Servidor de pruebas para el chatbot TDX WhatsApp Agent",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS - secure for production, permissive for development
is_render = os.getenv("RENDER") == "production"

if is_render:
    # Production CORS - secure configuration
    allowed_origins = [
        "https://aivoicelivekitdemo-testing.onrender.com",
        "https://*.onrender.com",
        "https://localhost:3000",  # For potential frontend deployments
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
    logger.info(f"🔒 CORS configured for production with origins: {allowed_origins}")
else:
    # Development CORS - permissive for testing
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for local testing
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("🔓 CORS configured for development (permissive)")

# Include test router
app.include_router(test_router)

# Serve static files (frontend)
try:
    frontend_path = os.path.join(os.path.dirname(__file__), "testing", "frontend")
    if os.path.exists(frontend_path):
        app.mount("/static", StaticFiles(directory=frontend_path), name="static")
        logger.info(f"✅ Frontend mounted from: {frontend_path}")
    else:
        logger.warning(f"⚠️ Frontend directory not found: {frontend_path}")
except Exception as e:
    logger.error(f"❌ Error mounting static files: {e}")

# Root endpoint - serve the main interface
@app.get("/")
async def serve_frontend():
    """Serve the main test interface"""
    try:
        frontend_file = os.path.join(os.path.dirname(__file__), "testing", "frontend", "index.html")
        if os.path.exists(frontend_file):
            return FileResponse(frontend_file)
        else:
            return {"message": "TDX Chatbot Test Server", "status": "Frontend not found", "docs": "/docs"}
    except Exception as e:
        logger.error(f"Error serving frontend: {e}")
        return {"message": "TDX Chatbot Test Server", "error": str(e), "docs": "/docs"}

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check for the test server"""
    return {
        "status": "healthy",
        "service": "TDX Chatbot Test Server",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/api/test/chat",
            "reset": "/api/test/reset",
            "status": "/api/test/status",
            "frontend": "/",
            "docs": "/docs"
        }
    }

# Server info endpoint
@app.get("/info")
async def server_info():
    """Get server information"""
    return {
        "server": "TDX Chatbot Test Server",
        "version": "1.0.0",
        "description": "Servidor independiente para testing del chatbot TDX",
        "features": [
            "Chat interface estilo ChatGPT",
            "Mismo agente que producción",
            "Reset completo de conversaciones",
            "Exportación de datos de prueba",
            "Aislamiento total de Chatwoot"
        ],
        "endpoints": {
            "test_api": "/api/test/",
            "frontend": "/",
            "health": "/health",
            "docs": "/docs",
            "redoc": "/redoc"
        },
        "usage": {
            "frontend": "Abrir / en el navegador para la interfaz de chat",
            "api": "Usar /api/test/ para llamadas programáticas",
            "reset": "POST /api/test/reset para reiniciar conversación"
        }
    }

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests for debugging"""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    
    return response

# Import time for middleware
import time

if __name__ == "__main__":
    # Render-compatible port and host configuration
    # Use environment variable PORT (provided by Render) or fallback to 8001 for local development
    test_port = int(os.getenv("PORT", "8001"))
    
    # Use 0.0.0.0 for container compatibility (required for Render)
    # Use 127.0.0.1 only for local development
    is_render = os.getenv("RENDER") == "production"
    host = "0.0.0.0" if is_render else "127.0.0.1"
    
    # Enable reload only in development
    enable_reload = not is_render
    
    logger.info(f"🌍 Environment: {'Render Production' if is_render else 'Local Development'}")
    logger.info(f"🧪 Starting test server on {host}:{test_port}")
    
    # Server configuration optimized for both local and Render deployment
    config = {
        "host": host,
        "port": test_port,
        "log_level": "info",
        "reload": enable_reload,  # Only reload in development
        "access_log": True
    }
    
    logger.info("🚀 TDX Chatbot Test Server Starting...")
    logger.info(f"📱 Frontend: http://127.0.0.1:{test_port}/")
    logger.info(f"📖 API Docs: http://127.0.0.1:{test_port}/docs")
    logger.info(f"🔧 API Base: http://127.0.0.1:{test_port}/api/test/")
    logger.info("=" * 60)
    
    try:
        uvicorn.run("main_test:app", **config)
    except KeyboardInterrupt:
        logger.info("🛑 Test server stopped by user")
    except Exception as e:
        logger.error(f"❌ Error starting test server: {e}")
        sys.exit(1)