"""
SQLAlchemy ORM Models for Infrastructure Storage
Maps infrastructure models to PostgreSQL database tables.
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base


class InfrastructureModelDB(Base):
    """
    Main table for storing infrastructure models.
    Stores the model metadata and edit tracking information.
    """
    __tablename__ = "infrastructure_models"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(String(100), unique=True, nullable=False, index=True)
    last_edit_source = Column(String(50), nullable=False, default="initial")
    last_edit_timestamp = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships to resource tables
    vpcs = relationship("VPCRecord", back_populates="infrastructure_model", cascade="all, delete-orphan")
    ec2_instances = relationship("EC2InstanceRecord", back_populates="infrastructure_model", cascade="all, delete-orphan")
    rds_databases = relationship("RDSDatabaseRecord", back_populates="infrastructure_model", cascade="all, delete-orphan")
    load_balancers = relationship("LoadBalancerRecord", back_populates="infrastructure_model", cascade="all, delete-orphan")
    s3_buckets = relationship("S3BucketRecord", back_populates="infrastructure_model", cascade="all, delete-orphan")
    security_groups = relationship("SecurityGroupRecord", back_populates="infrastructure_model", cascade="all, delete-orphan")
    nat_gateways = relationship("NATGatewayRecord", back_populates="infrastructure_model", cascade="all, delete-orphan")
    flow_logs = relationship("VPCFlowLogsRecord", back_populates="infrastructure_model", cascade="all, delete-orphan")


class VPCRecord(Base):
    """VPC storage table"""
    __tablename__ = "vpcs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    infrastructure_model_id = Column(Integer, ForeignKey("infrastructure_models.id"), nullable=False)
    vpc_id = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    cidr = Column(String(50), nullable=False)
    subnets = Column(JSON, nullable=False, default=[])  # Store subnets as JSON array
    
    infrastructure_model = relationship("InfrastructureModelDB", back_populates="vpcs")


class EC2InstanceRecord(Base):
    """EC2 instance storage table"""
    __tablename__ = "ec2_instances"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    infrastructure_model_id = Column(Integer, ForeignKey("infrastructure_models.id"), nullable=False)
    instance_id = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    instance_type = Column(String(50), nullable=False)
    subnet_id = Column(String(100), nullable=False)
    ami = Column(String(100), nullable=False)
    
    infrastructure_model = relationship("InfrastructureModelDB", back_populates="ec2_instances")


class RDSDatabaseRecord(Base):
    """RDS database storage table"""
    __tablename__ = "rds_databases"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    infrastructure_model_id = Column(Integer, ForeignKey("infrastructure_models.id"), nullable=False)
    database_id = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    engine = Column(String(50), nullable=False)
    instance_class = Column(String(50), nullable=False)
    subnet_ids = Column(JSON, nullable=False, default=[])  # Store as JSON array
    allocated_storage = Column(Integer, nullable=False, default=20)
    
    infrastructure_model = relationship("InfrastructureModelDB", back_populates="rds_databases")


class LoadBalancerRecord(Base):
    """Load balancer storage table"""
    __tablename__ = "load_balancers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    infrastructure_model_id = Column(Integer, ForeignKey("infrastructure_models.id"), nullable=False)
    lb_id = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    subnet_ids = Column(JSON, nullable=False, default=[])
    target_instance_ids = Column(JSON, nullable=False, default=[])
    
    infrastructure_model = relationship("InfrastructureModelDB", back_populates="load_balancers")


class S3BucketRecord(Base):
    """S3 bucket storage table"""
    __tablename__ = "s3_buckets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    infrastructure_model_id = Column(Integer, ForeignKey("infrastructure_models.id"), nullable=False)
    bucket_id = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    versioning_enabled = Column(Boolean, nullable=False, default=False)
    encryption_enabled = Column(Boolean, nullable=False, default=True)
    
    infrastructure_model = relationship("InfrastructureModelDB", back_populates="s3_buckets")


class SecurityGroupRecord(Base):
    """Security group storage table"""
    __tablename__ = "security_groups"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    infrastructure_model_id = Column(Integer, ForeignKey("infrastructure_models.id"), nullable=False)
    sg_id = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    vpc_id = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    ingress_rules = Column(JSON, nullable=False, default=[])
    egress_rules = Column(JSON, nullable=False, default=[])
    
    infrastructure_model = relationship("InfrastructureModelDB", back_populates="security_groups")


class NATGatewayRecord(Base):
    """NAT Gateway storage table"""
    __tablename__ = "nat_gateways"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    infrastructure_model_id = Column(Integer, ForeignKey("infrastructure_models.id"), nullable=False)
    nat_id = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    subnet_id = Column(String(100), nullable=False)
    elastic_ip = Column(String(100), nullable=True)
    
    infrastructure_model = relationship("InfrastructureModelDB", back_populates="nat_gateways")


class VPCFlowLogsRecord(Base):
    """VPC Flow Logs storage table"""
    __tablename__ = "vpc_flow_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    infrastructure_model_id = Column(Integer, ForeignKey("infrastructure_models.id"), nullable=False)
    flow_log_id = Column(String(100), nullable=False)
    vpc_id = Column(String(100), nullable=False)
    log_destination_type = Column(String(50), nullable=False, default="cloud-watch-logs")
    traffic_type = Column(String(20), nullable=False, default="ALL")
    log_group_name = Column(String(255), nullable=True)
    
    infrastructure_model = relationship("InfrastructureModelDB", back_populates="flow_logs")
