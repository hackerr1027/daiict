import { useState, useEffect } from 'react';
import { Plus, Trash2, MoveHorizontal, Info } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { Input } from '@/components/ui/input';
import { type DiagramEditEvent } from '@/services/api';

interface DiagramControlsProps {
  onEdit: (event: DiagramEditEvent) => void;
  disabled?: boolean;
  currentDiagram?: string; // NEW: Pass diagram to extract resource IDs
}

const resourceTypes = [
  { value: 'ec2', label: 'EC2 Instance', icon: '🖥️' },
  { value: 'rds', label: 'RDS Database', icon: '🗄️' },
  { value: 'load_balancer', label: 'Load Balancer', icon: '⚖️' },
  { value: 's3', label: 'S3 Bucket', icon: '🪣' },
  { value: 'security_group', label: 'Security Group', icon: '🛡️' },
];

const subnetOptions = [
  { value: 'subnet-public-1', label: 'Public Subnet', color: 'bg-success/20 text-success' },
  { value: 'subnet-private-1', label: 'Private Subnet', color: 'bg-warning/20 text-warning' },
  { value: 'subnet-private-2', label: 'Private Subnet 2', color: 'bg-warning/20 text-warning' },
];

// Extract resource IDs from Mermaid diagram
function extractResourceIds(diagram: string): { id: string; type: string; label: string }[] {
  if (!diagram) return [];

  const resources: { id: string; type: string; label: string }[] = [];
  const lines = diagram.split('\n');

  for (const line of lines) {
    // Match patterns like: ec2-web-1["🖥️ web-server-1<br/>ID: ec2-web-1<br/>t2.micro"]
    const match = line.match(/(\w+-[\w-]+)\["([^"]+)"/);
    if (match) {
      const id = match[1];
      const label = match[2].replace(/<br\/>/g, ' ').replace(/ID:\s*/g, '');

      let type = 'unknown';
      if (id.startsWith('ec2-')) type = 'EC2';
      else if (id.startsWith('rds-')) type = 'RDS';
      else if (id.startsWith('lb-')) type = 'Load Balancer';
      else if (id.startsWith('s3-')) type = 'S3';
      else if (id.startsWith('sg-')) type = 'Security Group';

      resources.push({ id, type, label });
    }
  }

  return resources;
}

export function DiagramControls({ onEdit, disabled = false, currentDiagram }: DiagramControlsProps) {
  const [selectedResource, setSelectedResource] = useState('ec2');
  const [resourceId, setResourceId] = useState('');
  const [targetSubnet, setTargetSubnet] = useState('subnet-public-1');
  const [activeAction, setActiveAction] = useState<'add' | 'remove' | 'move' | null>(null);

  // Extract available resources from diagram
  const availableResources = extractResourceIds(currentDiagram || '');
  const movableResources = availableResources.filter(r => r.type === 'EC2' || r.type === 'RDS');

  // CRITICAL FIX: Reset resourceId if it no longer exists in the updated diagram
  // This prevents operations on deleted resources
  useEffect(() => {
    if (resourceId && !availableResources.find(r => r.id === resourceId)) {
      setResourceId(''); // Clear stale resource ID
      setActiveAction(null); // Reset active action
    }
  }, [currentDiagram, resourceId, availableResources]);

  // Helper function to get default properties for each resource type
  const getDefaultProperties = (resourceType: string): Record<string, any> => {
    switch (resourceType) {
      case 'ec2':
        return {
          subnet_id: 'subnet-public-1',
          instance_type: 't2.micro'
        };
      case 'rds':
        return {
          subnet_ids: ['subnet-private-1', 'subnet-private-2'],
          engine: 'postgres',
          instance_class: 'db.t3.micro'
        };
      case 'elb':
      case 'load_balancer':
        return {
          subnet_ids: ['subnet-public-1'],
          target_instance_ids: []
        };
      case 's3':
        return {};
      case 'security_group':
        return {
          vpc_id: 'vpc-main'
        };
      default:
        return {};
    }
  };

  const handleAction = (action: 'add' | 'remove' | 'move') => {
    if (activeAction === action) {
      // CRITICAL FIX: Validate resource exists before operating on it
      if ((action === 'remove' || action === 'move') && resourceId) {
        const resourceExists = availableResources.find(r => r.id === resourceId);
        if (!resourceExists) {
          console.error(`Resource ${resourceId} not found in current diagram`);
          setResourceId('');
          setActiveAction(null);
          return; // Abort operation
        }
      }

      const event: DiagramEditEvent = {
        action,
        resourceType: selectedResource,
        resourceId: resourceId || undefined,
        targetSubnet: action === 'move' ? targetSubnet : undefined,
        properties: action === 'add' ? getDefaultProperties(selectedResource) : undefined,
      };
      onEdit(event);
      setResourceId('');
      setActiveAction(null);
    } else {
      setActiveAction(action);
    }
  };

  return (
    <div className="space-y-4 p-4 rounded-lg border border-border/50 bg-panel-bg/50 glass">
      <div className="flex items-center gap-2 pb-2 border-b border-border/30">
        <div className="flex items-center justify-center w-7 h-7 rounded-md bg-primary/10 border border-primary/20">
          <MoveHorizontal className="w-4 h-4 text-primary" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-foreground">Diagram Controls</h3>
          <p className="text-xs text-muted-foreground">Add, remove, or move resources</p>
        </div>
      </div>

      {/* Resource Type Selection for Add */}
      {activeAction === 'add' && (
        <div className="space-y-2 animate-fade-in">
          <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Resource Type</label>
          <Select value={selectedResource} onValueChange={setSelectedResource} disabled={disabled}>
            <SelectTrigger className="w-full bg-background/50 border-border/50 hover:border-primary/30 transition-all duration-300">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="glass-strong border-primary/20">
              {resourceTypes.map(type => (
                <SelectItem key={type.value} value={type.value} className="focus:bg-primary/10">
                  <span className="flex items-center gap-2">
                    <span>{type.icon}</span>
                    <span>{type.label}</span>
                  </span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

      {/* Resource ID Input for Remove */}
      {activeAction === 'remove' && (
        <div className="space-y-2 animate-fade-in">
          <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-1">
            Resource ID
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger>
                  <Info className="w-3 h-3" />
                </TooltipTrigger>
                <TooltipContent className="glass-strong border-primary/20 max-w-xs">
                  <p className="text-xs">Copy the ID from the diagram (e.g., ec2-web-1, rds-main)</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </label>
          {availableResources.length > 0 ? (
            <Select value={resourceId} onValueChange={setResourceId} disabled={disabled}>
              <SelectTrigger className="w-full bg-background/50 border-border/50 hover:border-primary/30 transition-all duration-300">
                <SelectValue placeholder="Select resource to remove" />
              </SelectTrigger>
              <SelectContent className="glass-strong border-primary/20">
                {availableResources.map(resource => (
                  <SelectItem key={resource.id} value={resource.id} className="focus:bg-primary/10">
                    <span className="flex items-center gap-2 text-xs">
                      <span className="px-1.5 py-0.5 rounded bg-destructive/20 text-destructive font-mono">{resource.id}</span>
                      <span className="text-muted-foreground">{resource.type}</span>
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : (
            <Input
              placeholder="e.g., ec2-web-1"
              value={resourceId}
              onChange={(e: any) => setResourceId(e.target.value)}
              disabled={disabled}
              className="bg-background/50 border-border/50 focus:border-primary/50 transition-all duration-300 font-mono text-sm"
            />
          )}
        </div>
      )}

      {/* Resource ID Selection for Move */}
      {activeAction === 'move' && (
        <>
          <div className="space-y-2 animate-fade-in">
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-1">
              Resource to Move
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger>
                    <Info className="w-3 h-3" />
                  </TooltipTrigger>
                  <TooltipContent className="glass-strong border-primary/20 max-w-xs">
                    <p className="text-xs">Only EC2 and RDS resources can be moved between subnets</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </label>
            {movableResources.length > 0 ? (
              <Select value={resourceId} onValueChange={setResourceId} disabled={disabled}>
                <SelectTrigger className="w-full bg-background/50 border-border/50 hover:border-primary/30 transition-all duration-300">
                  <SelectValue placeholder="Select resource to move" />
                </SelectTrigger>
                <SelectContent className="glass-strong border-primary/20">
                  {movableResources.map(resource => (
                    <SelectItem key={resource.id} value={resource.id} className="focus:bg-primary/10">
                      <span className="flex items-center gap-2 text-xs">
                        <span className="px-1.5 py-0.5 rounded bg-primary/20 text-primary font-mono">{resource.id}</span>
                        <span className="text-muted-foreground">{resource.type}</span>
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <Input
                placeholder="e.g., ec2-web-1"
                value={resourceId}
                onChange={(e: any) => setResourceId(e.target.value)}
                disabled={disabled}
                className="bg-background/50 border-border/50 focus:border-primary/50 transition-all duration-300 font-mono text-sm"
              />
            )}
          </div>

          <div className="space-y-2 animate-fade-in">
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Target Subnet</label>
            <Select value={targetSubnet} onValueChange={setTargetSubnet} disabled={disabled}>
              <SelectTrigger className="w-full bg-background/50 border-border/50 hover:border-primary/30 transition-all duration-300">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="glass-strong border-primary/20">
                {subnetOptions.map(subnet => (
                  <SelectItem key={subnet.value} value={subnet.value} className="focus:bg-primary/10">
                    <span className={`px-2 py-0.5 rounded-md text-xs font-medium ${subnet.color}`}>
                      {subnet.label}
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </>
      )}

      {/* Action Buttons */}
      <div className="grid grid-cols-3 gap-2 pt-2">
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant={activeAction === 'add' ? 'default' : 'outline'}
                size="sm"
                onClick={() => handleAction('add')}
                disabled={disabled}
                className="w-full transition-all duration-300 hover:scale-105"
              >
                <Plus className="w-4 h-4 mr-1" />
                {activeAction === 'add' ? 'Confirm' : 'Add'}
              </Button>
            </TooltipTrigger>
            <TooltipContent className="glass-strong border-primary/20">
              <p className="text-xs">Add a new resource to the infrastructure</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>

        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant={activeAction === 'remove' ? 'destructive' : 'outline'}
                size="sm"
                onClick={() => handleAction('remove')}
                disabled={disabled}
                className="w-full transition-all duration-300 hover:scale-105"
              >
                <Trash2 className="w-4 h-4 mr-1" />
                {activeAction === 'remove' ? 'Confirm' : 'Remove'}
              </Button>
            </TooltipTrigger>
            <TooltipContent className="glass-strong border-primary/20">
              <p className="text-xs">Remove an existing resource</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>

        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant={activeAction === 'move' ? 'default' : 'outline'}
                size="sm"
                onClick={() => handleAction('move')}
                disabled={disabled}
                className="w-full transition-all duration-300 hover:scale-105"
              >
                <MoveHorizontal className="w-4 h-4 mr-1" />
                {activeAction === 'move' ? 'Confirm' : 'Move'}
              </Button>
            </TooltipTrigger>
            <TooltipContent className="glass-strong border-primary/20">
              <p className="text-xs">Move a resource between subnets</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      {/* Helper text */}
      {movableResources.length === 0 && activeAction === 'move' && (
        <p className="text-xs text-warning bg-warning/10 border border-warning/20 rounded px-2 py-1.5 animate-fade-in">
          ⚠️ Generate infrastructure first to see movable resources
        </p>
      )}
    </div>
  );
}
