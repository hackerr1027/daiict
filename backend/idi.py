"""
Infrastructure Decision Intelligence (IDI)
Generates decision cards explaining WHY architectural choices were made.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from .model import InfrastructureModel, SubnetType


@dataclass
class DecisionCard:
    """Represents a single architectural decision with rationale and impact."""
    id: str
    title: str
    why: str
    risk_reduced: str
    risk_level: str  # "Low" | "Medium" | "High"
    tradeoff: str
    cost_impact: str
    confidence: str  # "Low" | "Medium" | "High"
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "why": self.why,
            "riskReduced": self.risk_reduced,
            "riskLevel": self.risk_level,
            "tradeoff": self.tradeoff,
            "costImpact": self.cost_impact,
            "confidence": self.confidence
        }


@dataclass
class DecisionReport:
    """Complete decision intelligence report for infrastructure."""
    decisions: List[DecisionCard] = field(default_factory=list)
    total_monthly_cost_estimate: str = "$0/month"
    architecture_complexity: str = "Simple"
    cost_breakdown: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "decisions": [d.to_dict() for d in self.decisions],
            "totalMonthlyCostEstimate": self.total_monthly_cost_estimate,
            "architectureComplexity": self.architecture_complexity,
            "costBreakdown": self.cost_breakdown
        }


def generate_decision_intelligence(model: InfrastructureModel) -> DecisionReport:
    """
    Analyze infrastructure model and generate decision intelligence report.
    
    This is rule-based and deterministic - no LLM required.
    """
    print("🎯 [IDI] Generating decision intelligence...")
    
    report = DecisionReport()
    
    # Detect all architectural decisions
    report.decisions = detect_decisions(model)
    
    # Calculate cost estimates
    cost_data = estimate_monthly_cost(model)
    report.total_monthly_cost_estimate = cost_data["total"]
    report.cost_breakdown = cost_data["breakdown"]
    
    # Determine architecture complexity
    report.architecture_complexity = determine_complexity(model)
    
    print(f"✅ [IDI] Generated {len(report.decisions)} decision cards")
    
    return report


def detect_decisions(model: InfrastructureModel) -> List[DecisionCard]:
    """Detect architectural decisions from infrastructure model."""
    decisions = []
    
    # Helper: Check if resource is in private subnet
    def is_in_private_subnet(subnet_id: str) -> bool:
        subnet = model.get_subnet_by_id(subnet_id)
        return subnet and subnet.subnet_type == SubnetType.PRIVATE
    
    # Decision 1: EC2 in Private Subnet
    private_ec2 = [ec2 for ec2 in model.ec2_instances if is_in_private_subnet(ec2.subnet_id)]
    if private_ec2:
        decisions.append(DecisionCard(
            id="private-subnet-ec2",
            title="EC2 Instances in Private Subnet",
            why="Reduces public attack surface by isolating compute resources from direct internet access. Only the load balancer is exposed publicly.",
            risk_reduced="Prevents direct exploitation of application vulnerabilities and unauthorized access to compute instances",
            risk_level="High",
            tradeoff="Requires NAT Gateway for outbound internet access (updates, external APIs)",
            cost_impact="+$32/month (NAT Gateway)",
            confidence="High (industry best practice)"
        ))
    
    # Decision 2: Load Balancer
    if model.load_balancers:
        lb_count = len(model.load_balancers)
        decisions.append(DecisionCard(
            id="load-balancer",
            title=f"Application Load Balancer{'s' if lb_count > 1 else ''} Added",
            why="Enables horizontal scalability, fault tolerance, SSL termination, and distributes traffic across multiple instances",
            risk_reduced="Improves availability and prevents single point of failure",
            risk_level="Medium",
            tradeoff="Increased complexity and additional component to manage",
            cost_impact=f"+${lb_count * 18}/month (ALB base cost)",
            confidence="High"
        ))
    
    # Decision 3: Database in Private Subnet
    private_rds = [rds for rds in model.rds_databases 
                   if all(is_in_private_subnet(sid) for sid in rds.subnet_ids)]
    if private_rds:
        decisions.append(DecisionCard(
            id="database-isolation",
            title="Database in Isolated Private Subnet",
            why="Prevents direct database access from the internet. Only application servers within the VPC can connect.",
            risk_reduced="Eliminates risk of unauthorized database connections and data breaches",
            risk_level="High",
            tradeoff="Requires application servers in VPC to access database (cannot connect from local machine without VPN)",
            cost_impact="$0 (no additional cost)",
            confidence="High (security requirement)"
        ))
    
    # Decision 4: Multi-AZ Database
    multi_az_rds = [rds for rds in model.rds_databases if getattr(rds, 'multi_az', False)]
    if multi_az_rds:
        decisions.append(DecisionCard(
            id="multi-az-database",
            title="Multi-AZ Database Deployment",
            why="Provides automatic failover to standby replica in different availability zone for high availability",
            risk_reduced="Protects against availability zone failures and reduces downtime",
            risk_level="Medium",
            tradeoff="Doubles database infrastructure cost due to standby replica",
            cost_impact="+100% database cost",
            confidence="High"
        ))
    
    # Decision 5: NAT Gateway
    nat_gateways = getattr(model, 'nat_gateways', [])
    if nat_gateways:
        nat_count = len(nat_gateways)
        decisions.append(DecisionCard(
            id="nat-gateway",
            title=f"NAT Gateway{'s' if nat_count > 1 else ''} for Outbound Access",
            why="Allows private subnet resources to access internet for updates, patches, and external API calls while remaining private",
            risk_reduced="Maintains security posture while enabling necessary outbound connectivity",
            risk_level="Low",
            tradeoff="Additional monthly cost and potential single point of failure for outbound traffic",
            cost_impact=f"+${nat_count * 32}/month per NAT Gateway",
            confidence="High"
        ))
    
    # Decision 6: VPC Flow Logs
    flow_logs = getattr(model, 'flow_logs', [])
    if flow_logs:
        decisions.append(DecisionCard(
            id="flow-logs",
            title="VPC Flow Logs Enabled",
            why="Captures network traffic metadata for security analysis, troubleshooting, and compliance auditing",
            risk_reduced="Enables detection of anomalous traffic patterns and security incidents",
            risk_level="Low",
            tradeoff="Additional storage costs for log data and requires log analysis tools",
            cost_impact="+$5-10/month (varies by traffic volume)",
            confidence="Medium"
        ))
    
    # Decision 7: RDS Encryption
    encrypted_rds = [rds for rds in model.rds_databases 
                     if getattr(rds, 'storage_encrypted', False)]
    if encrypted_rds:
        decisions.append(DecisionCard(
            id="database-encryption",
            title="Database Encryption at Rest",
            why="Protects sensitive data from unauthorized access to underlying storage volumes",
            risk_reduced="Compliance with data protection regulations (GDPR, HIPAA, PCI-DSS)",
            risk_level="High",
            tradeoff="Minimal performance impact, cannot disable encryption after database creation",
            cost_impact="$0 (included in RDS)",
            confidence="High"
        ))
    
    # Decision 8: VPC Created
    if model.vpcs:
        vpc = model.vpcs[0]
        subnet_count = len(vpc.subnets)
        decisions.append(DecisionCard(
            id="vpc-isolation",
            title="Dedicated VPC for Network Isolation",
            why="Creates isolated network environment with full control over IP addressing, routing, and security",
            risk_reduced="Prevents resource exposure to shared infrastructure",
            risk_level="Medium",
            tradeoff="Requires network configuration and subnet planning",
            cost_impact="$0 (VPC is free)",
            confidence="High"
        ))
    
    # Decision 9: Multiple Subnets
    if model.vpcs and len(model.vpcs[0].subnets) >= 2:
        public_count = len([s for s in model.vpcs[0].subnets if s.subnet_type == SubnetType.PUBLIC])
        private_count = len([s for s in model.vpcs[0].subnets if s.subnet_type == SubnetType.PRIVATE])
        
        if public_count > 0 and private_count > 0:
            decisions.append(DecisionCard(
                id="subnet-segmentation",
                title="Public and Private Subnet Segmentation",
                why="Separates internet-facing resources from internal resources for defense in depth",
                risk_reduced="Limits blast radius of security incidents",
                risk_level="High",
                tradeoff="Increased network complexity and routing configuration",
                cost_impact="$0 (subnets are free)",
                confidence="High"
            ))
    
    return decisions


def estimate_monthly_cost(model: InfrastructureModel) -> Dict:
    """
    Estimate rough monthly costs for infrastructure.
    Prices based on US East (N. Virginia) region as of 2024.
    """
    cost = 0.0
    breakdown = []
    
    # EC2 Instances
    ec2_cost_map = {
        "t2.micro": 8.50,
        "t2.small": 17.00,
        "t2.medium": 34.00,
        "t3.micro": 7.50,
        "t3.small": 15.00,
        "t3.medium": 30.00,
        "t3.large": 60.00,
    }
    
    for ec2 in model.ec2_instances:
        instance_cost = ec2_cost_map.get(ec2.instance_type.value, 20.00)
        cost += instance_cost
        breakdown.append(f"EC2 {ec2.instance_type.value}: ${instance_cost:.2f}")
    
    # RDS Databases
    for rds in model.rds_databases:
        # Base cost estimate for db.t3.micro
        db_cost = 50.00
        
        # Double for Multi-AZ
        if getattr(rds, 'multi_az', False):
            db_cost *= 2
        
        cost += db_cost
        multi_az_label = " (Multi-AZ)" if getattr(rds, 'multi_az', False) else ""
        breakdown.append(f"RDS {rds.engine.value}{multi_az_label}: ${db_cost:.2f}")
    
    # Application Load Balancers
    alb_cost = len(model.load_balancers) * 18.00
    if model.load_balancers:
        cost += alb_cost
        breakdown.append(f"ALB ({len(model.load_balancers)}): ${alb_cost:.2f}")
    
    # NAT Gateways
    nat_gateways = getattr(model, 'nat_gateways', [])
    nat_cost = len(nat_gateways) * 32.00
    if nat_gateways:
        cost += nat_cost
        breakdown.append(f"NAT Gateway ({len(nat_gateways)}): ${nat_cost:.2f}")
    
    # VPC Flow Logs
    flow_logs = getattr(model, 'flow_logs', [])
    if flow_logs:
        flow_cost = 7.00
        cost += flow_cost
        breakdown.append(f"VPC Flow Logs: ${flow_cost:.2f}")
    
    # S3 Buckets (minimal cost estimate)
    if model.s3_buckets:
        s3_cost = 5.00 * len(model.s3_buckets)
        cost += s3_cost
        breakdown.append(f"S3 Storage ({len(model.s3_buckets)} buckets): ${s3_cost:.2f}")
    
    return {
        "total": f"${cost:.2f}/month",
        "breakdown": breakdown
    }


def determine_complexity(model: InfrastructureModel) -> str:
    """Determine architecture complexity level."""
    resource_count = (
        len(model.vpcs) +
        len(model.ec2_instances) +
        len(model.rds_databases) +
        len(model.load_balancers) +
        len(model.s3_buckets) +
        len(getattr(model, 'nat_gateways', []))
    )
    
    if resource_count <= 3:
        return "Simple"
    elif resource_count <= 8:
        return "Moderate"
    else:
        return "Complex"
