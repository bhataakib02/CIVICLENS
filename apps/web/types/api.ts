export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type?: string;
  expires_in?: number;
}

export interface CitizenProfile {
  id: string;
  email?: string | null;
  phone_number?: string | null;
  education_level?: string | null;
  date_of_birth?: string | null;
  gender?: string | null;
  category?: string | null;
  occupation?: string | null;
  declared_annual_income?: number | null;
  disability_status?: boolean | null;
  family_size?: number | null;
  profile_completeness: number;
  current_version_no: number;
}

export interface CitizenProfileUpdate {
  date_of_birth?: string | null;
  gender?: string | null;
  category?: string | null;
  occupation?: string | null;
  declared_annual_income?: number | null;
  disability_status?: boolean | null;
  family_size?: number | null;
}

export interface Address {
  id: string;
  type: 'permanent' | 'current';
  state: string;
  district: string;
  pincode: string;
  line1: string;
  line2?: string | null;
  is_primary?: boolean;
}

export interface AddressInput {
  type: 'permanent' | 'current';
  state: string;
  district: string;
  pincode: string;
  line1: string;
  line2?: string | null;
  is_primary?: boolean;
}

export interface SchemeSummary {
  id: string;
  canonical_name: string;
  category: string;
  scope: 'central' | 'state';
  benefits_summary: string;
}

export interface DocumentRequirement {
  document_type: string;
  is_mandatory: boolean;
  notes?: string | null;
}

export interface SchemeDetail extends SchemeSummary {
  administering_dept?: string;
  document_requirements?: DocumentRequirement[];
  last_verified_at?: string;
  scheme_version_id?: string;
  official_source_url?: string;
  description?: string;
}

export interface SchemePage {
  items: SchemeSummary[];
  page: number;
  page_size: number;
  total: number;
}

export interface RuleOutcome {
  rule_id?: string;
  field_key: string;
  outcome: 'pass' | 'fail' | 'unknown';
  explanation: string;
  source_citation?: {
    knowledge_source_id?: string;
    section?: string;
  };
}

export type EligibilityResultStatus = 'eligible' | 'not_eligible' | 'likely_eligible' | 'insufficient_data';

export interface EligibilityResult {
  scheme_id: string;
  scheme_version_id?: string;
  result: EligibilityResultStatus;
  computed_at: string;
  rule_breakdown?: RuleOutcome[];
  scheme_name?: string;
}

export interface AssistantCitation {
  knowledge_source_id?: string;
  title?: string;
  section?: string;
}

export interface AssistantResponse {
  conversation_id: string;
  answer: string;
  citations?: AssistantCitation[];
  eligibility_tool_calls?: EligibilityResult[];
}

export interface UploadInitResponse {
  upload_url: string;
  document_id: string;
  expires_at: string;
}

export type DocumentStatus =
  | 'uploaded'
  | 'processing'
  | 'verified'
  | 'rejected'
  | 'verification_required'
  | 'validation_failed'
  | 'processing_failed';

export interface Document {
  id: string;
  document_type: string;
  status: DocumentStatus;
  uploaded_at: string;
  filename?: string;
}

export interface DocumentDetail extends Document {
  extracted_fields?: Record<string, any>;
  confidence?: number;
  verified_by_citizen?: boolean;
}

export type ApplicationStatus =
  | 'draft'
  | 'ready_for_submission'
  | 'submission_pending'
  | 'submission_failed'
  | 'submitted'
  | 'under_review'
  | 'action_required'
  | 'info_requested'
  | 'approved'
  | 'rejected'
  | 'withdrawn'
  | 'completed';

export interface Application {
  id: string;
  scheme_id: string;
  scheme_name?: string;
  status: ApplicationStatus;
  created_at: string;
  submitted_at?: string | null;
}

export interface ApplicationStatusHistory {
  from_status?: string | null;
  to_status: string;
  note?: string | null;
  created_at: string;
}

export interface ApplicationDetail extends Application {
  status_history?: ApplicationStatusHistory[];
  attached_documents?: Document[];
  scheme_specific_answers?: Record<string, any>;
}

export interface ApplicationPage {
  items: Application[];
  page: number;
  page_size: number;
  total: number;
}

export interface ApplicationChecklistItem {
  document_type: string;
  is_mandatory: boolean;
  is_satisfied: boolean;
  document_id?: string;
}

export interface ApplicationChecklist {
  items: ApplicationChecklistItem[];
  all_required_satisfied: boolean;
}

export interface Notification {
  id: string;
  channel: 'sms' | 'email' | 'in_app';
  category: 'scheme_match' | 'status_change' | 'doc_reverification' | 'deadline_reminder';
  status: 'queued' | 'sent' | 'failed';
  sent_at?: string | null;
  title?: string;
  message?: string;
  is_read?: boolean;
  application_id?: string;
}

export interface ApiErrorDetail {
  code: string;
  message: string;
  request_id: string;
  field_errors?: Array<{ field: string; message: string }>;
}

export interface ApiErrorResponse {
  error: ApiErrorDetail;
}
