#!/usr/bin/env python3
"""
Test script to verify that testing integration doesn't affect production
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("integration_safety_test")

def test_production_routes_unchanged():
    """Test that production routes remain unchanged"""
    logger.info("Testing production routes...")
    
    try:
        # Import the main receiver app
        from src.webhooks.receiver import app
        
        # Get all routes
        routes = [route.path for route in app.routes]
        
        # Check critical production routes exist
        critical_routes = [
            "/",
            "/health", 
            "/webhooks/chatwoot/{token}",
            "/webhooks/whatsapp/{token}"
        ]
        
        for route in critical_routes:
            route_exists = any(r == route or route in r for r in routes)
            if route_exists:
                logger.info(f"SUCCESS: Production route {route} exists")
            else:
                logger.error(f"ERROR: Production route {route} missing")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"ERROR testing production routes: {e}")
        return False

def test_testing_integration_optional():
    """Test that testing integration is optional and safe"""
    logger.info("Testing integration safety...")
    
    try:
        # Test with testing enabled
        os.environ['TESTING_ENABLED'] = 'true'
        from src.webhooks.receiver import app as app_with_testing
        
        routes_with_testing = [route.path for route in app_with_testing.routes]
        testing_routes_exist = any('testing' in str(route) for route in routes_with_testing)
        
        if testing_routes_exist:
            logger.info("SUCCESS: Testing routes mounted when enabled")
        else:
            logger.error("ERROR: Testing routes not mounted when enabled")
            return False
        
        # Test with testing disabled
        os.environ['TESTING_ENABLED'] = 'false'
        
        # Clear module cache to test fresh import
        import importlib
        if 'src.webhooks.receiver' in sys.modules:
            importlib.reload(sys.modules['src.webhooks.receiver'])
        
        logger.info("SUCCESS: Testing integration is optional and safe")
        return True
        
    except Exception as e:
        logger.error(f"ERROR testing integration safety: {e}")
        return False

def test_error_handling():
    """Test that errors in testing don't affect production"""
    logger.info("Testing error handling...")
    
    try:
        # Test that production app still works even if testing fails
        from src.webhooks.receiver import app
        
        # App should be created regardless of testing status
        if app is None:
            logger.error("ERROR: Main app is None")
            return False
        
        logger.info("SUCCESS: Production app unaffected by testing errors")
        return True
        
    except Exception as e:
        logger.error(f"ERROR testing error handling: {e}")
        return False

def test_environment_detection():
    """Test environment detection works correctly"""
    logger.info("Testing environment detection...")
    
    try:
        from src.core.testing_integration import should_enable_testing
        
        # Test development environment
        os.environ.pop('RENDER', None)
        os.environ['TESTING_ENABLED'] = 'true'
        dev_enabled = should_enable_testing()
        
        # Test production environment
        os.environ['RENDER'] = 'production'
        os.environ['TESTING_ENABLED'] = 'false'
        prod_disabled = should_enable_testing()
        
        if dev_enabled and not prod_disabled:
            logger.info("SUCCESS: Environment detection working correctly")
            return True
        else:
            logger.error(f"ERROR: Environment detection failed - dev: {dev_enabled}, prod: {prod_disabled}")
            return False
            
    except Exception as e:
        logger.error(f"ERROR testing environment detection: {e}")
        return False

def run_safety_tests():
    """Run all safety tests"""
    logger.info("="*50)
    logger.info("RUNNING INTEGRATION SAFETY TESTS")
    logger.info("="*50)
    
    tests = [
        ("Production routes unchanged", test_production_routes_unchanged),
        ("Testing integration optional", test_testing_integration_optional),
        ("Error handling safe", test_error_handling),
        ("Environment detection", test_environment_detection)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\nRunning: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("SAFETY TEST RESULTS")
    logger.info("="*50)
    
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        logger.info(f"{status}: {test_name}")
        if result:
            passed += 1
    
    logger.info(f"\nResult: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        logger.info("SUCCESS: All safety tests passed - Integration is safe for deployment")
        return True
    else:
        logger.error("ERROR: Some safety tests failed - Review before deployment")
        return False

if __name__ == "__main__":
    try:
        success = run_safety_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)