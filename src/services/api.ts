// API service for infrastructure generator backend
// All API calls to the backend are centralized here

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface InfrastructureResponse {
  diagram: string;
  terraform: string;
  warnings: Warning[];
  corrections?: string[]; // Architecture auto-corrections
  modelId?: string;
  model?: any; // Infrastructure model JSON
}

export interface Warning {
  severity: 'error' | 'warning' | 'info';
  message: string;
  resource?: string;
  recommendation?: string;
}

export interface DiagramEditEvent {
  action: 'add' | 'remove' | 'move';
  resourceType: string;
  resourceId?: string;
  targetSubnet?: string;
  properties?: Record<string, unknown>;
}

export interface HealthStatus {
  status: 'healthy' | 'unhealthy';
  timestamp?: string;
}

export async function checkHealth(): Promise<HealthStatus> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    if (response.ok) {
      return { status: 'healthy', timestamp: new Date().toISOString() };
    }
    return { status: 'unhealthy' };
  } catch (error) {
    console.error('Health check failed:', error);
    return { status: 'unhealthy' };
  }
}

export async function generateFromText(text: string): Promise<InfrastructureResponse> {
  const response = await fetch(`${API_BASE_URL}/text`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    throw new Error(`Failed to generate infrastructure: ${response.statusText}`);
  }

  const data = await response.json();

  console.log('Backend response received, model_id:', data.model_id);

  const mappedWarnings = (data.security_warnings || []).map((w: any) => ({
    ...w,
    severity: w.severity === 'HIGH' ? 'error' : w.severity === 'MEDIUM' ? 'warning' : 'info'
  }));

  return {
    diagram: data.mermaid_diagram,
    terraform: data.terraform_code,
    warnings: mappedWarnings,
    corrections: data.corrections || [], // Architecture auto-corrections
    modelId: data.model_id,
    model: data.model_summary, // Extract model JSON
  };
}

export async function editDiagram(
  modelId: string,
  event: DiagramEditEvent
): Promise<InfrastructureResponse> {
  const operation = `${event.action}_resource`;

  const backendRequest: any = {
    current_model_id: modelId,
    operation: operation,
    resource_type: event.resourceType,
  };

  if (event.action === 'add') {
    // Use properties from event, or provide sensible defaults
    backendRequest.properties = event.properties || {
      subnet_id: 'subnet-public-1',  // Default for EC2
      subnet_ids: ['subnet-private-1'],  // Default for RDS/LB
    };
  }

  if (event.action === 'remove' || event.action === 'move') {
    if (!event.resourceId) {
      throw new Error('Resource ID is required for remove/move operations');
    }
    backendRequest.resource_id = event.resourceId;
  }

  if (event.action === 'move') {
    if (!event.targetSubnet) {
      throw new Error('Target subnet is required for move operation');
    }
    backendRequest.target_subnet_id = event.targetSubnet;
  }

  const response = await fetch(`${API_BASE_URL}/edit/diagram`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(backendRequest),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to edit diagram: ${response.statusText} - ${errorText}`);
  }

  const data = await response.json();

  // Check if backend operation succeeded
  if (!data.success) {
    throw new Error(data.error || 'Operation failed');
  }

  const mappedWarnings = (data.security_warnings || []).map((w: any) => ({
    ...w,
    severity: w.severity === 'HIGH' ? 'error' : w.severity === 'MEDIUM' ? 'warning' : 'info'
  }));

  return {
    diagram: data.mermaid_diagram || '',
    terraform: data.terraform_code || '',
    warnings: mappedWarnings,
    modelId: data.model_id,
    model: data.model_summary,
  };
}

export async function editTerraform(
  modelId: string,
  originalCode: string,
  modifiedCode: string
): Promise<InfrastructureResponse> {
  const response = await fetch(`${API_BASE_URL}/edit/terraform`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      current_model_id: modelId,
      original_terraform: originalCode,
      modified_terraform: modifiedCode,
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to update Terraform: ${response.statusText} - ${errorText}`);
  }

  const data = await response.json();

  const mappedWarnings = (data.security_warnings || []).map((w: any) => ({
    ...w,
    severity: w.severity === 'HIGH' ? 'error' : w.severity === 'MEDIUM' ? 'warning' : 'info'
  }));

  return {
    diagram: data.mermaid_diagram || '',
    terraform: data.terraform_code || '',
    warnings: mappedWarnings,
    modelId: data.model_id,
    model: data.model_summary,
  };
}

