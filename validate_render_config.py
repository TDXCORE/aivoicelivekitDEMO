#!/usr/bin/env python3
"""
Script de validación para configuración de Render
Verifica que todos los cambios sean compatibles con Render deployment
"""

import os
import sys
import asyncio
import logging
import tempfile
import requests
from urllib.parse import urlparse

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("render-validation")

def validate_port_configuration():
    """Validar configuración de puerto"""
    logger.info("🔍 Validando configuración de puerto...")
    
    try:
        # Test local development config
        os.environ.pop('RENDER', None)  # Remove RENDER env var
        os.environ.pop('PORT', None)    # Remove PORT env var
        
        # Import main_test to check config
        import importlib.util
        spec = importlib.util.spec_from_file_location("main_test", "main_test.py")
        main_test = importlib.util.module_from_spec(spec)
        
        # Test development configuration
        test_port = int(os.getenv("PORT", "8001"))
        is_render = os.getenv("RENDER") == "production"
        host = "0.0.0.0" if is_render else "127.0.0.1"
        
        assert test_port == 8001, f"Expected port 8001 for dev, got {test_port}"
        assert host == "127.0.0.1", f"Expected localhost for dev, got {host}"
        assert not is_render, "Expected development mode"
        
        # Test production configuration
        os.environ['RENDER'] = 'production'
        os.environ['PORT'] = '8000'
        
        test_port = int(os.getenv("PORT", "8001"))
        is_render = os.getenv("RENDER") == "production"
        host = "0.0.0.0" if is_render else "127.0.0.1"
        
        assert test_port == 8000, f"Expected port 8000 for prod, got {test_port}"
        assert host == "0.0.0.0", f"Expected 0.0.0.0 for prod, got {host}"
        assert is_render, "Expected production mode"
        
        logger.info("✅ Configuración de puerto correcta")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en configuración de puerto: {e}")
        return False
    finally:
        # Clean up environment
        os.environ.pop('RENDER', None)
        os.environ.pop('PORT', None)

def validate_cors_configuration():
    """Validar configuración de CORS"""
    logger.info("🔍 Validando configuración de CORS...")
    
    try:
        # Read main_test.py content
        with open("main_test.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check CORS configuration exists
        assert "CORSMiddleware" in content, "CORSMiddleware not found"
        assert "is_render" in content, "Environment detection not found"
        assert "allow_origins" in content, "CORS origins configuration not found"
        assert "aivoicelivekitdemo-testing.onrender.com" in content, "Render domain not in CORS"
        
        logger.info("✅ Configuración de CORS correcta")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en configuración de CORS: {e}")
        return False

def validate_render_yaml():
    """Validar archivo render-testing.yaml"""
    logger.info("🔍 Validando render-testing.yaml...")
    
    try:
        assert os.path.exists("render-testing.yaml"), "render-testing.yaml not found"
        
        with open("render-testing.yaml", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check required configurations
        required_configs = [
            "aivoicelivekitdemo-testing",
            "python main_test.py",
            "RENDER",
            "OPENAI_API_KEY",
            "VITE_CHATWOOT_ACCOUNT_ID",
            "healthCheckPath: /api/test/health"
        ]
        
        for config in required_configs:
            assert config in content, f"Required config '{config}' not found in render-testing.yaml"
        
        logger.info("✅ render-testing.yaml configurado correctamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en render-testing.yaml: {e}")
        return False

def validate_dockerfile():
    """Validar Dockerfile.testing"""
    logger.info("🔍 Validando Dockerfile.testing...")
    
    try:
        assert os.path.exists("Dockerfile.testing"), "Dockerfile.testing not found"
        
        with open("Dockerfile.testing", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check required configurations
        required_configs = [
            "FROM python:3.12-slim",
            'CMD ["python", "main_test.py"]',
            "HEALTHCHECK",
            "/api/test/health",
            "USER appuser"  # Security
        ]
        
        for config in required_configs:
            assert config in content, f"Required config '{config}' not found in Dockerfile.testing"
        
        logger.info("✅ Dockerfile.testing configurado correctamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en Dockerfile.testing: {e}")
        return False

def validate_environment_variables():
    """Validar variables de entorno para Render"""
    logger.info("🔍 Validando variables de entorno...")
    
    try:
        # Check render-testing.yaml for environment variables
        with open("render-testing.yaml", "r", encoding="utf-8") as f:
            content = f.read()
        
        required_env_vars = [
            "RENDER",
            "TESTING_ENABLED", 
            "OPENAI_API_KEY",
            "VITE_CHATWOOT_ACCOUNT_ID",
            "VITE_CHATWOOT_API_TOKEN"
        ]
        
        for env_var in required_env_vars:
            assert env_var in content, f"Environment variable '{env_var}' not configured"
        
        logger.info("✅ Variables de entorno configuradas")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en variables de entorno: {e}")
        return False

def validate_imports_and_dependencies():
    """Validar que todas las importaciones funcionen"""
    logger.info("🔍 Validando importaciones y dependencias...")
    
    try:
        # Test core imports
        import fastapi
        import uvicorn
        import testing
        from testing.test_integration import TestAgentWrapper
        from testing.test_router import test_router
        
        # Test agent import
        from src.agents.whatsapp_agent import TDXWhatsAppAgentClean
        
        logger.info("✅ Todas las importaciones funcionan")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en importaciones: {e}")
        return False

def validate_health_endpoints():
    """Validar que los health endpoints existan"""
    logger.info("🔍 Validando health endpoints...")
    
    try:
        # Read test_router.py to check health endpoints
        with open("testing/test_router.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        required_endpoints = [
            '/health',
            '/status',
            'get_test_status'
        ]
        
        for endpoint in required_endpoints:
            assert endpoint in content, f"Health endpoint '{endpoint}' not found"
        
        logger.info("✅ Health endpoints configurados")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en health endpoints: {e}")
        return False

async def run_render_validation():
    """Ejecutar todas las validaciones de Render"""
    logger.info("🚀 Iniciando validación de configuración para Render")
    logger.info("=" * 60)
    
    tests = [
        ("Configuración de puerto", validate_port_configuration),
        ("Configuración de CORS", validate_cors_configuration),
        ("Archivo render-testing.yaml", validate_render_yaml),
        ("Dockerfile.testing", validate_dockerfile),
        ("Variables de entorno", validate_environment_variables),
        ("Importaciones y dependencias", validate_imports_and_dependencies),
        ("Health endpoints", validate_health_endpoints)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n📋 Ejecutando: {test_name}")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ Error en {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen
    logger.info("\n" + "=" * 60)
    logger.info("📊 RESUMEN DE VALIDACIÓN RENDER")
    logger.info("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} {test_name}")
        if result:
            passed += 1
    
    logger.info(f"\n🎯 Resultado: {passed}/{len(results)} validaciones pasaron")
    
    if passed == len(results):
        logger.info("🎉 ¡Sistema listo para deploy en Render!")
        logger.info("\n📖 Próximos pasos:")
        logger.info("   1. Crear nuevo servicio en Render")
        logger.info("   2. Usar render-testing.yaml como configuración")
        logger.info("   3. Configurar variables de entorno sensibles")
        logger.info("   4. Deploy y verificar health checks")
        return True
    else:
        logger.error("⚠️ Algunas validaciones fallaron - revisar errores arriba")
        logger.info("\n📖 Acciones recomendadas:")
        logger.info("   1. Arreglar errores mostrados")
        logger.info("   2. Re-ejecutar validación")
        logger.info("   3. Proceder con deploy una vez todo pase")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(run_render_validation())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        logger.info("\n🛑 Validación interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        sys.exit(1)