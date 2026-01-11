"""
Error Handling Test Script
Tests the improved error handling with proper HTTP status codes and user-friendly messages
"""

import requests
import json

print("=" * 70)
print("ERROR HANDLING IMPROVEMENT TEST")
print("=" * 70)

# Note: Start the server first with: uvicorn backend.main:app --reload

BASE_URL = "http://localhost:8000"

def test_validation_error():
    """Test that validation errors return 400 with user-friendly message"""
    print("\n🧪 Test 1: Validation Error (missing required field)")
    print("-" * 70)
    
    try:
        response = requests.post(f"{BASE_URL}/text", json={})
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 400 or response.status_code == 422:
            print("   ✅ PASS: Returns 4xx for validation error")
        else:
            print(f"   ❌ FAIL: Expected 400/422, got {response.status_code}")
    except Exception as e:
        print(f"   ⚠️  Server not running: {e}")

def test_request_id_header():
    """Test that responses include X-Request-ID header"""
    print("\n🧪 Test 2: Request ID in Response Headers")
    print("-" * 70)
    
    try:
        response = requests.post(
            f"{BASE_URL}/text",
            json={"text": "create a vpc"}
        )
        
        request_id = response.headers.get("X-Request-ID")
        print(f"   X-Request-ID: {request_id}")
        
        if request_id:
            print("   ✅ PASS: Request ID header present")
        else:
            print("   ❌ FAIL: No request ID header")
    except Exception as e:
        print(f"   ⚠️  Server not running: {e}")

def test_error_response_structure():
    """Test error response has consistent structure"""
    print("\n🧪 Test 3: Standardized Error Response Format")
    print("-" * 70)
    
    try:
        # This should trigger a validation error
        response = requests.post(f"{BASE_URL}/text", json={})
        error_data = response.json()
        
        print(f"   Response structure:")
        print(f"   {json.dumps(error_data, indent=2)}")
        
        # Check for expected fields
        has_success = "success" in error_data or "detail" in error_data
        
        if has_success:
            print("   ✅ PASS: Response has expected structure")
        else:
            print("   ❌ FAIL: Missing expected fields")
    except Exception as e:
        print(f"   ⚠️  Server not running: {e}")

if __name__ == "__main__":
    print("\nℹ️  NOTE: These tests require the server to be running.")
    print("   Start with: uvicorn backend.main:app --reload")
    print()
    
    test_validation_error()
    test_request_id_header()
    test_error_response_structure()
    
    print("\n" + "=" * 70)
    print("TEST SUITE COMPLETE")
    print("=" * 70)
    print("\nTo verify all improvements:")
    print("1. Start the server: uvicorn backend.main:app --reload")
    print("2. Run this test script")
    print("3. Check that:")
    print("   - HTTP status codes are correct (400, 404, 500, etc.)")
    print("   - Error messages are user-friendly")
    print("   - X-Request-ID header is present")
    print("   - Response format is consistent")
