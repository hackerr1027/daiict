"""
Quick Test Script for PostgreSQL Database Integration
Run this to verify database setup and connection
"""

import os
import sys

# Set up path to import backend modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_database_integration():
    """Test all aspects of database integration"""
    print("=" * 60)
    print("PostgreSQL Database Integration Test")
    print("=" * 60)
    
    # Step 1: Test connection
    print("\n1️⃣  Testing database connection...")
    try:
        from backend.database import test_connection, init_db
        if test_connection():
            print("   ✅ Database connection successful")
        else:
            print("   ❌ Database connection failed")
            print("\n⚠️  Please check your DATABASE_URL in .env file")
            print("   See DATABASE_SETUP.md for configuration help")
            return False
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        print("\n⚠️  Make sure PostgreSQL is running and DATABASE_URL is set")
        return False
    
    # Step 2: Initialize database
    print("\n2️⃣  Initializing database tables...")
    try:
        init_db()
        print("   ✅ Database tables created/verified")
    except Exception as e:
        print(f"   ❌ Table creation error: {e}")
        return False
    
    # Step 3: Test repository operations
    print("\n3️⃣  Testing repository operations...")
    try:
        from backend.database import SessionLocal
        from backend.repository import InfrastructureRepository
        from backend.model import InfrastructureModel, VPC, EC2Instance, Subnet, SubnetType, InstanceType
        
        db = SessionLocal()
        try:
            repo = InfrastructureRepository(db)
            
            # Create test model
            test_model = InfrastructureModel(model_id="test-model-001")
            vpc = VPC(id="vpc-1", name="Test VPC", cidr="10.0.0.0/16")
            vpc.subnets.append(Subnet(
                id="subnet-1", 
                name="Public Subnet", 
                cidr="10.0.1.0/24",
                subnet_type=SubnetType.PUBLIC
            ))
            test_model.add_vpc(vpc)
            test_model.add_ec2(EC2Instance(
                id="ec2-1",
                name="Web Server",
                instance_type=InstanceType.T2_MICRO,
                subnet_id="subnet-1"
            ))
            
            # Test SAVE
            print("   📝 Testing SAVE operation...")
            model_id = repo.save_model(test_model)
            print(f"   ✅ Model saved: {model_id}")
            
            # Test GET
            print("   📖 Testing GET operation...")
            retrieved_model = repo.get_model(model_id)
            if retrieved_model:
                print(f"   ✅ Model retrieved: {retrieved_model.model_id}")
                print(f"      - VPCs: {len(retrieved_model.vpcs)}")
                print(f"      - EC2 Instances: {len(retrieved_model.ec2_instances)}")
            else:
                print("   ❌ Model not found")
                return False
            
            # Test LIST
            print("   📋 Testing LIST operation...")
            models = repo.list_models(limit=10)
            print(f"   ✅ Found {len(models)} model(s) in database")
            
            # Test DELETE
            print("   🗑️  Testing DELETE operation...")
            deleted = repo.delete_model(model_id)
            if deleted:
                print("   ✅ Model deleted successfully")
            else:
                print("   ❌ Delete failed")
                return False
            
        finally:
            db.close()
            
        print("\n   ✅ All repository operations working correctly!")
        
    except Exception as e:
        print(f"   ❌ Repository test error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Success!
    print("\n" + "=" * 60)
    print("✅ All tests passed! Database integration is working!")
    print("=" * 60)
    print("\n💡 Next steps:")
    print("   1. Start the backend: uvicorn backend.main:app --reload")
    print("   2. Test via API or frontend application")
    print("   3. Models will now persist across server restarts!")
    print("\n")
    return True


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check if DATABASE_URL is set
    if not os.getenv("DATABASE_URL"):
        print("⚠️  DATABASE_URL not found in environment")
        print("   Please create a .env file with your database connection")
        print("   See DATABASE_SETUP.md for instructions")
        sys.exit(1)
    
    # Run tests
    success = test_database_integration()
    sys.exit(0 if success else 1)
