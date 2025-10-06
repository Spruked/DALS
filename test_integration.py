#!/usr/bin/env python3
"""
ISS Module Prometheus Prime Integration Test
===========================================

This script tests the ISS Module's compatibility with Prometheus Prime
microservices architecture. Run this to verify the integration works.
"""

import asyncio
import sys
from typing import Dict, Any

def test_basic_imports():
    """Test basic ISS Module imports"""
    try:
        from iss_module import ISS, CaptainLog, Exporters, get_stardate, current_timecodes
        print("✓ Core ISS Module components imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import core components: {e}")
        return False

def test_prometheus_integration():
    """Test Prometheus Prime integration components"""
    try:
        from iss_module.prometheus_integration import (
            PrometheusISS, 
            create_prometheus_iss_app,
            ReasoningRequest,
            ReasoningResponse
        )
        print("✓ Prometheus Prime integration components imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import Prometheus components: {e}")
        print("  Install dependencies with: pip install structlog pydantic-settings httpx")
        return False

def test_configuration():
    """Test configuration system"""
    try:
        from iss_module.config import settings, ISSSettings
        print(f"✓ Configuration loaded - Service: {settings.service_name}")
        return True
    except ImportError as e:
        print(f"✗ Failed to import configuration: {e}")
        return False

def test_structured_logging():
    """Test structured logging"""
    try:
        from iss_module.logging_config import get_logger, configure_structured_logging
        configure_structured_logging()
        logger = get_logger("test")
        logger.info("Test log message", test=True)
        print("✓ Structured logging configured successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import logging components: {e}")
        return False

async def test_reasoning_request():
    """Test reasoning request processing"""
    try:
        from iss_module.prometheus_integration import PrometheusISS, ReasoningRequest
        
        # Create ISS instance
        prometheus_iss = PrometheusISS()
        await prometheus_iss.initialize()
        
        # Create test request
        request = ReasoningRequest(
            input_data={"query": "test integration", "source": "integration_test"},
            cycle_type="test",
            timeout_ms=1000,
            context={}
        )
        
        # Process request
        response = await prometheus_iss.process_reasoning(request)
        
        print(f"✓ Reasoning request processed successfully")
        print(f"  Cycle ID: {response.cycle_id}")
        print(f"  Stardate: {response.stardate}")
        print(f"  Processing time: {response.processing_time_ms}ms")
        
        return True
    except Exception as e:
        print(f"✗ Reasoning request failed: {e}")
        return False

async def test_vault_query():
    """Test vault query functionality"""
    try:
        from iss_module.prometheus_integration import PrometheusISS, VaultQueryRequest
        
        prometheus_iss = PrometheusISS()
        await prometheus_iss.initialize()
        
        # Add a test log entry first
        await prometheus_iss.captain_log.create_entry(
            content="Test entry for vault query",
            category="test",
            tags=["integration", "test"]
        )
        
        # Query the vault
        query_request = VaultQueryRequest(
            query={"category": "test"},
            limit=10
        )
        
        response = await prometheus_iss.query_vault(query_request)
        
        print(f"✓ Vault query successful")
        print(f"  Results: {response.total_count} entries")
        print(f"  Query time: {response.query_time_ms}ms")
        
        return True
    except Exception as e:
        print(f"✗ Vault query failed: {e}")
        return False

def test_fastapi_app_creation():
    """Test FastAPI app creation"""
    try:
        from iss_module.prometheus_integration import create_prometheus_iss_app
        
        app = create_prometheus_iss_app("test-service")
        
        print("✓ FastAPI app created successfully")
        print(f"  Title: {app.title}")
        print(f"  Version: {app.version}")
        
        # Check routes
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        print(f"  Routes: {', '.join(routes)}")
        
        return True
    except Exception as e:
        print(f"✗ FastAPI app creation failed: {e}")
        return False

async def test_integration_compatibility():
    """Test full integration compatibility"""
    try:
        from iss_module import get_stardate, current_timecodes
        from iss_module.prometheus_integration import ReasoningRequest, ReasoningResponse
        
        # Test time anchoring (critical for Prometheus Prime)
        stardate = get_stardate()
        timecodes = current_timecodes()
        
        # Simulate API Gateway request format
        api_request = {
            "input_data": {
                "command": "status_check", 
                "source": "api_gateway",
                "user_id": "test_user"
            },
            "cycle_type": "system_check",
            "timeout_ms": 2000
        }
        
        # Test that we can create the request model
        reasoning_request = ReasoningRequest(**api_request)
        
        print("✓ Prometheus Prime API compatibility verified")
        print(f"  Stardate: {stardate}")
        print(f"  Request model: {reasoning_request.cycle_type}")
        print(f"  Time anchors: ISO={timecodes['iso_timestamp'][:19]}")
        
        return True
    except Exception as e:
        print(f"✗ Integration compatibility test failed: {e}")
        return False

async def main():
    """Run all integration tests"""
    print("ISS Module Prometheus Prime Integration Test")
    print("=" * 50)
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("Prometheus Integration", test_prometheus_integration),
        ("Configuration", test_configuration),
        ("Structured Logging", test_structured_logging),
        ("FastAPI App Creation", test_fastapi_app_creation),
        ("Reasoning Request", test_reasoning_request),
        ("Vault Query", test_vault_query),
        ("Integration Compatibility", test_integration_compatibility),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\nTesting {test_name}...")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Results Summary:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"  {symbol} {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! ISS Module is ready for Prometheus Prime integration.")
        print("\nNext steps:")
        print("1. Deploy with: ./deploy.sh deploy")
        print("2. Configure API Gateway to route to http://iss-controller:8003")
        print("3. Update service discovery with ISS Controller registration")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please fix issues before deployment.")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))