"""
Evidence Collection Script - PostgreSQL Database Verification
Collects logs, query outputs, and verification results
"""
import sys
import os
from datetime import datetime
sys.path.insert(0, '.')

print("=" * 80)
print("POSTGRESQL DATABASE VERIFICATION - EVIDENCE COLLECTION")
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

from dotenv import load_dotenv
load_dotenv()

# Evidence 1: Environment Configuration
print("\n" + "=" * 80)
print("EVIDENCE 1: ENVIRONMENT CONFIGURATION")
print("=" * 80)

db_url = os.getenv('DATABASE_URL')
if db_url:
    # Obscure credentials
    import re
    obscured = re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', db_url)
    print(f"DATABASE_URL: {obscured}")
    print(f"Database Type: {db_url.split('://')[0]}")
    print(f"Host: {db_url.split('@')[1].split('/')[0] if '@' in db_url else 'N/A'}")
    print(f"Database Name: {db_url.split('/')[-1] if '/' in db_url else 'N/A'}")
    print("✅ PASS: Environment variable loaded")
else:
    print("❌ FAIL: DATABASE_URL not set")
    sys.exit(1)

# Evidence 2: Database Connection Test
print("\n" + "=" * 80)
print("EVIDENCE 2: DATABASE CONNECTION TEST")
print("=" * 80)

from backend.database import engine, test_connection
try:
    success = test_connection()
    if success:
        print("✅ PASS: Database connection successful")
    else:
        print("❌ FAIL: Connection failed")
        sys.exit(1)
except Exception as e:
    print(f"❌ FAIL: Connection error - {e}")
    sys.exit(1)

# Evidence 3: Table Existence Verification
print("\n" + "=" * 80)
print("EVIDENCE 3: TABLE EXISTENCE VERIFICATION")
print("=" * 80)

from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()

print(f"Total tables found: {len(tables)}")
required_tables = [
    'infrastructure_models', 'vpcs', 'ec2_instances', 'rds_databases',
    'load_balancers', 's3_buckets', 'security_groups', 
    'nat_gateways', 'vpc_flow_logs'
]

all_present = True
for table in required_tables:
    status = "✅ EXISTS" if table in tables else "❌ MISSING"
    print(f"  {table:30} {status}")
    if table not in tables:
        all_present = False

if all_present:
    print("\n✅ PASS: All 9 required tables exist")
else:
    print("\n❌ FAIL: Some tables missing")
    sys.exit(1)

# Evidence 4: Query Execution Test
print("\n" + "=" * 80)
print("EVIDENCE 4: QUERY EXECUTION TEST")
print("=" * 80)

from sqlalchemy import text

with engine.connect() as conn:
    # Test 1: Simple SELECT
    print("\nQuery 1: SELECT 1 (Connection test)")
    result = conn.execute(text("SELECT 1 AS test_value"))
    row = result.fetchone()
    print(f"  Result: {row[0]}")
    print("  ✅ PASS: Basic query executed")
    
    # Test 2: Count rows in infrastructure_models
    print("\nQuery 2: SELECT COUNT(*) FROM infrastructure_models")
    result = conn.execute(text("SELECT COUNT(*) FROM infrastructure_models"))
    count = result.scalar()
    print(f"  Result: {count} models")
    print("  ✅ PASS: Table query executed")
    
    # Test 3: Get table columns
    print("\nQuery 3: Show infrastructure_models columns")
    columns = inspector.get_columns('infrastructure_models')
    for col in columns:
        print(f"  - {col['name']:25} {str(col['type']):20}")
    print("  ✅ PASS: Schema introspection works")

# Evidence 5: CRUD Operations Test
print("\n" + "=" * 80)
print("EVIDENCE 5: CRUD OPERATIONS TEST")
print("=" * 80)

from backend.database import SessionLocal
from backend.repository import InfrastructureRepository
from backend.model import InfrastructureModel, VPC, Subnet, SubnetType

db = SessionLocal()
repo = InfrastructureRepository(db)

# CREATE
print("\n[CREATE] Inserting test model...")
test_id = f"evidence-test-{datetime.now().strftime('%Y%m%d%H%M%S')}"
model = InfrastructureModel(model_id=test_id)
vpc = VPC(id='vpc-evidence', name='Evidence VPC', cidr='10.99.0.0/16')
vpc.subnets.append(Subnet(
    id='subnet-evidence',
    name='Evidence Subnet',
    cidr='10.99.1.0/24',
    subnet_type=SubnetType.PUBLIC
))
model.add_vpc(vpc)

saved_id = repo.save_model(model)
print(f"  Model saved: {saved_id}")
print("  ✅ PASS: CREATE operation successful")

# READ
print("\n[READ] Retrieving test model...")
retrieved = repo.get_model(test_id)
if retrieved:
    print(f"  Retrieved: {retrieved.model_id}")
    print(f"  VPCs: {len(retrieved.vpcs)}")
    print(f"  Subnets: {len(retrieved.vpcs[0].subnets)}")
    print("  ✅ PASS: READ operation successful")
else:
    print("  ❌ FAIL: Could not retrieve model")
    db.close()
    sys.exit(1)

# UPDATE
print("\n[UPDATE] Updating model...")
retrieved.vpcs[0].name = "Updated Evidence VPC"
repo.save_model(retrieved)
updated = repo.get_model(test_id)
if updated.vpcs[0].name == "Updated Evidence VPC":
    print(f"  Updated name: {updated.vpcs[0].name}")
    print("  ✅ PASS: UPDATE operation successful")
else:
    print("  ❌ FAIL: Update not persisted")
    db.close()
    sys.exit(1)

# DELETE
print("\n[DELETE] Deleting test model...")
deleted = repo.delete_model(test_id)
if deleted:
    print(f"  Model deleted: {test_id}")
    verify_gone = repo.get_model(test_id)
    if not verify_gone:
        print("  ✅ PASS: DELETE operation successful")
    else:
        print("  ❌ FAIL: Model still exists after delete")
        db.close()
        sys.exit(1)
else:
    print("  ❌ FAIL: Delete operation failed")
    db.close()
    sys.exit(1)

db.close()

# Evidence 6: Persistence Across Sessions
print("\n" + "=" * 80)
print("EVIDENCE 6: PERSISTENCE ACROSS SESSIONS TEST")
print("=" * 80)

print("\n[Session 1] Creating test data...")
db1 = SessionLocal()
repo1 = InfrastructureRepository(db1)
persist_id = f"persist-{datetime.now().strftime('%Y%m%d%H%M%S')}"
persist_model = InfrastructureModel(model_id=persist_id)
persist_model.add_vpc(VPC(id='vpc-p', name='Persist VPC', cidr='10.88.0.0/16'))
repo1.save_model(persist_model)
print(f"  Created model: {persist_id}")
db1.close()
print("  Session 1 closed")

print("\n[Session 2] Retrieving data (simulated restart)...")
db2 = SessionLocal()
repo2 = InfrastructureRepository(db2)
retrieved_persist = repo2.get_model(persist_id)
if retrieved_persist:
    print(f"  Retrieved model: {retrieved_persist.model_id}")
    print(f"  VPCs: {len(retrieved_persist.vpcs)}")
    print("  ✅ PASS: Data persists across sessions")
    
    # Cleanup
    repo2.delete_model(persist_id)
    db2.close()
else:
    print("  ❌ FAIL: Data not found in new session")
    db2.close()
    sys.exit(1)

# Evidence 7: Foreign Key Relationships
print("\n" + "=" * 80)
print("EVIDENCE 7: FOREIGN KEY RELATIONSHIPS VERIFICATION")
print("=" * 80)

fk_count = 0
for table in required_tables:
    if table == 'infrastructure_models':
        continue
    fks = inspector.get_foreign_keys(table)
    for fk in fks:
        print(f"  {table:25} → {fk['referred_table']:25}")
        fk_count += 1

print(f"\nTotal foreign keys: {fk_count}")
if fk_count >= 8:
    print("✅ PASS: Foreign key relationships configured")
else:
    print("❌ FAIL: Missing foreign keys")
    sys.exit(1)

# Evidence 8: Primary Keys
print("\n" + "=" * 80)
print("EVIDENCE 8: PRIMARY KEYS VERIFICATION")
print("=" * 80)

pk_issues = []
for table in required_tables:
    pk = inspector.get_pk_constraint(table)
    if pk and pk['constrained_columns']:
        print(f"  {table:30} PK: {pk['constrained_columns']}")
    else:
        print(f"  {table:30} ❌ NO PRIMARY KEY")
        pk_issues.append(table)

if not pk_issues:
    print("\n✅ PASS: All tables have primary keys")
else:
    print(f"\n❌ FAIL: {len(pk_issues)} tables missing primary keys")
    sys.exit(1)

# Final Summary
print("\n" + "=" * 80)
print("VERIFICATION SUMMARY")
print("=" * 80)

evidence_results = {
    "Environment Configuration": "✅ PASS",
    "Database Connection": "✅ PASS",
    "Table Existence (9/9)": "✅ PASS",
    "Query Execution": "✅ PASS",
    "CRUD Operations": "✅ PASS",
    "Session Persistence": "✅ PASS",
    "Foreign Key Relationships": "✅ PASS",
    "Primary Keys": "✅ PASS"
}

print("\nTest Results:")
for test, result in evidence_results.items():
    print(f"  {test:35} {result}")

print("\n" + "=" * 80)
print("🎉 ALL TESTS PASSED - DATABASE FULLY OPERATIONAL")
print("=" * 80)

print("\nDatabase Details:")
print(f"  Provider: Render (Cloud PostgreSQL)")
print(f"  Tables: 9/9 present")
print(f"  Foreign Keys: {fk_count} configured")
print(f"  CRUD Operations: All working")
print(f"  Persistence: Verified across sessions")

print("\n✅ FINAL VERDICT: PASS")
print("   PostgreSQL database is properly configured and fully functional.")
print("=" * 80)
