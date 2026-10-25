const API_BASE = '/api';

export interface BoundingBox {
  label: string;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  confidence: number;
  masked_text?: string;
}

export interface OCRLine {
  text: string;
  confidence: number;
}

export interface GenerateSampleResponse {
  original_image_base64: string;
  redacted_image_base64: string;
  bounding_boxes: BoundingBox[];
  secrets_detected: number;
  width: number;
  height: number;
  is_safe: boolean;
  ocr_lines: OCRLine[];
}

export interface RedactResponse {
  original_image_base64: string;
  redacted_image_base64: string;
  bounding_boxes: BoundingBox[];
  secrets_detected: number;
  is_safe: boolean;
  ocr_lines: OCRLine[];
  telemetry: {
    execution_time_ms: number;
    pixels_blurred: number;
    secrets_redacted: number;
    redaction_mode: string;
    ocr_lines_processed?: number;
  };
}

export interface HoneyToken {
  id: number;
  token_type: string;
  decoy_key: string;
  decoy_value: string;
  filepath_hint: string;
  status: string;
  created_at: string;
}

export interface DeployHoneyTokensResponse {
  status: string;
  deployed_count: number;
  tokens: HoneyToken[];
}

export interface PlantDecoyResponse {
  status: string;
  file_path: string;
  canary_url: string;
  tokens_written: number;
  timestamp: string;
}

export interface InspectCommandResponse {
  blocked: boolean;
  severity: string;
  trigger_type: string | null;
  action_taken: string;
  matched_tokens: string[];
  matched_patterns: string[];
  explanation: string;
  incident_id: number | null;
  timestamp: string;
}

export interface AirlockFinding {
  rule: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  snippet: string;
  description: string;
  line_number?: number;
}

export interface AirlockScanResponse {
  risk_score: number;
  blocked: boolean;
  findings: AirlockFinding[];
  sanitized_content: string;
  audit_id: number;
  timestamp: string;
}

export interface AgentHookStatusResponse {
  hook_installed: boolean;
  rule_installed: boolean;
  hook_path: string;
  rule_path: string;
}

export interface AgentHookInstallResponse {
  status: string;
  hook_path: string;
  rule_path: string;
  message: string;
}

export interface ResetDbResponse {
  status: string;
  message: string;
  rows_deleted: Record<string, number>;
}

export interface DashboardStats {
  total_screenshots_redacted: number;
  active_honey_tokens: number;
  blocked_scavenge_attempts: number;
  airlock_audits: number;
  recent_events: Array<{
    id: string;
    type: string;
    title: string;
    severity: string;
    blocked: boolean;
    details: string;
    timestamp: string;
  }>;
}

export const api = {
  async getHealth() {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  },

  async getDashboardStats(): Promise<DashboardStats> {
    const res = await fetch(`${API_BASE}/v1/dashboard/stats`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  },

  async generateSample(): Promise<GenerateSampleResponse> {
    const res = await fetch(`${API_BASE}/v1/pixel/generate-sample`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  },

  async redactImage(imageBase64: string, filename = 'uploaded.png'): Promise<RedactResponse> {
    const res = await fetch(`${API_BASE}/v1/pixel/redact`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        image_base64: imageBase64,
        filename,
        auto_detect: true,
      }),
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  },

  async deployHoneyTokens(): Promise<DeployHoneyTokensResponse> {
    const res = await fetch(`${API_BASE}/v1/honeytrap/deploy`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  },

  async getHoneyTokens(): Promise<HoneyToken[]> {
    const res = await fetch(`${API_BASE}/v1/honeytrap/tokens`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  },

  async plantDecoyFile(targetPath?: string): Promise<PlantDecoyResponse> {
    const res = await fetch(`${API_BASE}/v1/honeytrap/plant-file`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_path: targetPath }),
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  },

  async triggerCanary(tokenId = 1): Promise<InspectCommandResponse> {
    const res = await fetch(`${API_BASE}/v1/honeytrap/canary/${tokenId}`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  },

  async inspectCommand(command: string, context?: string): Promise<InspectCommandResponse> {
    const res = await fetch(`${API_BASE}/v1/honeytrap/inspect-command`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command, context }),
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  },

  async scanAirlock(content: string, sourceType = 'SKILL_MD'): Promise<AirlockScanResponse> {
    const res = await fetch(`${API_BASE}/v1/airlock/scan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, source_type: sourceType }),
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  },

  async installAgentHook(): Promise<AgentHookInstallResponse> {
    const res = await fetch(`${API_BASE}/v1/agent-integration/install-hook`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  },

  async getAgentHookStatus(): Promise<AgentHookStatusResponse> {
    const res = await fetch(`${API_BASE}/v1/agent-integration/status`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  },

  async resetDatabase(): Promise<ResetDbResponse> {
    const res = await fetch(`${API_BASE}/v1/admin/reset-db`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  },
};
