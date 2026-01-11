"""
Test script to verify diagram improvements
"""
import sys
sys.path.insert(0, '.')

from backend.model import InfrastructureModel, VPC, EC2Instance, RDSDatabase, LoadBalancer, InstanceType, DatabaseEngine
from backend.diagram import generate_mermaid_diagram

print("=" * 70)
print("DIAGRAM IMPROVEMENTS TEST")
print("=" * 70)

# Create test model with multiple resources
model = InfrastructureModel(model_id="test-diagram")

# Add VPC
vpc = VPC(id="vpc-1", name="Main VPC", cidr="10.0.0.0/16")
model.add_vpc(vpc)

# Add multiple EC2 instances
for i in range(5):
    ec2 = EC2Instance(
        id=f"ec2-{i+1}",
        name=f"web-server-with-very-long-name-{i+1}",  # Long name to test truncation
        instance_type=InstanceType.T2_MICRO,
        subnet_id="subnet-1"
    )
    model.add_ec2(ec2)

# Add RDS
rds = RDSDatabase(
    id="rds-1",
    name="production-postgresql-database",  # Long name
    engine=DatabaseEngine.POSTGRES,
    instance_class="db.t3.micro",
    subnet_ids=["subnet-2", "subnet-3"]
)
model.add_rds(rds)

# Add Load Balancer with many targets (tests connection optimization)
lb = LoadBalancer(
    id="lb-1",
    name="main-application-load-balancer",
    subnet_ids=["subnet-1"],
    target_instance_ids=["ec2-1", "ec2-2", "ec2-3", "ec2-4", "ec2-5"]
)
model.add_load_balancer(lb)

# Generate diagram
print("\n📊 Generating diagram...")
diagram = generate_mermaid_diagram(model)

print("\n✅ Generated Mermaid Diagram:")
print("-" * 70)
print(diagram)
print("-" * 70)

# Check improvements
print("\n🔍 Verification:")
print()

# Check 1: Spacing configuration
if "nodeSpacing" in diagram:
    print("✅ Spacing configuration added")
else:
    print("❌ Spacing configuration missing")

# Check 2: Truncated labels
if "..." in diagram:
    print("✅ Long text truncation working")
else:
    print("⚠️  No truncation detected (may be OK if all names short)")

# Check 3: Connection optimization
connection_count = diagram.count("==>")
print(f"   Total connections shown: {connection_count}")
if "more connections" in diagram:
    print("✅ Connection optimization working (note added)")
elif connection_count <= 3:
    print("✅ Connection optimization working (≤3 connections)")
else:
    print(f"⚠️  {connection_count} connections shown (expected max 3)")

# Check 4: Consistent node format
lines_with_br = [line for line in diagram.split('\n') if '<br/>' in line and '[' in line]
print(f"\n   Nodes with <br/> formatting: {len(lines_with_br)}")
if lines_with_br:
    print("   Sample node:")
    print(f"   {lines_with_br[0]}")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
