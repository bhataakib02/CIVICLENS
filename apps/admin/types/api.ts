/* ─── Auth ───────────────────────────────────────────────────────────────────── */
export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type?: string;
  expires_in?: number;
}

export interface AccountInfo {
  id: string;
  email: string | null;
  phone_number: string | null;
  role: UserRole;
  status: 'active' | 'suspended';
}

/* ─── Roles ──────────────────────────────────────────────────────────────────── */
export type UserRole = 'citizen' | 'agent' | 'scheme_admin' | 'admin';

/* ─── Dashboard ──────────────────────────────────────────────────────────────── */
export interface DashboardMetrics {
  applications_pending_review: number;
  applications_action_required: number;
  documents_verification_required: number;
  scheme_drafts_awaiting_review: number;
  knowledge_sources_pending: number;
  notifications_failed: number;
  total_citizens: number;
  total_applications: number;
}

/* ─── Audit ──────────────────────────────────────────────────────────────────── */
export interface AuditLogEntry {
  id: string;
  actor_user_id: string | null;
  action: string;
  entity_type: string;
  entity_id: string | null;
  diff: Record<string, any> | null;
  created_at: string;
}

export interface AuditLogPage {
  items: AuditLogEntry[];
  total: number;
  page: number;
  page_size: number;
}

/* ─── Citizens ───────────────────────────────────────────────────────────────── */
export interface CitizenSummary {
  user_id: string;
  email: string | null;
  phone_number_masked: string | null;
  role: string;
  status: string;
  created_at: string;
  profile_completeness: number;
}

export interface CitizenSummaryPage {
  items: CitizenSummary[];
  total: number;
  page: number;
  page_size: number;
}

export interface CitizenDetail {
  user_id: string;
  email: string | null;
  phone_number_masked: string | null;
  role: string;
  status: string;
  created_at: string;
  profile: Record<string, any> | null;
  addresses: Record<string, any>[];
  applications_count: number;
  documents_count: number;
  active_consents_count: number;
}

export interface ConsentRecord {
  id: string;
  citizen_id: string;
  consent_type: string;
  purpose: string;
  scope: Record<string, any> | null;
  version: string;
  agent_id: string | null;
  granted_at: string;
  revoked_at: string | null;
}

/* ─── Applications ───────────────────────────────────────────────────────────── */
export type ApplicationStatus =
  | 'draft' | 'ready_for_submission' | 'submission_pending' | 'submission_failed'
  | 'submitted' | 'under_review' | 'action_required' | 'info_requested'
  | 'approved' | 'rejected' | 'withdrawn' | 'completed';

export interface ApplicationSummary {
  id: string;
  application_number: string;
  scheme_id: string;
  scheme_version_id: string;
  status: ApplicationStatus;
  created_at: string;
  submitted_at: string | null;
}

export interface ApplicationPage {
  items: ApplicationSummary[];
  page: number;
  page_size: number;
  total: number;
}

export interface StatusHistoryItem {
  from_status: string | null;
  to_status: string;
  note: string | null;
  created_at: string;
}

export interface EligibilitySummary {
  decision: string | null;
  engine_version: string | null;
  scheme_version_id: string | null;
  evaluated_at: string | null;
}

export interface ChecklistItem {
  document_type: string;
  required: boolean;
  status: string;
  document_id: string | null;
}

export interface ReviewInfo {
  assigned_case_worker_id: string | null;
  open_actions: Array<{ reason: string; required_items: string[] | null }>;
}

export interface SubmissionInfo {
  status: string;
  submission_method: string;
  external_reference: string | null;
  submitted_at: string | null;
  provider_environment: string | null;
}

export interface ApplicationDetail extends ApplicationSummary {
  eligibility: EligibilitySummary;
  checklist: { items: ChecklistItem[]; all_required_satisfied: boolean };
  status_history: StatusHistoryItem[];
  attached_document_ids: string[];
  submission: SubmissionInfo | null;
  next_actions: string[];
  review: ReviewInfo | null;
}

/* ─── Documents ──────────────────────────────────────────────────────────────── */
export type DocumentStatus =
  | 'uploading' | 'uploaded' | 'validating' | 'processing' | 'extracted'
  | 'verification_required' | 'verified' | 'validation_failed' | 'processing_failed' | 'rejected';

export interface DocumentSummary {
  id: string;
  document_type: string;
  status: DocumentStatus;
  filename: string;
  mime_type: string;
  size_bytes: number;
  uploaded_at: string;
  created_at: string;
}

export interface ExtractedField {
  field_name: string;
  value_type: string;
  raw_value: string | null;
  normalized_value: string | null;
  verified_value: string | null;
  confidence: number;
  confidence_level: string;
  page_number: number | null;
  text_span: string | null;
  bounding_box: any | null;
  source: string;
  verification_status: string;
}

export interface DocumentDetail extends DocumentSummary {
  extracted_fields: Record<string, any>;
  fields: ExtractedField[];
  confidence: number | null;
  verified_by_citizen: boolean;
  classified_type: string | null;
  identity_match: any | null;
  conflicts: any[];
  processing_status: string | null;
}

/* ─── Schemes ────────────────────────────────────────────────────────────────── */
export type SchemeVersionStatus = 'draft' | 'in_review' | 'published' | 'superseded' | 'archived';

export interface SchemeSummary {
  id: string;
  canonical_name: string;
  category: string;
  scope: 'central' | 'state';
  benefits_summary: string | null;
}

export interface SchemePage {
  items: SchemeSummary[];
  page: number;
  page_size: number;
  total: number;
}

export interface SchemeDetail extends SchemeSummary {
  administering_dept: string | null;
  document_requirements: any[];
  last_verified_at: string | null;
  scheme_version_id: string | null;
}

export interface SchemeVersion {
  id: string;
  scheme_id: string;
  version_no: number;
  status: SchemeVersionStatus;
  benefits_summary: string;
  effective_from: string;
  effective_to: string | null;
  published_at: string | null;
}

export interface EligibilityRule {
  id: string;
  rule_code: string;
  field_key: string;
  operator: string;
  value: string;
  mandatory: boolean;
  group_id: string | null;
  group_operator: string | null;
  explanation_text: string | null;
  source_citation: string | null;
}

export interface RuleValidationResult {
  valid: boolean;
  normalized_rule_count: number;
  message: string;
}

export interface SimulationResult {
  scheme_version_id: string;
  total_profiles_evaluated: number;
  newly_eligible: number;
  newly_ineligible: number;
  unchanged: number;
  insufficient_data: number;
  summary: Record<string, number>;
}

/* ─── Knowledge ──────────────────────────────────────────────────────────────── */
export interface KnowledgeSource {
  id: string;
  title: string;
  url: string;
  publisher: string | null;
  source_type: string | null;
  trust_level: string;
  verification_status: string;
  scheme_id: string | null;
  created_at: string;
}

export interface IngestionJob {
  id: string;
  status: string;
  url: string;
  knowledge_source_id: string | null;
  attempts: number;
  max_attempts: number;
  error: string | null;
  result: any;
  created_at: string;
}

/* ─── Notifications ──────────────────────────────────────────────────────────── */
export interface NotificationOps {
  id: string;
  user_id: string | null;
  channel: string;
  category: string;
  priority: string;
  status: string;
  title: string | null;
  entity_type: string | null;
  entity_id: string | null;
  created_at: string | null;
  sent_at: string | null;
  failure_code: string | null;
  attempts: number;
}

export interface NotificationOpsPage {
  items: NotificationOps[];
  total: number;
  page: number;
  page_size: number;
}

/* ─── Users ──────────────────────────────────────────────────────────────────── */
export interface UserInfo {
  id: string;
  email: string | null;
  phone_number_masked: string | null;
  role: UserRole;
  status: 'active' | 'suspended';
  last_login_at: string | null;
  created_at: string;
}

export interface UserPage {
  items: UserInfo[];
  total: number;
  page: number;
  page_size: number;
}

/* ─── System ─────────────────────────────────────────────────────────────────── */
export interface SystemHealth {
  database: string;
  redis: string;
  overall: string;
}

/* ─── Agent ──────────────────────────────────────────────────────────────────── */
export interface AssistedCitizen {
  citizen_id: string;
  user_id: string | null;
  consent_status: string;
  consent_id: string;
  phone_number_masked: string | null;
  email: string | null;
  profile_completeness: number;
}

/* ─── API errors ─────────────────────────────────────────────────────────────── */
export interface ApiErrorDetail {
  code: string;
  message: string;
  request_id: string;
  field_errors?: Array<{ field: string; message: string }>;
}

export interface ApiErrorResponse {
  error: ApiErrorDetail;
}
