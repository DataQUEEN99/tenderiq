// Type definitions for TenderIQ Frontend

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'Admin' | 'Manager' | 'Member' | 'Viewer';
  is_active: boolean;
  organization_id: string;
  created_at: string;
  updated_at: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  status: 'Active' | 'Suspended' | 'Disabled';
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
}

export interface CompanyProfile {
  id: string;
  company_name: string;
  industry?: string;
  employee_count?: string;
  annual_revenue?: string;
  website?: string;
  address?: string;
  phone?: string;
  email?: string;
  certifications: string[];
  capabilities: string[];
  past_experience?: string;
  key_personnel?: string;
  financial_info?: string;
  organization_id: string;
  created_at: string;
  updated_at: string;
}

export interface Document {
  id: string;
  filename: string;
  original_filename: string;
  file_hash: string;
  file_size: number;
  mime_type: string;
  extension: string;
  document_type: 'Tender' | 'Proposal' | 'Company' | 'Reference' | 'Other';
  status: 'Uploading' | 'Processing' | 'Processed' | 'Failed' | 'Deleted';
  error_message?: string;
  organization_id: string;
  uploaded_by: string;
  chunk_count: number;
  vector_collection?: string;
  created_at: string;
  updated_at: string;
}

export interface Tender {
  id: string;
  title: string;
  reference_number: string;
  description?: string;
  issuing_authority?: string;
  submission_deadline?: string;
  estimated_value?: string;
  currency: string;
  contract_duration?: string;
  status: 'Draft' | 'Published' | 'In Progress' | 'Submitted' | 'Awarded' | 'Lost' | 'Archived';
  organization_id: string;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface TenderDocument {
  id: string;
  tender_id: string;
  document_id: string;
  document?: Document;
  created_at: string;
  updated_at: string;
}

export interface Proposal {
  id: string;
  title: string;
  version: number;
  status: 'Draft' | 'In Review' | 'Finalized' | 'Submitted' | 'Won' | 'Lost' | 'Archived';
  executive_summary?: string;
  compliance_score?: number;
  submitted_at?: string;
  tender_id: string;
  organization_id: string;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface ProposalSection {
  id: string;
  title: string;
  content?: string;
  order: number;
  section_type?: string;
  is_generated: boolean;
  generation_prompt?: string;
  proposal_id: string;
  created_at: string;
  updated_at: string;
}

export interface ChatSession {
  id: string;
  title?: string;
  status: 'Active' | 'Archived';
  organization_id: string;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  tokens_used?: number;
  model_used?: string;
  session_id: string;
  created_at: string;
  updated_at: string;
}

export interface ChatContext {
  id: string;
  context_type: string;
  reference_id?: string;
  content: string;
  metadata?: string;
  session_id: string;
  created_at: string;
  updated_at: string;
}

export interface Export {
  id: string;
  export_format: 'PDF' | 'DOCX' | 'HTML';
  status: 'Pending' | 'Processing' | 'Completed' | 'Failed';
  file_path?: string;
  error_message?: string;
  proposal_id: string;
  organization_id: string;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface UserInvitation {
  id: string;
  email: string;
  role: 'Admin' | 'Manager' | 'Member' | 'Viewer';
  token: string;
  expires_at: string;
  accepted_at?: string;
  organization_id: string;
  invited_by: string;
  created_at: string;
  updated_at: string;
}

export interface AuditLog {
  id: string;
  action: 'CREATE' | 'READ' | 'UPDATE' | 'DELETE' | 'LOGIN' | 'LOGOUT' | 'EXPORT' | 'IMPORT' | 'AI_PROCESS' | 'STATUS_CHANGE';
  resource_type: string;
  resource_id?: string;
  details?: Record<string, unknown>;
  ip_address?: string;
  user_agent?: string;
  is_deleted: boolean;
  organization_id: string;
  user_id?: string;
  created_at: string;
  updated_at: string;
}

// API Response types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface ApiError {
  detail: string;
  status_code: number;
}

// Auth types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterOrgRequest {
  org_name: string;
  email: string;
  password: string;
  full_name: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
  organization: Organization;
}

// AI Output types
export interface TenderSummary {
  id: string;
  tender_id: string;
  version: number;
  content: string;
  generated_at: string;
}

export interface ComplianceMatrix {
  id: string;
  tender_id: string;
  version: number;
  matrix: ComplianceItem[];
  generated_at: string;
}

export interface ComplianceItem {
  requirement_id: string;
  requirement_text: string;
  category: string;
  proposal_section?: string;
  status: 'COMPLIANT' | 'PARTIAL' | 'NON-COMPLIANT' | 'NOT ADDRESSED';
  evidence?: string;
  gap?: string;
  notes?: string;
}

export interface EligibilityAnalysis {
  id: string;
  tender_id: string;
  version: number;
  decision: 'GO' | 'NO-GO';
  confidence: number;
  criteria_analysis: EligibilityCriterion[];
  missing_requirements: string[];
  recommendations: string[];
  reasoning: string;
  generated_at: string;
}

export interface EligibilityCriterion {
  criterion: string;
  met: boolean;
  evidence: string;
  gap?: string;
}

export interface ProposalDraft {
  id: string;
  tender_id: string;
  version: number;
  content: string;
  generated_at: string;
}

// Chat types
export interface ChatSessionCreate {
  tender_id?: string;
}

export interface ChatMessageCreate {
  session_id: string;
  message_text: string;
}

export interface ChatMessageResponse {
  message: ChatMessage;
  citations?: Citation[];
}

export interface Citation {
  document_id: string;
  document_name: string;
  chunk_text: string;
  score: number;
}

// Company Profile types
export interface CompanyProfileUpdate {
  company_name?: string;
  industry?: string;
  employee_count?: string;
  annual_revenue?: string;
  website?: string;
  address?: string;
  phone?: string;
  email?: string;
  certifications?: string[];
  capabilities?: string[];
  past_experience?: string;
  key_personnel?: string;
  financial_info?: string;
}

export interface CompanyDocument {
  id: string;
  document_type: string;
  document: Document;
  created_at: string;
}

// User Profile types
export interface UpdateUserRequest {
  full_name?: string;
  phone?: string;
  timezone?: string;
  language?: string;
  avatar_url?: string | null;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}