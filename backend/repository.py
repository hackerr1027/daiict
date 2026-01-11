"""
Repository Pattern for Infrastructure Model Persistence
Handles conversion between dataclasses and SQLAlchemy models, and all database operations.
"""

import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

from backend.model import (
    InfrastructureModel, VPC, EC2Instance, RDSDatabase, LoadBalancer,
    S3Bucket, SecurityGroup, NATGateway, VPCFlowLogs, Subnet,
    EditSource, SubnetType, InstanceType, DatabaseEngine
)
from backend.db_models import (
    InfrastructureModelDB, VPCRecord, EC2InstanceRecord, RDSDatabaseRecord,
    LoadBalancerRecord, S3BucketRecord, SecurityGroupRecord,
    NATGatewayRecord, VPCFlowLogsRecord
)

logger = logging.getLogger(__name__)


class InfrastructureRepository:
    """Repository for infrastructure model database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def save_model(self, model: InfrastructureModel) -> str:
        """
        Save or update an infrastructure model to the database.
        Returns the model_id.
        """
        try:
            # Check if model already exists
            existing = self.db.query(InfrastructureModelDB).filter(
                InfrastructureModelDB.model_id == model.model_id
            ).first()
            
            if existing:
                # Update existing model
                self._update_model_record(existing, model)
            else:
                # Create new model
                model_record = self._create_model_record(model)
                self.db.add(model_record)
            
            self.db.commit()
            return model.model_id
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database save failed for model {model.model_id}: {e}", exc_info=True)
            # Re-raise with user-friendly message (global handler will catch it)
            raise Exception("Unable to save infrastructure model. Please try again.")
    
    def get_model(self, model_id: str) -> Optional[InfrastructureModel]:
        """
        Retrieve an infrastructure model by ID.
        Returns None if not found.
        """
        try:
            model_record = self.db.query(InfrastructureModelDB).filter(
                InfrastructureModelDB.model_id == model_id
            ).first()
            
            if not model_record:
                return None
            
            return self._record_to_model(model_record)
            
        except SQLAlchemyError as e:
            logger.error(f"Database retrieval failed for model {model_id}: {e}", exc_info=True)
            raise Exception("Unable to retrieve infrastructure model. Please try again.")
    
    def delete_model(self, model_id: str) -> bool:
        """
        Delete an infrastructure model by ID.
        Returns True if deleted, False if not found.
        """
        try:
            model_record = self.db.query(InfrastructureModelDB).filter(
                InfrastructureModelDB.model_id == model_id
            ).first()
            
            if not model_record:
                return False
            
            self.db.delete(model_record)
            self.db.commit()
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database deletion failed for model {model_id}: {e}", exc_info=True)
            raise Exception("Unable to delete infrastructure model. Please try again.")
    
    def list_models(self, limit: int = 100, offset: int = 0) -> List[InfrastructureModel]:
        """
        List all infrastructure models with pagination.
        """
        try:
            records = self.db.query(InfrastructureModelDB).order_by(
                InfrastructureModelDB.created_at.desc()
            ).limit(limit).offset(offset).all()
            
            return [self._record_to_model(record) for record in records]
            
        except SQLAlchemyError as e:
            logger.error(f"Database list failed: {e}", exc_info=True)
            raise Exception("Unable to retrieve infrastructure models. Please try again.")
    
    def _create_model_record(self, model: InfrastructureModel) -> InfrastructureModelDB:
        """Convert InfrastructureModel to database record"""
        model_record = InfrastructureModelDB(
            model_id=model.model_id,
            last_edit_source=model.last_edit_source.value,
            last_edit_timestamp=model.last_edit_timestamp
        )
        
        # Add all resources
        for vpc in model.vpcs:
            model_record.vpcs.append(self._vpc_to_record(vpc))
        
        for ec2 in model.ec2_instances:
            model_record.ec2_instances.append(self._ec2_to_record(ec2))
        
        for rds in model.rds_databases:
            model_record.rds_databases.append(self._rds_to_record(rds))
        
        for lb in model.load_balancers:
            model_record.load_balancers.append(self._lb_to_record(lb))
        
        for bucket in model.s3_buckets:
            model_record.s3_buckets.append(self._s3_to_record(bucket))
        
        for sg in model.security_groups:
            model_record.security_groups.append(self._sg_to_record(sg))
        
        for nat in model.nat_gateways:
            model_record.nat_gateways.append(self._nat_to_record(nat))
        
        for logs in model.flow_logs:
            model_record.flow_logs.append(self._logs_to_record(logs))
        
        return model_record
    
    def _update_model_record(self, record: InfrastructureModelDB, model: InfrastructureModel):
        """Update existing database record with new model data"""
        # Update metadata
        record.last_edit_source = model.last_edit_source.value
        record.last_edit_timestamp = model.last_edit_timestamp
        record.updated_at = datetime.utcnow()
        
        # Clear existing resources (cascade delete will handle related records)
        record.vpcs.clear()
        record.ec2_instances.clear()
        record.rds_databases.clear()
        record.load_balancers.clear()
        record.s3_buckets.clear()
        record.security_groups.clear()
        record.nat_gateways.clear()
        record.flow_logs.clear()
        
        # Add updated resources
        for vpc in model.vpcs:
            record.vpcs.append(self._vpc_to_record(vpc))
        
        for ec2 in model.ec2_instances:
            record.ec2_instances.append(self._ec2_to_record(ec2))
        
        for rds in model.rds_databases:
            record.rds_databases.append(self._rds_to_record(rds))
        
        for lb in model.load_balancers:
            record.load_balancers.append(self._lb_to_record(lb))
        
        for bucket in model.s3_buckets:
            record.s3_buckets.append(self._s3_to_record(bucket))
        
        for sg in model.security_groups:
            record.security_groups.append(self._sg_to_record(sg))
        
        for nat in model.nat_gateways:
            record.nat_gateways.append(self._nat_to_record(nat))
        
        for logs in model.flow_logs:
            record.flow_logs.append(self._logs_to_record(logs))
    
    def _record_to_model(self, record: InfrastructureModelDB) -> InfrastructureModel:
        """Convert database record to InfrastructureModel dataclass"""
        model = InfrastructureModel(
            model_id=record.model_id,
            last_edit_source=EditSource(record.last_edit_source),
            last_edit_timestamp=record.last_edit_timestamp
        )
        
        # Convert all resources
        for vpc_record in record.vpcs:
            model.vpcs.append(self._record_to_vpc(vpc_record))
        
        for ec2_record in record.ec2_instances:
            model.ec2_instances.append(self._record_to_ec2(ec2_record))
        
        for rds_record in record.rds_databases:
            model.rds_databases.append(self._record_to_rds(rds_record))
        
        for lb_record in record.load_balancers:
            model.load_balancers.append(self._record_to_lb(lb_record))
        
        for bucket_record in record.s3_buckets:
            model.s3_buckets.append(self._record_to_s3(bucket_record))
        
        for sg_record in record.security_groups:
            model.security_groups.append(self._record_to_sg(sg_record))
        
        for nat_record in record.nat_gateways:
            model.nat_gateways.append(self._record_to_nat(nat_record))
        
        for logs_record in record.flow_logs:
            model.flow_logs.append(self._record_to_logs(logs_record))
        
        return model
    
    # Resource conversion helpers - Model to Record
    
    def _vpc_to_record(self, vpc: VPC) -> VPCRecord:
        """Convert VPC dataclass to database record"""
        return VPCRecord(
            vpc_id=vpc.id,
            name=vpc.name,
            cidr=vpc.cidr,
            subnets=[{
                "id": s.id,
                "name": s.name,
                "cidr": s.cidr,
                "subnet_type": s.subnet_type.value,
                "availability_zone": s.availability_zone
            } for s in vpc.subnets]
        )
    
    def _ec2_to_record(self, ec2: EC2Instance) -> EC2InstanceRecord:
        """Convert EC2Instance dataclass to database record"""
        return EC2InstanceRecord(
            instance_id=ec2.id,
            name=ec2.name,
            instance_type=ec2.instance_type.value,
            subnet_id=ec2.subnet_id,
            ami=ec2.ami
        )
    
    def _rds_to_record(self, rds: RDSDatabase) -> RDSDatabaseRecord:
        """Convert RDSDatabase dataclass to database record"""
        return RDSDatabaseRecord(
            database_id=rds.id,
            name=rds.name,
            engine=rds.engine.value,
            instance_class=rds.instance_class,
            subnet_ids=rds.subnet_ids,
            allocated_storage=rds.allocated_storage
        )
    
    def _lb_to_record(self, lb: LoadBalancer) -> LoadBalancerRecord:
        """Convert LoadBalancer dataclass to database record"""
        return LoadBalancerRecord(
            lb_id=lb.id,
            name=lb.name,
            subnet_ids=lb.subnet_ids,
            target_instance_ids=lb.target_instance_ids
        )
    
    def _s3_to_record(self, bucket: S3Bucket) -> S3BucketRecord:
        """Convert S3Bucket dataclass to database record"""
        return S3BucketRecord(
            bucket_id=bucket.id,
            name=bucket.name,
            versioning_enabled=bucket.versioning_enabled,
            encryption_enabled=bucket.encryption_enabled
        )
    
    def _sg_to_record(self, sg: SecurityGroup) -> SecurityGroupRecord:
        """Convert SecurityGroup dataclass to database record"""
        return SecurityGroupRecord(
            sg_id=sg.id,
            name=sg.name,
            vpc_id=sg.vpc_id,
            description=sg.description,
            ingress_rules=sg.ingress_rules,
            egress_rules=sg.egress_rules
        )
    
    def _nat_to_record(self, nat: NATGateway) -> NATGatewayRecord:
        """Convert NATGateway dataclass to database record"""
        return NATGatewayRecord(
            nat_id=nat.id,
            name=nat.name,
            subnet_id=nat.subnet_id,
            elastic_ip=nat.elastic_ip
        )
    
    def _logs_to_record(self, logs: VPCFlowLogs) -> VPCFlowLogsRecord:
        """Convert VPCFlowLogs dataclass to database record"""
        return VPCFlowLogsRecord(
            flow_log_id=logs.id,
            vpc_id=logs.vpc_id,
            log_destination_type=logs.log_destination_type,
            traffic_type=logs.traffic_type,
            log_group_name=logs.log_group_name
        )
    
    # Resource conversion helpers - Record to Model
    
    def _record_to_vpc(self, record: VPCRecord) -> VPC:
        """Convert database record to VPC dataclass"""
        vpc = VPC(
            id=record.vpc_id,
            name=record.name,
            cidr=record.cidr
        )
        # Add subnets
        for subnet_data in record.subnets:
            vpc.subnets.append(Subnet(
                id=subnet_data["id"],
                name=subnet_data["name"],
                cidr=subnet_data["cidr"],
                subnet_type=SubnetType(subnet_data["subnet_type"]),
                availability_zone=subnet_data.get("availability_zone", "us-east-1a")
            ))
        return vpc
    
    def _record_to_ec2(self, record: EC2InstanceRecord) -> EC2Instance:
        """Convert database record to EC2Instance dataclass"""
        return EC2Instance(
            id=record.instance_id,
            name=record.name,
            instance_type=InstanceType(record.instance_type),
            subnet_id=record.subnet_id,
            ami=record.ami
        )
    
    def _record_to_rds(self, record: RDSDatabaseRecord) -> RDSDatabase:
        """Convert database record to RDSDatabase dataclass"""
        return RDSDatabase(
            id=record.database_id,
            name=record.name,
            engine=DatabaseEngine(record.engine),
            instance_class=record.instance_class,
            subnet_ids=record.subnet_ids,
            allocated_storage=record.allocated_storage
        )
    
    def _record_to_lb(self, record: LoadBalancerRecord) -> LoadBalancer:
        """Convert database record to LoadBalancer dataclass"""
        return LoadBalancer(
            id=record.lb_id,
            name=record.name,
            subnet_ids=record.subnet_ids,
            target_instance_ids=record.target_instance_ids
        )
    
    def _record_to_s3(self, record: S3BucketRecord) -> S3Bucket:
        """Convert database record to S3Bucket dataclass"""
        return S3Bucket(
            id=record.bucket_id,
            name=record.name,
            versioning_enabled=record.versioning_enabled,
            encryption_enabled=record.encryption_enabled
        )
    
    def _record_to_sg(self, record: SecurityGroupRecord) -> SecurityGroup:
        """Convert database record to SecurityGroup dataclass"""
        return SecurityGroup(
            id=record.sg_id,
            name=record.name,
            vpc_id=record.vpc_id,
            description=record.description,
            ingress_rules=record.ingress_rules,
            egress_rules=record.egress_rules
        )
    
    def _record_to_nat(self, record: NATGatewayRecord) -> NATGateway:
        """Convert database record to NATGateway dataclass"""
        return NATGateway(
            id=record.nat_id,
            name=record.name,
            subnet_id=record.subnet_id,
            elastic_ip=record.elastic_ip
        )
    
    def _record_to_logs(self, record: VPCFlowLogsRecord) -> VPCFlowLogs:
        """Convert database record to VPCFlowLogs dataclass"""
        return VPCFlowLogs(
            id=record.flow_log_id,
            vpc_id=record.vpc_id,
            log_destination_type=record.log_destination_type,
            traffic_type=record.traffic_type,
            log_group_name=record.log_group_name
        )
