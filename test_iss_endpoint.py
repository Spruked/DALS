#!/usr/bin/env python3
"""
Quick test script to verify ISS timestamp endpoint
"""

import requests
import json
from datetime import datetime

def test_iss_endpoint():
    """Test the ISS timestamp endpoint"""
    try:
        # Test the new /api/v1/iss/now endpoint
        response = requests.get("http://127.0.0.1:8003/api/v1/iss/now", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ /api/v1/iss/now endpoint working!")
            print(json.dumps(data, indent=2))
            
            # Verify the expected fields
            expected_fields = ["timestamp_iso", "timestamp_epoch", "timestamp_julian", "stardate_iss"]
            for field in expected_fields:
                if field in data:
                    print(f"✅ Field '{field}' present: {data[field]}")
                else:
                    print(f"❌ Field '{field}' missing")
        else:
            print(f"❌ Endpoint failed with status {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is it running on port 8003?")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_time_endpoint():
    """Test the general time endpoint"""
    try:
        # Test the existing /api/time endpoint
        response = requests.get("http://127.0.0.1:8003/api/time", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ /api/time endpoint working!")
            print(json.dumps(data, indent=2))
        else:
            print(f"❌ /api/time endpoint failed with status {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is it running on port 8003?")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Testing ISS Module Timestamp Endpoints")
    print("=" * 50)
    
    print("\n1. Testing /api/v1/iss/now")
    test_iss_endpoint()
    
    print("\n2. Testing /api/time")  
    test_time_endpoint()
    
    print("\n" + "=" * 50)
    print("Test completed!")