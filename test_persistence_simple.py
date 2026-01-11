"""
Simple persistence validation - insert and retrieve data
"""
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from backend.database import SessionLocal, init_db
from backend.repository import InfrastructureRepository
from backend.model import InfrastructureModel, VPC, Subnet, SubnetType, EC2Instance, InstanceType

print("=" * 60)
print("PERSISTENCE VALIDATION TEST")
print("=" * 60)

# Initialize database
print("\n1. Initializing database...")
init_db()
print("✅ Database ready")

# Insert data
print("\n2. Inserting test data...")
db = SessionLocal()
repo = InfrastructureRepository(db)

model = InfrastructureModel(model_id='persist-test-001')
vpc = VPC(id='vpc-1', name='Test VPC', cidr='10.0.0.0/16')
vpc.subnets.append(Subnet(
    id='subnet-1',
    name='Public Subnet',
    cidr='10.0.1.0/24',
    subnet_type=SubnetType.PUBLIC
))
model.add_vpc(vpc)
model.add_ec2(EC2Instance(
    id='ec2-1',
    name='Web Server',
    instance_type=InstanceType.T2_MICRO,
    subnet_id='subnet-1'
))

repo.save_model(model)
print(f"✅ Saved model: {model.model_id}")
print(f"   - VPCs: {len(model.vpcs)}")
print(f"   - EC2 Instances: {len(model.ec2_instances)}")
db.close()

# Retrieve data (simulating restart)
print("\n3. Simulating restart - creating new session...")
db_new = SessionLocal()
repo_new = InfrastructureRepository(db_new)

retrieved = repo_new.get_model('persist-test-001')
if retrieved:
    print(f"✅ Retrieved model: {retrieved.model_id}")
    print(f"   - VPCs: {len(retrieved.vpcs)}")
    print(f"   - Subnets: {len(retrieved.vpcs[0].subnets)}")
    print(f"   - EC2 Instances: {len(retrieved.ec2_instances)}")
    print(f"\n🎉 PERSISTENCE VERIFIED!")
    print(f"   Data survived session restart")
else:
    print("❌ FAILED: Could not retrieve model")
    sys.exit(1)

db_new.close()

# List all models
print("\n4. Listing all models in database...")
db = SessionLocal()
repo = InfrastructureRepository(db)
all_models = repo.list_models(limit=10)
print(f"✅ Total models in database: {len(all_models)}")
for m in all_models:
    print(f"   - {m.model_id}")
db.close()

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED - DATABASE PERSISTENCE WORKING!")
print("=" * 60)
