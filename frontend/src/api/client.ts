// Centralized API client for TenderIQ Frontend
// Handles multi-tenant headers, error handling, and all API endpoints

import type {
  User,
  Organization,
  CompanyProfile,
  CompanyProfileUpdate,
  CompanyDocument,
  Document,
  Tender,
  TenderDocument,
  Proposal,
  ProposalSection,
  ChatSession,
  ChatMessage,
  ChatMessageResponse,
  Citation,
  TenderSummary,
  ComplianceMatrix,
  EligibilityAnalysis,
  ProposalDraft,
  Export,
  AuditLog,
  UserInvitation,
  LoginRequest,
  RegisterOrgRequest,
  AuthResponse,
  PaginatedResponse,
  ChatSessionCreate,
  ChatMessageCreate,
  ChangePasswordRequest,
  UpdateUserRequest,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

class ApiClient {
  private organizationId: string | null = null;
  private userId: string | null = null;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  constructor() {
    // Load from localStorage on initialization
    if (typeof window !== 'undefined') {
      this.organizationId = localStorage.getItem('organization_id');
      this.userId = localStorage.getItem('user_id');
      this.accessToken = localStorage.getItem('access_token');
      this.refreshToken = localStorage.getItem('refresh_token');
    }
  }

  setAuth(organizationId: string, userId: string, accessToken: string, refreshToken: string) {
    this.organizationId = organizationId;
    this.userId = userId;
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;

    if (typeof window !== 'undefined') {
      localStorage.setItem('organization_id', organizationId);
      localStorage.setItem('user_id', userId);
      localStorage.setItem('access_token', accessToken);
      localStorage.setItem('refresh_token', refreshToken);
    }
  }

  clearAuth() {
    this.organizationId = null;
    this.userId = null;
    this.accessToken = null;
    this.refreshToken = null;

    if (typeof window !== 'undefined') {
      localStorage.removeItem('organization_id');
      localStorage.removeItem('user_id');
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  }

  private getHeaders(includeAuth = true, isFormData = false): Record<string, string> {
    const headers: Record<string, string> = {
      'bypass-tunnel-reminder': 'true',
    };

    if (!isFormData) {
      headers['Content-Type'] = 'application/json';
    }

    if (includeAuth && this.organizationId) {
      headers['x-organization-id'] = this.organizationId;
    }
    if (includeAuth && this.userId) {
      headers['x-user-id'] = this.userId;
    }
    if (includeAuth && this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    return headers;
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      let errorDetail = `HTTP ${response.status}`;
      try {
        const errorData = await response.json();
        errorDetail = errorData.detail || errorDetail;
      } catch {
        // Use default error
      }
      throw new Error(errorDetail);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return response.json();
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    includeAuth = true
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        ...this.getHeaders(includeAuth),
        ...options.headers,
      },
    });

    return this.handleResponse<T>(response);
  }

  // ==================== Auth ====================
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const rawResponse = await this.request<any>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    }, false); // Don't include auth headers for login

    const orgId = rawResponse.organization?.organization_id || rawResponse.organization?.id || rawResponse.user?.organization_id || '';
    const userId = rawResponse.user?.user_id || rawResponse.user?.id || '';
    const accessToken = rawResponse.access_token || '';
    const refreshToken = rawResponse.refresh_token || rawResponse.access_token || '';

    // Normalize user object
    const user: User = {
      id: userId,
      email: rawResponse.user?.email || '',
      full_name: rawResponse.user?.full_name || '',
      role: rawResponse.user?.role || 'Admin',
      is_active: rawResponse.user?.is_active ?? true,
      organization_id: orgId,
      created_at: rawResponse.user?.created_at || new Date().toISOString(),
      updated_at: rawResponse.user?.updated_at || new Date().toISOString(),
    };

    // Normalize organization object
    const organization: Organization = {
      id: orgId,
      name: rawResponse.organization?.name || 'TenderIQ Organization',
      slug: rawResponse.organization?.slug || 'tenderiq-org',
      status: (rawResponse.organization?.status as any) || 'Active',
      is_deleted: rawResponse.organization?.is_deleted ?? false,
      created_at: rawResponse.organization?.created_at || new Date().toISOString(),
      updated_at: rawResponse.organization?.updated_at || new Date().toISOString(),
    };

    // Store tokens after successful login
    this.setAuth(
      orgId,
      userId,
      accessToken,
      refreshToken
    );

    return {
      access_token: accessToken,
      refresh_token: refreshToken,
      token_type: rawResponse.token_type || 'bearer',
      user,
      organization,
    };
  }

  async registerOrg(data: any): Promise<AuthResponse> {
    const orgName = data.org_name || data.organization_name || 'My Organization';
    const email = data.email || data.admin_email || '';
    const password = data.password || data.admin_password || '';
    const fullName = data.full_name || data.admin_full_name || email.split('@')[0];

    let rawResponse: any;
    try {
      rawResponse = await this.request<any>('/auth/register', {
        method: 'POST',
        body: JSON.stringify({
          org_name: orgName,
          organization_name: orgName,
          email: email,
          admin_email: email,
          password: password,
          admin_password: password,
          full_name: fullName,
          admin_full_name: fullName,
        }),
      }, false);
    } catch (err: any) {
      // Fallback to bootstrap if register not found
      rawResponse = await this.request<any>('/auth/bootstrap', {
        method: 'POST',
        body: JSON.stringify({
          organization_name: orgName,
          admin_email: email,
          admin_password: password,
          admin_full_name: fullName,
        }),
      }, false);
    }

    const orgId = rawResponse.organization?.organization_id || rawResponse.organization?.id || rawResponse.organization_id || rawResponse.user?.organization_id || '';
    const userId = rawResponse.user?.user_id || rawResponse.user?.id || rawResponse.user_id || '';
    const accessToken = rawResponse.access_token || '';
    const refreshToken = rawResponse.refresh_token || rawResponse.access_token || '';

    const user: User = {
      id: userId,
      email: rawResponse.user?.email || email,
      full_name: rawResponse.user?.full_name || fullName,
      role: rawResponse.user?.role || 'Admin',
      is_active: rawResponse.user?.is_active ?? true,
      organization_id: orgId,
      created_at: rawResponse.user?.created_at || new Date().toISOString(),
      updated_at: rawResponse.user?.updated_at || new Date().toISOString(),
    };

    const organization: Organization = {
      id: orgId,
      name: rawResponse.organization?.name || orgName,
      slug: rawResponse.organization?.slug || orgName.toLowerCase().replace(/[^a-z0-9]/g, '-'),
      status: (rawResponse.organization?.status as any) || 'Active',
      is_deleted: false,
      created_at: rawResponse.organization?.created_at || new Date().toISOString(),
      updated_at: rawResponse.organization?.updated_at || new Date().toISOString(),
    };

    this.setAuth(
      orgId,
      userId,
      accessToken,
      refreshToken
    );

    return {
      access_token: accessToken,
      refresh_token: refreshToken,
      token_type: rawResponse.token_type || 'bearer',
      user,
      organization,
    };
  }

  async loginGoogle(data: { email?: string; full_name?: string; id_token?: string }): Promise<AuthResponse> {
    const rawResponse = await this.request<any>('/auth/google', {
      method: 'POST',
      body: JSON.stringify(data),
    }, false);

    const orgId = rawResponse.organization?.organization_id || rawResponse.organization?.id || rawResponse.user?.organization_id || '';
    const userId = rawResponse.user?.user_id || rawResponse.user?.id || '';
    const accessToken = rawResponse.access_token || '';
    const refreshToken = rawResponse.refresh_token || rawResponse.access_token || '';

    const user: User = {
      id: userId,
      email: rawResponse.user?.email || data.email || '',
      full_name: rawResponse.user?.full_name || data.full_name || '',
      role: rawResponse.user?.role || 'Admin',
      is_active: rawResponse.user?.is_active ?? true,
      organization_id: orgId,
      created_at: rawResponse.user?.created_at || new Date().toISOString(),
      updated_at: rawResponse.user?.updated_at || new Date().toISOString(),
    };

    const organization: Organization = {
      id: orgId,
      name: rawResponse.organization?.name || 'TenderIQ Organization',
      slug: rawResponse.organization?.slug || 'tenderiq-org',
      status: (rawResponse.organization?.status as any) || 'Active',
      is_deleted: false,
      created_at: rawResponse.organization?.created_at || new Date().toISOString(),
      updated_at: rawResponse.organization?.updated_at || new Date().toISOString(),
    };

    this.setAuth(orgId, userId, accessToken, refreshToken);

    return {
      access_token: accessToken,
      refresh_token: refreshToken,
      token_type: rawResponse.token_type || 'bearer',
      user,
      organization,
    };
  }

  async logout(): Promise<void> {
    try {
      await this.request('/auth/logout', { method: 'POST' });
    } finally {
      this.clearAuth();
    }
  }

  async refreshAccessToken(): Promise<string | null> {
    if (!this.refreshToken) return null;

    try {
      const response = await this.request<{ access_token: string }>('/auth/refresh', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.refreshToken}`,
        },
      }, false);

      this.accessToken = response.access_token;
      if (typeof window !== 'undefined') {
        localStorage.setItem('access_token', response.access_token);
      }
      return response.access_token;
    } catch {
      this.clearAuth();
      return null;
    }
  }

  // ==================== Organization ====================
  async getOrganization(): Promise<Organization> {
    try {
      const res = await this.request<any>('/organizations/me');
      return {
        id: res.organization_id || res.id || '',
        name: res.name || 'TenderIQ Organization',
        slug: res.slug || 'tenderiq-org',
        status: res.status || 'Active',
        is_deleted: res.is_deleted ?? false,
        created_at: res.created_at || new Date().toISOString(),
        updated_at: res.updated_at || new Date().toISOString(),
      };
    } catch {
      return {
        id: this.organizationId || '',
        name: 'TenderIQ Organization',
        slug: 'tenderiq-org',
        status: 'Active',
        is_deleted: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
    }
  }

  async updateOrganization(data: Partial<Organization>): Promise<Organization> {
    return this.request<Organization>('/organizations', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  // ==================== Company Profile ====================
  async getCompanyProfile(): Promise<CompanyProfile | null> {
    try {
      return await this.request<CompanyProfile>('/company-profiles');
    } catch (error) {
      if ((error as Error).message.includes('404')) {
        return null;
      }
      throw error;
    }
  }

  async updateCompanyProfile(data: CompanyProfileUpdate): Promise<CompanyProfile> {
    return this.request<CompanyProfile>('/company-profiles', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async uploadCompanyDocument(file: File, documentType: string): Promise<CompanyDocument> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);

    const response = await fetch(`${API_BASE_URL}/company-profiles/documents`, {
      method: 'POST',
      headers: this.getHeaders(true, true) as HeadersInit,
      body: formData,
    });

    return this.handleResponse<CompanyDocument>(response);
  }

  async deleteCompanyDocument(documentId: string): Promise<void> {
    await this.request(`/company-profiles/documents/${documentId}`, {
      method: 'DELETE',
    });
  }

  // ==================== Tenders ====================
  async listTenders(params?: { page?: number; page_size?: number }): Promise<PaginatedResponse<Tender>> {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', params.page.toString());
    if (params?.page_size) searchParams.set('page_size', params.page_size.toString());
    const query = searchParams.toString() ? `?${searchParams.toString()}` : '';
    const res = await this.request<any>(`/tenders${query}`);
    const items = (res.items || []).map((t: any) => ({
      ...t,
      id: t.tender_id || t.id,
    }));
    return {
      ...res,
      items,
    };
  }

  async getTender(tenderId: string): Promise<Tender> {
    const res = await this.request<any>(`/tenders/${tenderId}`);
    return {
      ...res,
      id: res.tender_id || res.id,
    };
  }

  async createTender(data: Partial<Tender>): Promise<Tender> {
    const res = await this.request<any>('/tenders', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return {
      ...res,
      id: res.tender_id || res.id,
    };
  }

  async updateTender(tenderId: string, data: Partial<Tender>): Promise<Tender> {
    return this.request<Tender>(`/tenders/${tenderId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteTender(tenderId: string): Promise<void> {
    await this.request(`/tenders/${tenderId}`, { method: 'DELETE' });
  }

  // ==================== Documents ====================
  async uploadDocument(file: File, tenderId: string, documentType: string): Promise<Document> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('tender_id', tenderId);
    formData.append('document_type', documentType);

    const response = await fetch(`${API_BASE_URL}/documents/upload`, {
      method: 'POST',
      headers: this.getHeaders(true, true) as HeadersInit,
      body: formData,
    });

    return this.handleResponse<Document>(response);
  }

  async getDocument(documentId: string): Promise<Document> {
    return this.request<Document>(`/documents/${documentId}`);
  }

  async deleteDocument(documentId: string): Promise<void> {
    await this.request(`/documents/${documentId}`, { method: 'DELETE' });
  }

  async listTenderDocuments(tenderId: string): Promise<TenderDocument[]> {
    return this.request<TenderDocument[]>(`/tenders/${tenderId}/documents`);
  }

  // ==================== AI Outputs ====================
  async generateSummary(tenderId: string): Promise<TenderSummary> {
    return this.request<TenderSummary>('/ai-outputs/summary/generate', {
      method: 'POST',
      body: JSON.stringify({ tender_id: tenderId }),
    });
  }

  async getSummary(tenderId: string): Promise<TenderSummary | null> {
    try {
      return await this.request<TenderSummary>(`/ai-outputs/summary/${tenderId}`);
    } catch (error) {
      if ((error as Error).message.includes('404')) {
        return null;
      }
      throw error;
    }
  }

  async generateCompliance(tenderId: string): Promise<ComplianceMatrix> {
    return this.request<ComplianceMatrix>('/ai-outputs/compliance/generate', {
      method: 'POST',
      body: JSON.stringify({ tender_id: tenderId }),
    });
  }

  async getCompliance(tenderId: string): Promise<ComplianceMatrix | null> {
    try {
      return await this.request<ComplianceMatrix>(`/ai-outputs/compliance/${tenderId}`);
    } catch (error) {
      if ((error as Error).message.includes('404')) {
        return null;
      }
      throw error;
    }
  }

  async generateEligibility(tenderId: string): Promise<EligibilityAnalysis> {
    return this.request<EligibilityAnalysis>('/ai-outputs/eligibility/generate', {
      method: 'POST',
      body: JSON.stringify({ tender_id: tenderId }),
    });
  }

  async getEligibility(tenderId: string): Promise<EligibilityAnalysis | null> {
    try {
      return await this.request<EligibilityAnalysis>(`/ai-outputs/eligibility/${tenderId}`);
    } catch (error) {
      if ((error as Error).message.includes('404')) {
        return null;
      }
      throw error;
    }
  }

  async generateProposal(tenderId: string): Promise<ProposalDraft> {
    return this.request<ProposalDraft>('/ai-outputs/proposal/generate', {
      method: 'POST',
      body: JSON.stringify({ tender_id: tenderId }),
    });
  }

  // ==================== Proposals ====================
  async listProposals(params?: { tender_id?: string; page?: number; page_size?: number }): Promise<PaginatedResponse<Proposal>> {
    const searchParams = new URLSearchParams();
    if (params?.tender_id) searchParams.set('tender_id', params.tender_id);
    if (params?.page) searchParams.set('page', params.page.toString());
    if (params?.page_size) searchParams.set('page_size', params.page_size.toString());
    const query = searchParams.toString() ? `?${searchParams.toString()}` : '';
    return this.request<PaginatedResponse<Proposal>>(`/proposals${query}`);
  }

  async getProposal(proposalId: string): Promise<Proposal> {
    return this.request<Proposal>(`/proposals/${proposalId}`);
  }

  async createProposal(data: Partial<Proposal>): Promise<Proposal> {
    return this.request<Proposal>('/proposals', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateProposal(proposalId: string, data: Partial<Proposal>): Promise<Proposal> {
    return this.request<Proposal>(`/proposals/${proposalId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteProposal(proposalId: string): Promise<void> {
    await this.request(`/proposals/${proposalId}`, { method: 'DELETE' });
  }

  async getProposalSections(proposalId: string): Promise<ProposalSection[]> {
    return this.request<ProposalSection[]>(`/proposals/${proposalId}/sections`);
  }

  async createProposalSection(proposalId: string, data: Partial<ProposalSection>): Promise<ProposalSection> {
    return this.request<ProposalSection>(`/proposals/${proposalId}/sections`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateProposalSection(sectionId: string, data: Partial<ProposalSection>): Promise<ProposalSection> {
    return this.request<ProposalSection>(`/proposal-sections/${sectionId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteProposalSection(sectionId: string): Promise<void> {
    await this.request(`/proposal-sections/${sectionId}`, { method: 'DELETE' });
  }

  // ==================== Chat ====================
  async createChatSession(data: ChatSessionCreate | string): Promise<ChatSession> {
    const payload = typeof data === 'string'
      ? { title: 'Tender Chat', reference_id: data, context_type: 'Tender' }
      : data;
    const res = await this.request<any>('/chat/sessions', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return {
      id: res.chat_session_id || res.id,
      title: res.title || 'New Chat',
      status: res.status || 'Active',
      organization_id: res.organization_id,
      created_by: res.created_by,
      created_at: res.created_at || new Date().toISOString(),
      updated_at: res.updated_at || new Date().toISOString(),
    };
  }

  async getChatSession(sessionId: string): Promise<ChatSession> {
    const res = await this.request<any>(`/chat/sessions/${sessionId}`);
    return {
      id: res.chat_session_id || res.id,
      title: res.title || 'Chat',
      status: res.status || 'Active',
      organization_id: res.organization_id,
      created_by: res.created_by,
      created_at: res.created_at || new Date().toISOString(),
      updated_at: res.updated_at || new Date().toISOString(),
    };
  }

  async listChatSessions(params?: { tender_id?: string }): Promise<ChatSession[]> {
    const searchParams = new URLSearchParams();
    if (params?.tender_id) searchParams.set('tender_id', params.tender_id);
    const query = searchParams.toString() ? `?${searchParams.toString()}` : '';
    const res = await this.request<any>(`/chat/sessions${query}`);
    const items = Array.isArray(res) ? res : (res.items || []);
    return items.map((item: any) => ({
      id: item.chat_session_id || item.id,
      title: item.title || 'Chat Session',
      status: item.status || 'Active',
      organization_id: item.organization_id,
      created_by: item.created_by,
      created_at: item.created_at || new Date().toISOString(),
      updated_at: item.updated_at || new Date().toISOString(),
    }));
  }

  async getChatHistory(sessionId: string): Promise<ChatMessage[]> {
    return this.getChatMessages(sessionId);
  }

  async sendChatMessage(data: ChatMessageCreate | string, messageContent?: string): Promise<ChatMessageResponse> {
    const sessionId = typeof data === 'string' ? data : (data as any).session_id;
    const content = typeof data === 'string' ? (messageContent || '') : ((data as any).message || (data as any).content || '');
    const contextDocIds = (data as any)?.context_document_ids || [];

    const res = await this.request<any>(`/chat/sessions/${sessionId}/messages`, {
      method: 'POST',
      body: JSON.stringify({
        message: content,
        context_document_ids: contextDocIds,
      }),
    });

    const msg = res.message || res;
    return {
      message: {
        chat_message_id: msg.chat_message_id || msg.id,
        role: msg.role || 'assistant',
        content: msg.content || '',
        tokens_used: msg.tokens_used,
        model_used: msg.model_used,
        session_id: msg.session_id || sessionId,
        created_at: msg.created_at || new Date().toISOString(),
      },
      sources: res.sources || [],
      confidence: res.confidence ?? 1.0,
    };
  }

  // ==================== Exports ====================
  async exportProposal(proposalId: string, format: 'PDF' | 'DOCX' | 'HTML'): Promise<Export> {
    return this.request<Export>('/exports', {
      method: 'POST',
      body: JSON.stringify({ proposal_id: proposalId, export_format: format }),
    });
  }

  async getExport(exportId: string): Promise<Export> {
    return this.request<Export>(`/exports/${exportId}`);
  }

  async listExports(proposalId: string): Promise<Export[]> {
    return this.request<Export[]>(`/exports?proposal_id=${proposalId}`);
  }

  // ==================== Audit ====================
  async listAuditLogs(params?: {
    page?: number;
    page_size?: number;
    action?: string;
    resource_type?: string;
    resource_id?: string;
    user_id?: string;
    date_from?: string;
    date_to?: string;
  }): Promise<PaginatedResponse<AuditLog>> {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', params.page.toString());
    if (params?.page_size) searchParams.set('page_size', params.page_size.toString());
    if (params?.action) searchParams.set('action', params.action);
    if (params?.resource_type) searchParams.set('resource_type', params.resource_type);
    if (params?.resource_id) searchParams.set('resource_id', params.resource_id);
    if (params?.user_id) searchParams.set('user_id', params.user_id);
    if (params?.date_from) searchParams.set('date_from', params.date_from);
    if (params?.date_to) searchParams.set('date_to', params.date_to);
    const query = searchParams.toString() ? `?${searchParams.toString()}` : '';
    return this.request<PaginatedResponse<AuditLog>>(`/audit/logs${query}`);
  }

  async filterAuditLogs(filters: Record<string, unknown>): Promise<PaginatedResponse<AuditLog>> {
    return this.request<PaginatedResponse<AuditLog>>('/audit/logs/filter', {
      method: 'POST',
      body: JSON.stringify(filters),
    });
  }

  async getAuditLog(logId: string): Promise<AuditLog> {
    return this.request<AuditLog>(`/audit/logs/${logId}`);
  }

  // ==================== User Invitations ====================
  async inviteUser(email: string, role: string): Promise<UserInvitation> {
    return this.request<UserInvitation>('/invitations', {
      method: 'POST',
      body: JSON.stringify({ email, role }),
    });
  }

  async listInvitations(): Promise<UserInvitation[]> {
    return this.request<UserInvitation[]>('/invitations');
  }

  async revokeInvitation(invitationId: string): Promise<void> {
    await this.request(`/invitations/${invitationId}`, { method: 'DELETE' });
  }

  // ==================== Health Check ====================
  async healthCheck(): Promise<{ status: string; service: string }> {
    return this.request<{ status: string; service: string }>('/health', {}, false);
  }

  // ==================== User Profile ====================
  async getCurrentUser(): Promise<User> {
    return this.request<User>('/users/me');
  }

  async updateCurrentUser(data: UpdateUserRequest): Promise<User> {
    return this.request<User>('/users/me', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async changePassword(dataOrCurrent: ChangePasswordRequest | string, newPassword?: string): Promise<void> {
    const payload = typeof dataOrCurrent === 'string'
      ? { current_password: dataOrCurrent, new_password: newPassword }
      : dataOrCurrent;
    await this.request('/users/me/password', {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  }

  async deleteAccount(): Promise<void> {
    await this.request('/users/me', { method: 'DELETE' });
    this.clearAuth();
  }

  async uploadAvatar(file: File): Promise<{ url: string }> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/users/me/avatar`, {
      method: 'POST',
      headers: this.getHeaders() as HeadersInit,
      body: formData,
    });

    return this.handleResponse<{ url: string }>(response);
  }

  // ==================== Company Profile Extended ====================
  async uploadCompanyLogo(file: File): Promise<{ url: string }> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/company-profiles/logo`, {
      method: 'POST',
      headers: this.getHeaders() as HeadersInit,
      body: formData,
    });

    return this.handleResponse<{ url: string }>(response);
  }

  // ==================== Chat Extended ====================
  async getChatMessages(sessionId: string): Promise<ChatMessage[]> {
    try {
      const res = await this.request<any>(`/chat/sessions/${sessionId}/messages`);
      const items = Array.isArray(res) ? res : (res.messages || []);
      return items.map((m: any) => ({
        id: m.chat_message_id || m.id,
        role: m.role,
        content: m.content,
        tokens_used: m.tokens_used,
        model_used: m.model_used,
        session_id: m.session_id || sessionId,
        created_at: m.created_at || new Date().toISOString(),
        updated_at: m.updated_at || m.created_at || new Date().toISOString(),
      }));
    } catch {
      const detail = await this.request<any>(`/chat/sessions/${sessionId}/detail`);
      return (detail.messages || []).map((m: any) => ({
        id: m.chat_message_id || m.id,
        role: m.role,
        content: m.content,
        tokens_used: m.tokens_used,
        model_used: m.model_used,
        session_id: m.session_id || sessionId,
        created_at: m.created_at || new Date().toISOString(),
        updated_at: m.updated_at || m.created_at || new Date().toISOString(),
      }));
    }
  }

  async deleteChatSession(sessionId: string): Promise<void> {
    await this.request(`/chat/sessions/${sessionId}`, { method: 'DELETE' });
  }

  async updateChatMessage(messageId: string, content: string): Promise<ChatMessage> {
    return this.request<ChatMessage>(`/chat/messages/${messageId}`, {
      method: 'PUT',
      body: JSON.stringify({ content }),
    });
  }

  // ==================== Audit Extended ====================
  async exportAuditLogs(params?: {
    action?: string;
    resource_type?: string;
    date_from?: string;
    date_to?: string;
  }): Promise<Blob> {
    const searchParams = new URLSearchParams();
    if (params?.action) searchParams.set('action', params.action);
    if (params?.resource_type) searchParams.set('resource_type', params.resource_type);
    if (params?.date_from) searchParams.set('date_from', params.date_from);
    if (params?.date_to) searchParams.set('date_to', params.date_to);
    const query = searchParams.toString() ? `?${searchParams.toString()}` : '';

    const response = await fetch(`${API_BASE_URL}/audit/logs/export${query}`, {
      method: 'GET',
      headers: this.getHeaders() as HeadersInit,
    });

    if (!response.ok) {
      throw new Error(`Failed to export audit logs: ${response.statusText}`);
    }

    return response.blob();
  }

  // ==================== Utility ====================
  isAuthenticated(): boolean {
    return !!this.accessToken && !!this.organizationId;
  }

  getOrganizationId(): string | null {
    return this.organizationId;
  }

  getUserId(): string | null {
    return this.userId;
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
export default apiClient;