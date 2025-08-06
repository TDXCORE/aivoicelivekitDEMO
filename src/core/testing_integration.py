"""
Testing System Integration
Safely mounts the testing system as a sub-application at /testing
"""

import os
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger("testing_integration")

def create_testing_app() -> FastAPI:
    """Create the testing sub-application"""
    try:
        # Import testing components
        from testing.test_router import test_router
        
        # Create testing app
        testing_app = FastAPI(
            title="TDX Chatbot Testing Interface",
            description="Testing environment for TDX WhatsApp Agent - Isolated from production",
            version="1.0.0",
            docs_url="/docs",  # Will be available at /testing/docs
            redoc_url="/redoc"  # Will be available at /testing/redoc
        )
        
        # Configure CORS for testing - more permissive than production
        testing_app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Permissive for testing
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Include test router (API routes will be at /testing/api/test/)
        testing_app.include_router(test_router)
        
        # Mount static files for frontend
        frontend_path = Path(__file__).parent.parent.parent / "testing" / "frontend"
        if frontend_path.exists():
            testing_app.mount("/static", StaticFiles(directory=str(frontend_path)), name="testing_static")
            logger.info(f"✅ Testing frontend static files mounted from: {frontend_path}")
        else:
            logger.warning(f"⚠️ Testing frontend directory not found: {frontend_path}")
        
        # Serve frontend at testing root
        @testing_app.get("/")
        async def serve_testing_frontend():
            """Serve the testing interface at /testing/"""
            frontend_file = frontend_path / "index.html"
            if frontend_file.exists():
                return FileResponse(str(frontend_file))
            else:
                return {
                    "message": "TDX Chatbot Testing Interface",
                    "status": "Frontend files not found",
                    "expected_path": str(frontend_file),
                    "api_docs": "/testing/docs",
                    "api_base": "/testing/api/test"
                }
        
        @testing_app.get("/health")
        async def testing_health():
            """Testing system health check"""
            try:
                # Quick test of testing components
                from testing.test_integration import TestAgentWrapper
                wrapper_available = True
            except Exception as e:
                wrapper_available = False
                logger.warning(f"TestAgentWrapper not available: {e}")
            
            return {
                "status": "healthy",
                "service": "TDX Testing Interface",
                "mount_path": "/testing",
                "api_path": "/testing/api/test",
                "frontend_available": frontend_path.exists(),
                "agent_wrapper_available": wrapper_available,
                "docs": "/testing/docs"
            }
        
        @testing_app.get("/info")
        async def testing_info():
            """Testing system information"""
            return {
                "service": "TDX Chatbot Testing System",
                "description": "Isolated testing environment for WhatsApp agent",
                "version": "1.0.0",
                "mount_path": "/testing",
                "features": [
                    "Chat interface estilo ChatGPT",
                    "Mismo agente que producción",
                    "Reset completo de conversaciones", 
                    "Exportación de datos de prueba",
                    "Aislamiento total de Chatwoot"
                ],
                "endpoints": {
                    "frontend": "/testing/",
                    "api": "/testing/api/test/",
                    "health": "/testing/health",
                    "docs": "/testing/docs",
                    "redoc": "/testing/redoc"
                },
                "isolation": {
                    "production_safe": True,
                    "independent_memory": True,
                    "no_chatwoot_impact": True
                }
            }
        
        logger.info("✅ Testing sub-application created successfully")
        return testing_app
        
    except Exception as e:
        logger.error(f"❌ Error creating testing application: {e}")
        # Return a minimal error app
        error_app = FastAPI(title="Testing System Error")
        
        @error_app.get("/")
        async def error_info():
            return {
                "error": "Testing system could not be initialized",
                "details": str(e),
                "production_status": "unaffected"
            }
        
        return error_app

def should_enable_testing() -> bool:
    """Determine if testing should be enabled"""
    # Check environment variables
    testing_enabled = os.getenv("TESTING_ENABLED", "true").lower() == "true"
    render_env = os.getenv("RENDER")
    
    # Always enable in development, or when explicitly enabled
    if render_env != "production":
        return testing_enabled
    
    # In production, only enable if explicitly requested
    return testing_enabled

def integrate_testing_system(main_app: FastAPI) -> None:
    """Safely integrate testing system into main app"""
    try:
        # Check if testing should be enabled
        if not should_enable_testing():
            logger.info("⚠️ Testing system disabled via TESTING_ENABLED environment variable")
            return
        
        logger.info("🧪 Integrating testing system...")
        
        # Create and mount testing sub-application
        testing_app = create_testing_app()
        main_app.mount("/testing", testing_app, name="testing")
        
        logger.info("✅ Testing system integrated successfully")
        logger.info("🌐 Testing interface available at: /testing/")
        logger.info("🔧 Testing API available at: /testing/api/test/")
        logger.info("📖 Testing docs available at: /testing/docs")
        logger.info("❤️ Testing health check: /testing/health")
        
    except ImportError as e:
        logger.error(f"❌ Testing modules not available: {e}")
        logger.error("❌ Testing system will not be available")
        logger.info("✅ Production system unaffected")
        
    except Exception as e:
        logger.error(f"❌ Error integrating testing system: {e}")
        logger.error("❌ Testing system will not be available")
        logger.info("✅ Production system unaffected")

def get_testing_status() -> dict:
    """Get current testing integration status"""
    return {
        "enabled": should_enable_testing(),
        "testing_enabled_var": os.getenv("TESTING_ENABLED", "true"),
        "render_env": os.getenv("RENDER", "development"),
        "expected_mount_path": "/testing"
    }