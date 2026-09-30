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

  private getHeaders(includeAuth = true): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

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
    const response = await this.request<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    }, false); // Don't include auth headers for login

    // Store tokens after successful login
    this.setAuth(
      response.organization.id,
      response.user.id,
      response.access_token,
      response.refresh_token
    );

    return response;
  }

  async registerOrg(data: RegisterOrgRequest): Promise<AuthResponse> {
    const response = await this.request<AuthResponse>('/auth/register-org', {
      method: 'POST',
      body: JSON.stringify(data),
    }, false);

    this.setAuth(
      response.organization.id,
      response.user.id,
      response.access_token,
      response.refresh_token
    );

    return response;
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
    return this.request<Organization>('/organizations');
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
      headers: this.getHeaders() as HeadersInit,
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
    return this.request<PaginatedResponse<Tender>>(`/tenders${query}`);
  }

  async getTender(tenderId: string): Promise<Tender> {
    return this.request<Tender>(`/tenders/${tenderId}`);
  }

  async createTender(data: Partial<Tender>): Promise<Tender> {
    return this.request<Tender>('/tenders', {
      method: 'POST',
      body: JSON.stringify(data),
    });
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
      headers: this.getHeaders() as HeadersInit,
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
    const payload = typeof data === 'string' ? { tender_id: data } : data;
    return this.request<ChatSession>('/chat/sessions', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getChatSession(sessionId: string): Promise<ChatSession> {
    return this.request<ChatSession>(`/chat/sessions/${sessionId}`);
  }

  async listChatSessions(params?: { tender_id?: string }): Promise<ChatSession[]> {
    const searchParams = new URLSearchParams();
    if (params?.tender_id) searchParams.set('tender_id', params.tender_id);
    const query = searchParams.toString() ? `?${searchParams.toString()}` : '';
    return this.request<ChatSession[]>(`/chat/sessions${query}`);
  }

  async getChatHistory(sessionId: string): Promise<ChatMessage[]> {
    return this.request<ChatMessage[]>(`/chat/sessions/${sessionId}/history`);
  }

  async sendChatMessage(data: ChatMessageCreate | string, messageContent?: string): Promise<ChatMessageResponse> {
    const payload = typeof data === 'string'
      ? { session_id: data, message: messageContent, content: messageContent }
      : data;
    return this.request<ChatMessageResponse>('/chat/messages', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
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
    return this.request<ChatMessage[]>(`/chat/sessions/${sessionId}/messages`);
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