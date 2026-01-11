"""
Database Misconfiguration Detection Script
Detects fallback databases, incorrect .env loading, and hardcoded credentials
"""
import sys
import os
sys.path.insert(0, '.')

from dotenv import load_dotenv
import re

print("=" * 70)
print("DATABASE MISCONFIGURATION DETECTION")
print("=" * 70)

issues_found = []
warnings_found = []

# Step 1: Check for SQLite/Memory DB fallback
print("\n🔍 Step 1: Checking for SQLite/Memory DB Fallback")
print("-" * 70)

database_file = 'backend/database.py'
with open(database_file, 'r', encoding='utf-8') as f:
    db_content = f.read()

sqlite_patterns = ['sqlite', 'memory', ':memory:', 'db.sqlite']
found_sqlite = False
for pattern in sqlite_patterns:
    if pattern.lower() in db_content.lower():
        print(f"⚠️  Found '{pattern}' in database.py")
        warnings_found.append(f"SQLite/Memory DB reference: {pattern}")
        found_sqlite = True

if not found_sqlite:
    print("✅ No SQLite or memory DB fallback detected")
else:
    print("❌ SQLite/Memory DB fallback may be present")

# Step 2: Check DATABASE_URL configuration
print("\n⚙️  Step 2: Analyzing DATABASE_URL Configuration")
print("-" * 70)

# Check for hardcoded fallback
if 'os.getenv("DATABASE_URL"' in db_content:
    print("✅ DATABASE_URL loaded from environment variable")
    
    # Extract the fallback/default value
    fallback_match = re.search(r'os\.getenv\("DATABASE_URL",\s*"([^"]+)"\)', db_content)
    if fallback_match:
        fallback_url = fallback_match.group(1)
        print(f"⚠️  HARDCODED FALLBACK DETECTED:")
        print(f"   Default: {fallback_url}")
        
        # Check if fallback contains credentials
        if 'postgres:password' in fallback_url or 'localhost' in fallback_url:
            issues_found.append("Hardcoded database credentials in fallback")
            print("   ❌ SECURITY ISSUE: Hardcoded credentials (postgres:password)")
            print("   ❌ Risk: May connect to wrong database if .env missing")
        
        # Check database type in fallback
        if fallback_url.startswith('postgresql'):
            print("   ℹ️  Fallback type: PostgreSQL (correct)")
        elif fallback_url.startswith('sqlite'):
            issues_found.append("SQLite fallback configured")
            print("   ❌ Fallback type: SQLite (WRONG - should be PostgreSQL)")
else:
    issues_found.append("DATABASE_URL not loaded from environment")
    print("❌ DATABASE_URL is hardcoded (not from environment)")

# Step 3: Check .env file loading
print("\n📄 Step 3: Verifying .env File Loading")
print("-" * 70)

if 'load_dotenv()' in db_content:
    print("✅ load_dotenv() called in database.py")
else:
    issues_found.append(".env not loaded in database.py")
    print("❌ load_dotenv() NOT called")

# Check if .env file exists
env_file = '.env'
if os.path.exists(env_file):
    print(f"✅ .env file exists")
    
    # Read and validate .env
    with open(env_file, 'r', encoding='utf-8') as f:
        env_content = f.read()
    
    if 'DATABASE_URL=' in env_content:
        print("✅ DATABASE_URL defined in .env")
        
        # Check if it's the real value or placeholder
        if 'postgresql://user:password@host' in env_content or 'localhost' in env_content:
            warnings_found.append(".env may contain placeholder/test credentials")
            print("⚠️  .env may contain placeholder values")
        else:
            print("✅ .env appears to have real database URL")
    else:
        issues_found.append("DATABASE_URL not defined in .env")
        print("❌ DATABASE_URL not found in .env file")
else:
    issues_found.append(".env file missing")
    print("❌ .env file NOT FOUND")
    print("   Will use hardcoded fallback!")

# Step 4: Check for hardcoded credentials in code
print("\n🔐 Step 4: Scanning for Hardcoded Credentials")
print("-" * 70)

# Files to scan
files_to_scan = [
    'backend/database.py',
    'backend/main.py',
    'backend/repository.py',
]

hardcoded_patterns = {
    r'password\s*=\s*["\'][^"\']+["\']': 'Hardcoded password',
    r'postgresql://[^:]+:[^@]+@': 'Database URL with credentials',
    r'PORT\s*=\s*\d+': 'Hardcoded port',
    r'localhost:\d+': 'Hardcoded localhost with port',
}

found_hardcoded = False
for file_path in files_to_scan:
    if not os.path.exists(file_path):
        continue
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for pattern, description in hardcoded_patterns.items():
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            # Filter out comments and test code
            for match in matches:
                if not match.startswith('#'):
                    print(f"⚠️  {file_path}: {description}")
                    print(f"   Match: {match[:50]}...")
                    found_hardcoded = True
                    if 'password' in match.lower():
                        warnings_found.append(f"Potential hardcoded credential in {file_path}")

if not found_hardcoded:
    print("✅ No obvious hardcoded credentials found")

# Step 5: Check active connection
print("\n🔌 Step 5: Checking Active Database Connection")
print("-" * 70)

load_dotenv()
actual_db_url = os.getenv('DATABASE_URL')

if actual_db_url:
    print(f"✅ DATABASE_URL loaded from environment")
    
    # Analyze the URL
    if actual_db_url.startswith('postgresql://'):
        print("✅ Using PostgreSQL (correct)")
    elif actual_db_url.startswith('sqlite://'):
        issues_found.append("Currently using SQLite instead of PostgreSQL")
        print("❌ Using SQLite (WRONG)")
    elif actual_db_url.startswith('memory://') or ':memory:' in actual_db_url:
        issues_found.append("Currently using in-memory database")
        print("❌ Using in-memory database (WRONG)")
    
    # Check if it's the fallback or real URL
    if 'localhost' in actual_db_url and 'postgres:password' in actual_db_url:
        warnings_found.append("Using fallback localhost database")
        print("⚠️  Using fallback/development database")
        print("   (postgres:password@localhost)")
    else:
        print("✅ Using production database URL")
        
    # Obscure the URL for display
    obscured = re.sub(r'://[^:]+:([^@]+)@', r'://***:***@', actual_db_url)
    print(f"   Connection: {obscured}")
else:
    issues_found.append("DATABASE_URL environment variable not set")
    print("❌ DATABASE_URL not set in environment")
    print("   Will use hardcoded fallback!")

# Step 6: Verify PostgreSQL driver
print("\n📦 Step 6: Verifying PostgreSQL Driver")
print("-" * 70)

try:
    import psycopg2
    print("✅ psycopg2 (PostgreSQL driver) installed")
except ImportError:
    issues_found.append("PostgreSQL driver (psycopg2) not installed")
    print("❌ psycopg2 NOT installed - cannot connect to PostgreSQL")

try:
    import sqlalchemy
    print("✅ SQLAlchemy ORM installed")
except ImportError:
    issues_found.append("SQLAlchemy not installed")
    print("❌ SQLAlchemy NOT installed")

# Step 7: Check for test connection
print("\n🧪 Step 7: Testing Actual Database Connection")
print("-" * 70)

try:
    from backend.database import test_connection
    if test_connection():
        print("✅ Successfully connected to database")
    else:
        issues_found.append("Cannot connect to configured database")
        print("❌ Failed to connect to database")
except Exception as e:
    issues_found.append(f"Database connection error: {str(e)}")
    print(f"❌ Connection test failed: {e}")

# Final Report
print("\n" + "=" * 70)
print("MISCONFIGURATION DETECTION REPORT")
print("=" * 70)

print(f"\n📊 Issues Found: {len(issues_found)}")
if issues_found:
    for i, issue in enumerate(issues_found, 1):
        print(f"   {i}. ❌ {issue}")
else:
    print("   ✅ No critical issues detected")

print(f"\n⚠️  Warnings: {len(warnings_found)}")
if warnings_found:
    for i, warning in enumerate(warnings_found, 1):
        print(f"   {i}. ⚠️  {warning}")
else:
    print("   ✅ No warnings")

# Recommendations
print("\n💡 Recommendations:")
print("-" * 70)

if any('hardcoded' in str(i).lower() for i in issues_found + warnings_found):
    print("1. Remove hardcoded credentials from database.py")
    print("   Suggestion: Use None as fallback, fail fast if missing:")
    print("   DATABASE_URL = os.getenv('DATABASE_URL')")
    print("   if not DATABASE_URL:")
    print("       raise ValueError('DATABASE_URL environment variable required')")

if '.env file missing' in ' '.join(issues_found):
    print("2. Create .env file with DATABASE_URL")

if 'localhost' in str(warnings_found):
    print("3. Update .env with production database URL")

if not issues_found and not warnings_found:
    print("✅ Configuration is secure and correct!")
    print("   • PostgreSQL database configured")
    print("   • Environment variables used properly")
    print("   • No hardcoded credentials in production code")

print("\n" + "=" * 70)

# Exit code
sys.exit(1 if issues_found else 0)
