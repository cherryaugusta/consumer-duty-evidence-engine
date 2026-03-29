import { api } from "./client";

export type ReviewCase = {
  id: string;
  reference_code: string;
  title: string;
  status: string;
  review_status: string;
  priority: string;
  case_type: string;
  correlation_id: string;
  latest_eval_run_id: string | null;
  eval_case_id: string | null;
  degraded_mode_active: boolean;
  created_at: string;
  updated_at: string;
  summary_snapshot: Record<string, unknown>;
};

export type Claim = {
  id: string;
  case: string;
  claim_type: string;
  claim_text: string;
  normalized_claim_text: string;
  source_section: string;
  extraction_confidence: number;
  schema_valid: boolean;
  extraction_version: string;
  created_at: string;
};

export type EvidenceLink = {
  id: string;
  case: string;
  claim: string;
  outcome: string;
  section: string | null;
  link_type: string;
  rationale: string;
  score: string | number | null;
};

export type SupportAssessment = {
  id: string;
  case: string;
  claim: string;
  outcome: string;
  status: string;
  confidence: number;
  requires_review: boolean;
  assessment_reason: string;
  rules_triggered: unknown[];
  model_version: string;
  created_at: string;
};

export type ContradictionFlag = {
  id: string;
  case: string;
  claim: string | null;
  primary_section: string;
  secondary_section: string;
  contradiction_type: string;
  severity: string;
  reason: string;
  created_at: string;
};

export type AssessmentsResponse = {
  assessments: SupportAssessment[];
  contradictions: ContradictionFlag[];
};

export type Recommendation = {
  id: string;
  case: string;
  recommended_action: string;
  recommended_priority: string;
  executive_summary: string;
  structured_rationale: Record<string, unknown>;
  confidence: number;
  citation_count: number;
  model_version: string;
  prompt_version: string | null;
  prompt_version_name: string | null;
  prompt_version_label: string | null;
  created_at: string;
};

export type AuditEvent = {
  id: string;
  case: string;
  event_type: string;
  actor_type: string;
  actor_id: string | null;
  correlation_id: string;
  payload: Record<string, unknown>;
  created_at: string;
};

export type SourceArtifact = {
  id: string;
  case: string;
  artifact_type: string;
  filename: string;
  mime_type: string;
  source_channel: string;
  storage_path: string;
  sha256_checksum: string;
  parse_status: string;
  parse_error_code: string | null;
  text_length: number;
  uploaded_at: string;
};

export type ArtifactSection = {
  id: string;
  artifact: string;
  section_index: number;
  heading: string | null;
  text: string;
  page_number: number | null;
};

export async function getCases(): Promise<ReviewCase[]> {
  const response = await api.get<ReviewCase[]>("/cases/");
  return response.data;
}

export async function getCase(id: string): Promise<ReviewCase> {
  const response = await api.get<ReviewCase>(`/cases/${id}/`);
  return response.data;
}

export async function getCaseClaims(id: string): Promise<Claim[]> {
  const response = await api.get<Claim[]>(`/cases/${id}/claims/`);
  return response.data;
}

export async function getCaseEvidenceLinks(id: string): Promise<EvidenceLink[]> {
  const response = await api.get<EvidenceLink[]>(`/cases/${id}/evidence-links/`);
  return response.data;
}

export async function getCaseAssessments(id: string): Promise<AssessmentsResponse> {
  const response = await api.get<AssessmentsResponse>(`/cases/${id}/assessments/`);
  return response.data;
}

export async function getCaseRecommendation(id: string): Promise<Recommendation | null> {
  try {
    const response = await api.get<Recommendation>(`/cases/${id}/recommendation/`);
    return response.data;
  } catch (error: unknown) {
    if (typeof error === "object" && error !== null && "response" in error) {
      const response = (error as { response?: { status?: number } }).response;
      if (response?.status === 404) {
        return null;
      }
    }
    throw error;
  }
}

export async function getCaseAuditEvents(id: string): Promise<AuditEvent[]> {
  const response = await api.get<AuditEvent[]>(`/cases/${id}/audit-events/`);
  return response.data;
}

export async function getCaseArtifacts(id: string): Promise<SourceArtifact[]> {
  const response = await api.get<SourceArtifact[]>(`/cases/${id}/artifacts/`);
  return response.data;
}

export async function getArtifactSections(id: string): Promise<ArtifactSection[]> {
  const response = await api.get<ArtifactSection[]>(`/artifacts/${id}/sections/`);
  return response.data;
}