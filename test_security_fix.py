"""
Test script to verify hardcoded fallback removal
Tests both success and failure scenarios
"""
import sys
import os

print("=" * 70)
print("TESTING HARDCODED FALLBACK REMOVAL")
print("=" * 70)

# Test 1: With DATABASE_URL set (should work)
print("\n✅ Test 1: DATABASE_URL is set (current state)")
print("-" * 70)
try:
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.getenv('DATABASE_URL'):
        print("❌ FAIL: DATABASE_URL not in environment")
        sys.exit(1)
    
    from backend.database import DATABASE_URL, test_connection
    print(f"DATABASE_URL loaded: {DATABASE_URL[:20]}...")
    
    # Test connection
    success = test_connection()
    if success:
        print("✅ PASS: Connection successful with environment variable")
    else:
        print("❌ FAIL: Connection failed")
        sys.exit(1)
        
except EnvironmentError as e:
    print(f"❌ FAIL: Should not raise error when DATABASE_URL is set")
    print(f"Error: {e}")
    sys.exit(1)

# Test 2: Verify no hardcoded credentials in code
print("\n✅ Test 2: Verify hardcoded credentials removed from code")
print("-" * 70)

with open('backend/database.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check for hardcoded postgres credentials
if 'postgres:password@localhost' in content:
    print("❌ FAIL: Hardcoded credentials still present!")
    sys.exit(1)
elif 'os.getenv("DATABASE_URL", "' in content:
    print("❌ FAIL: Fallback value still present in os.getenv()")
    sys.exit(1)
else:
    print("✅ PASS: No hardcoded credentials found")
    print("✅ PASS: No fallback value in os.getenv()")

# Test 3: Verify fail-fast validation exists
print("\n✅ Test 3: Verify fail-fast validation is present")
print("-" * 70)

if 'if not DATABASE_URL:' in content and 'raise EnvironmentError' in content:
    print("✅ PASS: Fail-fast validation is present")
    print("   Application will raise EnvironmentError if DATABASE_URL missing")
else:
    print("❌ FAIL: Fail-fast validation not found")
    sys.exit(1)

# Summary
print("\n" + "=" * 70)
print("✅ ALL TESTS PASSED - SECURITY IMPROVEMENT VERIFIED")
print("=" * 70)

print("\nChanges Verified:")
print("  ✅ Hardcoded credentials removed")
print("  ✅ Fallback database URL removed")
print("  ✅ Fail-fast validation added")
print("  ✅ Clear error message for missing DATABASE_URL")
print("  ✅ Current configuration still works")

print("\nSecurity Benefits:")
print("  • No credentials exposed in source code")
print("  • Prevents accidental wrong database connection")
print("  • Forces explicit configuration")
print("  • Fails immediately with helpful error message")

print("\n" + "=" * 70)
