import { useState, useEffect, useCallback } from 'react';
import { Cloud, Zap, Code2, Shield, ChevronDown, ChevronUp, Send, RotateCw, Download, Sparkles, Terminal, Cpu, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { MermaidDiagram } from '@/components/MermaidDiagram';
import { TerraformEditor } from '@/components/TerraformEditor';
import { WarningsPanel } from '@/components/WarningsPanel';
import { DiagramControls } from '@/components/DiagramControls';
import { StatusIndicator } from '@/components/StatusIndicator';
import { NetworkParticles } from '@/components/NetworkParticles';
import { useToast } from '@/hooks/use-toast';
import {
  checkHealth,
  generateFromText,
  editDiagram,
  editTerraform,
  type InfrastructureResponse,
  type Warning,
  type DiagramEditEvent,
} from '@/services/api';

// Demo/fallback data for when backend is not available
const DEMO_DIAGRAM = `graph TB
    subgraph VPC["VPC (10.0.0.0/16)"]
        subgraph PublicSubnet["Public Subnet"]
            ALB[Application Load Balancer]
            NAT[NAT Gateway]
        end
        subgraph PrivateSubnet["Private Subnet"]
            EC2_1[EC2: web-server-1]
            EC2_2[EC2: web-server-2]
        end
        subgraph DatabaseSubnet["Database Subnet"]
            RDS[(RDS PostgreSQL)]
        end
    end
    
    Internet((Internet)) --> ALB
    ALB --> EC2_1
    ALB --> EC2_2
    EC2_1 --> RDS
    EC2_2 --> RDS
    PrivateSubnet --> NAT
    NAT --> Internet`;

const DEMO_TERRAFORM = `# AWS Provider Configuration
provider "aws" {
  region = "us-west-2"
}

# VPC Configuration
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "main-vpc"
  }
}

# Public Subnet
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-west-2a"
  map_public_ip_on_launch = true

  tags = {
    Name = "public-subnet"
  }
}

# Private Subnet
resource "aws_subnet" "private" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-west-2a"

  tags = {
    Name = "private-subnet"
  }
}

# EC2 Instances
resource "aws_instance" "web" {
  count         = 2
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"
  subnet_id     = aws_subnet.private.id

  tags = {
    Name = "web-server-\${count.index + 1}"
  }
}

# RDS Instance
resource "aws_db_instance" "main" {
  identifier        = "main-database"
  engine            = "postgres"
  engine_version    = "14"
  instance_class    = "db.t3.micro"
  allocated_storage = 20
  
  db_subnet_group_name = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.database.id]
  
  skip_final_snapshot = true
}`;

const DEMO_WARNINGS: Warning[] = [
  {
    severity: 'warning',
    message: 'EC2 instances in private subnet have no outbound internet access',
    resource: 'aws_instance.web',
    recommendation: 'Add a NAT Gateway to enable outbound internet access for updates and patches.',
  },
  {
    severity: 'info',
    message: 'Consider enabling Multi-AZ deployment for RDS',
    resource: 'aws_db_instance.main',
    recommendation: 'Multi-AZ provides high availability and automatic failover for production workloads.',
  },
];

export default function Index() {
  // State management
  const [inputText, setInputText] = useState('');
  const [diagram, setDiagram] = useState('');
  const [terraform, setTerraform] = useState('');
  const [originalTerraform, setOriginalTerraform] = useState(''); // Track original for diff
  const [currentModelId, setCurrentModelId] = useState<string | null>(null); // Track model ID for edits
  const [warnings, setWarnings] = useState<Warning[]>([]);
  const [corrections, setCorrections] = useState<string[]>([]); // Architecture auto-corrections
  const [isHealthy, setIsHealthy] = useState(false);
  const [syncStatus, setSyncStatus] = useState<'synced' | 'syncing' | 'error'>('synced');
  const [isLoading, setIsLoading] = useState(false);
  const [warningsExpanded, setWarningsExpanded] = useState(true);
  const { toast } = useToast();

  // Health check on mount and periodically
  useEffect(() => {
    const checkBackendHealth = async () => {
      const status = await checkHealth();
      setIsHealthy(status.status === 'healthy');
    };

    checkBackendHealth();
    const interval = setInterval(checkBackendHealth, 30000);

    return () => clearInterval(interval);
  }, []);

  // Generate infrastructure from text
  const handleGenerate = useCallback(async () => {
    if (!inputText.trim()) {
      toast({
        title: 'Input Required',
        description: 'Please enter an infrastructure description.',
        variant: 'destructive',
      });
      return;
    }

    setIsLoading(true);
    setSyncStatus('syncing');

    try {
      if (isHealthy) {
        console.log('Calling generateFromText API...');
        const response = await generateFromText(inputText);
        console.log('Got response from API:', {
          hasDiagram: !!response.diagram,
          hasTerraform: !!response.terraform,
          hasWarnings: !!response.warnings,
          hasModelId: !!response.modelId
        });
        updateInfrastructure(response);
      } else {
        await new Promise(resolve => setTimeout(resolve, 1500));
        setDiagram(DEMO_DIAGRAM);
        setTerraform(DEMO_TERRAFORM);
        setWarnings(DEMO_WARNINGS);
        toast({
          title: 'Demo Mode',
          description: 'Backend not connected. Showing demo infrastructure.',
        });
      }
      setSyncStatus('synced');
    } catch (error) {
      console.error('Generation error:', error);
      setSyncStatus('error');
      toast({
        title: 'Generation Failed',
        description: error instanceof Error ? error.message : 'Failed to generate infrastructure',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  }, [inputText, isHealthy, toast]);

  // Handle diagram edits
  const handleDiagramEdit = useCallback(async (event: DiagramEditEvent) => {
    console.log('handleDiagramEdit called:', { event, currentModelId, hasModelId: !!currentModelId });

    if (!currentModelId) {
      console.warn('No model ID available for edit');
      toast({
        title: 'Generate First',
        description: 'Please generate infrastructure before editing.',
        variant: 'destructive',
      });
      return;
    }

    setSyncStatus('syncing');

    try {
      if (isHealthy) {
        console.log('Calling editDiagram API with:', { modelId: currentModelId, event });
        const response = await editDiagram(currentModelId, event);
        console.log('Edit response:', response);
        updateInfrastructure(response);
        toast({
          title: 'Edit Applied',
          description: `Successfully ${event.action}ed ${event.resourceType}`,
        });
      } else {
        await new Promise(resolve => setTimeout(resolve, 500));
        toast({
          title: 'Backend Offline',
          description: 'Backend not connected. Cannot apply edits.',
          variant: 'destructive',
        });
      }
      setSyncStatus('synced');
    } catch (error) {
      console.error('Diagram edit error:', error);
      setSyncStatus('error');
      toast({
        title: 'Edit Failed',
        description: error instanceof Error ? error.message : 'Failed to update diagram',
        variant: 'destructive',
      });
    }
  }, [currentModelId, isHealthy, toast]);

  // Handle Terraform code changes
  const handleTerraformChange = useCallback((newCode: string) => {
    setTerraform(newCode);
    if (newCode !== terraform) {
      setSyncStatus('syncing');
    }
  }, [terraform]);

  // Apply Terraform changes
  const handleApplyTerraform = useCallback(async () => {
    console.log('handleApplyTerraform called:', { currentModelId, hasModelId: !!currentModelId, isHealthy });

    if (!currentModelId) {
      console.warn('No model ID available for Terraform edit');
      toast({
        title: 'Generate First',
        description: 'Please generate infrastructure before editing.',
        variant: 'destructive',
      });
      return;
    }

    setSyncStatus('syncing');

    try {
      if (isHealthy) {
        console.log('Calling editTerraform API with:', {
          modelId: currentModelId,
          originalLength: originalTerraform.length,
          modifiedLength: terraform.length
        });
        const response = await editTerraform(currentModelId, originalTerraform, terraform);
        console.log('Terraform edit response:', response);
        // CRITICAL FIX: Skip terraform update to preserve user's exact edits
        updateInfrastructure(response, { skipTerraformUpdate: true });
        toast({
          title: 'Changes Applied',
          description: 'Infrastructure updated from Terraform code.',
        });
      } else {
        toast({
          title: 'Backend Offline',
          description: 'Backend not connected. Cannot apply changes.',
          variant: 'destructive',
        });
      }
      setSyncStatus('synced');
    } catch (error) {
      console.error('Terraform apply error:', error);
      setSyncStatus('error');
      toast({
        title: 'Apply Failed',
        description: error instanceof Error ? error.message : 'Failed to apply Terraform changes',
        variant: 'destructive',
      });
    }
  }, [currentModelId, isHealthy, originalTerraform, terraform, toast]);

  // Update all infrastructure state from response
  const updateInfrastructure = (
    response: InfrastructureResponse,
    options: { skipTerraformUpdate?: boolean } = {}
  ) => {
    console.log('=== updateInfrastructure START ===');
    console.log('Full response:', response);
    console.log('Response keys:', Object.keys(response));
    console.log('response.modelId:', response.modelId);
    console.log('response.diagram length:', response.diagram?.length);
    console.log('response.terraform length:', response.terraform?.length);
    console.log('response.warnings count:', response.warnings?.length);
    console.log('response.corrections count:', response.corrections?.length);
    console.log('skipTerraformUpdate:', options.skipTerraformUpdate);

    setDiagram(response.diagram);

    // CRITICAL FIX: Only update terraform state if not applying terraform changes
    // This preserves user's exact edits in the editor
    if (!options.skipTerraformUpdate) {
      setTerraform(response.terraform);
      setOriginalTerraform(response.terraform);
    } else {
      // When applying terraform changes, only update originalTerraform for future diffs
      // Keep current terraform state to preserve user's edits
      setOriginalTerraform(terraform);
    }

    setWarnings(response.warnings);
    setCorrections(response.corrections || []); // Store architecture corrections

    // Extract model ID
    const extractedModelId = response.modelId;
    console.log('Extracted modelId:', extractedModelId);

    if (extractedModelId) {
      console.log('✅ Setting currentModelId to:', extractedModelId);
      setCurrentModelId(extractedModelId);
    } else {
      console.error('❌ NO MODEL ID FOUND IN RESPONSE!');
      console.log('Response structure:', JSON.stringify(response, null, 2));
    }

    console.log('=== updateInfrastructure END ===');
  };

  const handleDownload = () => {
    const blob = new Blob([terraform], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'main.tf';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast({
      title: 'Downloaded',
      description: 'Terraform file saved as main.tf',
    });
  };

  return (
    <div className="h-screen flex flex-col bg-background bg-animated-gradient noise overflow-hidden">
      {/* Animated network particles */}
      <NetworkParticles />

      {/* Decorative elements */}
      <div className="fixed inset-0 grid-pattern pointer-events-none opacity-30" />
      <div className="fixed top-0 left-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl pointer-events-none" />
      <div className="fixed bottom-0 right-1/4 w-96 h-96 bg-accent/5 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <header className="relative z-10 flex items-center justify-between px-6 py-4 border-b border-border/50 glass-strong">
        <div className="flex items-center gap-4">
          <div className="relative group">
            <div className="absolute inset-0 bg-primary/30 rounded-xl blur-xl group-hover:bg-primary/50 transition-all duration-500" />
            <div className="relative flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-primary/20 to-accent/20 border border-primary/30 group-hover:border-primary/50 transition-all duration-300">
              <Cpu className="w-6 h-6 text-primary animate-pulse-subtle" />
            </div>
          </div>
          <div>
            <h1 className="text-2xl font-display font-bold text-gradient tracking-wider">
              INFRAGEN AI
            </h1>
            <p className="text-xs text-muted-foreground font-medium tracking-wide">
              AI-Powered Infrastructure as Code Generator
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <StatusIndicator type="sync" status={syncStatus} />
          <StatusIndicator type="health" status={isHealthy ? 'healthy' : 'unhealthy'} />
        </div>
      </header>

      {/* Main Content - Three Panels */}
      <main className="relative z-10 flex-1 flex overflow-hidden">
        {/* Left Panel - Text Input */}
        <div className="w-80 border-r border-border/50 flex flex-col glass animate-slide-in-left">{/* CRITICAL: Removed flex-shrink-0 */}
          <div className="flex items-center gap-3 px-4 py-4 border-b border-border/50 bg-panel-header/50">
            <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary/10 border border-primary/20">
              <Sparkles className="w-4 h-4 text-primary" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-foreground">Describe Infrastructure</h2>
              <p className="text-xs text-muted-foreground">Natural language input</p>
            </div>
          </div>

          <div className="flex-1 p-4 flex flex-col gap-4 overflow-auto">
            <div className="relative flex-1">
              <Textarea
                placeholder="Describe your cloud infrastructure...&#10;&#10;Example:&#10;Create a VPC with public and private subnets. Add two EC2 instances behind a load balancer, connected to an RDS PostgreSQL database."
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                className="absolute inset-0 resize-none bg-background/50 border-border/50 focus:border-primary/50 transition-all duration-300 hover:border-primary/30"
              />
            </div>

            <Button
              variant="generate"
              size="lg"
              onClick={handleGenerate}
              disabled={isLoading || !inputText.trim()}
              className="w-full group relative overflow-hidden"
            >
              <span className="absolute inset-0 bg-gradient-to-r from-primary/0 via-primary/30 to-primary/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700" />
              <span className="relative flex items-center gap-2">
                {isLoading ? (
                  <>
                    <RotateCw className="w-5 h-5 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Zap className="w-5 h-5" />
                    Generate Infrastructure
                  </>
                )}
              </span>
            </Button>

            <DiagramControls
              onEdit={handleDiagramEdit}
              disabled={!isHealthy || isLoading}
              currentDiagram={diagram}
            />

            {/* Architecture Corrections Panel */}
            {corrections.length > 0 && (
              <div className="p-3 rounded-lg border border-primary/30 bg-primary/5 animate-fade-in">
                <div className="flex items-start gap-2 mb-2">
                  <div className="flex items-center justify-center w-5 h-5 rounded bg-primary/20 border border-primary/30 flex-shrink-0 mt-0.5">
                    <Check className="w-3 h-3 text-primary" />
                  </div>
                  <div>
                    <h3 className="text-xs font-semibold text-foreground">Architecture Auto-Corrections</h3>
                    <p className="text-xs text-muted-foreground">Best practices enforced</p>
                  </div>
                </div>
                <ul className="space-y-1.5 text-xs text-foreground/80">
                  {corrections.map((correction, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-primary mt-0.5">•</span>
                      <span>{correction}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>

        {/* Center Panel - Diagram */}
        <div className="flex-1 flex flex-col min-w-0 border-r border-border/50 animate-fade-in-up" style={{ animationDelay: '100ms' }}>
          <div className="flex items-center gap-3 px-4 py-4 border-b border-border/50 bg-panel-header/50 glass">
            <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary/10 border border-primary/20">
              <Cloud className="w-4 h-4 text-primary" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-foreground">Infrastructure Diagram</h2>
              <p className="text-xs text-muted-foreground">Visual architecture view</p>
            </div>
          </div>

          <div className="flex-1 overflow-hidden bg-background/30 scanlines">
            <MermaidDiagram code={diagram} className="w-full h-full" />
          </div>
        </div>

        {/* Right Panel - Terraform Code */}
        <div className="w-[480px] flex flex-col glass animate-slide-in-right">{/* CRITICAL: Removed flex-shrink-0 */}
          <div className="flex items-center justify-between px-4 py-4 border-b border-border/50 bg-panel-header/50">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary/10 border border-primary/20">
                <Terminal className="w-4 h-4 text-primary" />
              </div>
              <div>
                <h2 className="text-sm font-semibold text-foreground">Terraform Code</h2>
                <p className="text-xs text-muted-foreground">Infrastructure as Code</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleDownload}
                disabled={!terraform}
                className="border-border/50 hover:border-primary/50 hover:bg-primary/10 transition-all duration-300"
              >
                <Download className="w-4 h-4" />
                Export .tf
              </Button>
              {terraform && (
                <Button
                  variant="apply"
                  size="sm"
                  onClick={handleApplyTerraform}
                  disabled={!isHealthy || isLoading}
                  className="gap-2"
                >
                  <Check className="w-4 h-4" />
                  Apply Changes
                </Button>
              )}
            </div>
          </div>

          <div className="flex-1 overflow-hidden">
            <TerraformEditor
              code={terraform}
              onChange={handleTerraformChange}
              readOnly={isLoading}
            />
          </div>
        </div>
      </main>

      {/* Bottom Panel - Warnings */}
      <div
        className={`relative z-10 border-t border-border/50 glass-strong transition-all duration-500 ease-out ${warningsExpanded ? 'h-44' : 'h-14'
          }`}
      >
        <button
          onClick={() => setWarningsExpanded(!warningsExpanded)}
          className="w-full flex items-center justify-between px-5 py-4 bg-panel-header/30 hover:bg-panel-header/50 transition-all duration-300 group"
        >
          <div className="flex items-center gap-3">
            <div className={`flex items-center justify-center w-8 h-8 rounded-lg border transition-all duration-300 ${warnings.length > 0
              ? 'bg-warning/10 border-warning/30'
              : 'bg-success/10 border-success/30'
              }`}>
              <Shield className={`w-4 h-4 ${warnings.length > 0 ? 'text-warning' : 'text-success'}`} />
            </div>
            <div className="text-left">
              <h2 className="text-sm font-semibold text-foreground flex items-center gap-2">
                Security & Compliance
                {warnings.length > 0 && (
                  <span className="px-2 py-0.5 text-xs font-bold rounded-full bg-warning/20 text-warning border border-warning/30 animate-pulse-subtle">
                    {warnings.length}
                  </span>
                )}
              </h2>
              <p className="text-xs text-muted-foreground">
                {warnings.length > 0 ? 'Review issues below' : 'All checks passed'}
              </p>
            </div>
          </div>
          <div className={`p-2 rounded-lg transition-all duration-300 ${warningsExpanded ? 'bg-muted/50 rotate-180' : 'group-hover:bg-muted/30'
            }`}>
            <ChevronUp className="w-4 h-4 text-muted-foreground" />
          </div>
        </button>

        {warningsExpanded && (
          <div className="h-[calc(100%-56px)] overflow-auto animate-fade-in">
            <WarningsPanel warnings={warnings} />
          </div>
        )}
      </div>
    </div>
  );
}
