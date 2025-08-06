#!/usr/bin/env python3
"""
Script de validación para el sistema de testing TDX Chatbot
Verifica que todos los componentes funcionen correctamente
"""

import sys
import os
import asyncio
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("validation")

def check_file_structure():
    """Verificar que todos los archivos necesarios existan"""
    logger.info("🔍 Verificando estructura de archivos...")
    
    required_files = [
        "testing/__init__.py",
        "testing/test_storage.py", 
        "testing/test_integration.py",
        "testing/test_router.py",
        "testing/frontend/index.html",
        "testing/frontend/style.css",
        "testing/frontend/script.js",
        "main_test.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
            logger.error(f"❌ Archivo faltante: {file_path}")
        else:
            logger.info(f"✅ {file_path}")
    
    if missing_files:
        logger.error(f"❌ {len(missing_files)} archivos faltantes")
        return False
    else:
        logger.info("✅ Estructura de archivos completa")
        return True

def check_imports():
    """Verificar que las importaciones funcionen"""
    logger.info("🔍 Verificando importaciones...")
    
    try:
        # Verificar dependencias principales
        import fastapi
        import uvicorn
        import pydantic
        logger.info("✅ FastAPI dependencies")
        
        # Verificar módulo de testing
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        import testing
        logger.info("✅ Testing module")
        
        # Verificar componentes de testing
        from testing.test_storage import TestStorage
        from testing.test_integration import TestAgentWrapper
        from testing.test_router import test_router
        logger.info("✅ Testing components")
        
        # Verificar agente original
        from src.agents.whatsapp_agent import TDXWhatsAppAgentClean
        logger.info("✅ Original agent")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Error de importación: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        return False

async def test_storage():
    """Probar funcionalidad de almacenamiento"""
    logger.info("🔍 Probando TestStorage...")
    
    try:
        from testing.test_storage import TestStorage
        
        storage = TestStorage()
        
        # Probar guardado de mensajes
        storage.save_user_message("Mensaje de prueba")
        storage.save_bot_message("Respuesta de prueba")
        
        # Verificar datos
        messages = storage.get_conversation()
        assert len(messages) == 2, f"Esperaban 2 mensajes, obtuvo {len(messages)}"
        
        # Probar reset
        storage.clear()
        messages = storage.get_conversation()
        assert len(messages) == 0, f"Después del reset, esperaban 0 mensajes, obtuvo {len(messages)}"
        
        logger.info("✅ TestStorage funcionando correctamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en TestStorage: {e}")
        return False

async def test_agent_wrapper():
    """Probar wrapper del agente"""
    logger.info("🔍 Probando TestAgentWrapper...")
    
    try:
        from testing.test_integration import TestAgentWrapper
        
        # Crear wrapper
        wrapper = TestAgentWrapper()
        
        # Verificar inicialización
        assert wrapper.agent is not None, "Agente no inicializado"
        assert wrapper.storage is not None, "Storage no inicializado"
        assert wrapper.test_session_id is not None, "Session ID no generado"
        
        # Probar reset
        old_session = wrapper.test_session_id
        wrapper.reset_conversation()
        new_session = wrapper.test_session_id
        assert old_session != new_session, "Session ID no cambió después del reset"
        
        logger.info("✅ TestAgentWrapper funcionando correctamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en TestAgentWrapper: {e}")
        return False

def test_server_config():
    """Verificar configuración del servidor"""
    logger.info("🔍 Verificando configuración del servidor...")
    
    try:
        # Verificar que el archivo main_test.py sea ejecutable
        with open("main_test.py", "r", encoding="utf-8") as f:
            content = f.read()
            
        # Verificar elementos críticos
        assert "FastAPI" in content, "FastAPI no encontrado en main_test.py"
        assert "test_router" in content, "test_router no importado"
        assert "uvicorn" in content, "uvicorn no configurado"
        assert "8001" in content, "Puerto de testing no configurado"
        
        logger.info("✅ Configuración del servidor correcta")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verificando servidor: {e}")
        return False

def check_environment():
    """Verificar variables de entorno necesarias"""
    logger.info("🔍 Verificando variables de entorno...")
    
    # Variables críticas para el funcionamiento
    env_vars = {
        "OPENAI_API_KEY": "OpenAI API (crítico para respuestas)",
        "VITE_CHATWOOT_ACCOUNT_ID": "Chatwoot Account (para wrapper)",
        "VITE_CHATWOOT_API_TOKEN": "Chatwoot API (para wrapper)"
    }
    
    missing_vars = []
    for var, description in env_vars.items():
        value = os.getenv(var)
        if value:
            logger.info(f"✅ {var}: {'*' * min(len(value), 10)}...")
        else:
            missing_vars.append(f"{var} ({description})")
            logger.warning(f"⚠️ {var}: No configurado")
    
    if missing_vars:
        logger.warning("⚠️ Variables faltantes - el agente puede usar fallbacks")
        for var in missing_vars:
            logger.warning(f"   - {var}")
    else:
        logger.info("✅ Todas las variables de entorno configuradas")
    
    return True  # No es crítico para el testing

async def run_validation():
    """Ejecutar todas las validaciones"""
    logger.info("🚀 Iniciando validación del sistema de testing TDX Chatbot")
    logger.info("=" * 60)
    
    tests = [
        ("Estructura de archivos", check_file_structure),
        ("Importaciones", check_imports),
        ("TestStorage", test_storage),
        ("TestAgentWrapper", test_agent_wrapper),
        ("Configuración servidor", test_server_config),
        ("Variables de entorno", check_environment)
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
    logger.info("📊 RESUMEN DE VALIDACIÓN")
    logger.info("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} {test_name}")
        if result:
            passed += 1
    
    logger.info(f"\n🎯 Resultado: {passed}/{len(results)} pruebas pasaron")
    
    if passed == len(results):
        logger.info("🎉 ¡Sistema de testing completamente funcional!")
        logger.info("\n📖 Próximos pasos:")
        logger.info("   1. Ejecutar: python main_test.py")
        logger.info("   2. Abrir: http://127.0.0.1:8001/")
        logger.info("   3. Comenzar a probar el chatbot")
        return True
    else:
        logger.error("⚠️ Algunas validaciones fallaron - revisar errores arriba")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(run_validation())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        logger.info("\n🛑 Validación interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        sys.exit(1)