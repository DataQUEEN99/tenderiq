'use client';

import { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  FileText,
  Download,
  Edit,
  Trash2,
  Plus,
  Sparkles,
  CheckCircle,
  AlertTriangle,
  Clock,
  FileCheck,
  BarChart2,
  MessageSquare,
  MoreVertical,
  Eye,
  ExternalLink,
  Loader2,
} from 'lucide-react';
import { apiClient } from '../api/client';
import type { Tender, TenderDocument, TenderSummary, ComplianceMatrix, EligibilityAnalysis, ProposalDraft } from '../types';
import { format } from 'date-fns';
import {
  Button,
} from '../components/ui/button';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from '../components/ui/card';
import {
  Badge,
} from '../components/ui/badge';
import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from '../components/ui/tabs';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from '../components/ui/alert';
import {
  Skeleton,
} from '../components/ui/skeleton';
import { Separator } from '../components/ui/separator';
import { ScrollArea } from '../components/ui/scroll-area';
import { cn } from '../utils/cn';

const statusConfig: Record<string, { label: string; variant: 'default' | 'success' | 'warning' | 'destructive' }> = {
  Draft: { label: 'Draft', variant: 'default' },
  Published: { label: 'Published', variant: 'success' },
  'In Progress': { label: 'In Progress', variant: 'success' },
  Submitted: { label: 'Submitted', variant: 'warning' },
  Awarded: { label: 'Awarded', variant: 'success' },
  Lost: { label: 'Lost', variant: 'destructive' },
  Archived: { label: 'Archived', variant: 'default' },
};

export function TenderDetailPage() {
  const { tenderId } = useParams<{ tenderId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('overview');

  const { data: tender, isLoading: tenderLoading, error: tenderError } = useQuery({
    queryKey: ['tender', tenderId],
    queryFn: () => apiClient.getTender(tenderId!),
    enabled: !!tenderId,
  });

  const { data: documents, isLoading: docsLoading } = useQuery({
    queryKey: ['tender-documents', tenderId],
    queryFn: () => apiClient.listTenderDocuments(tenderId!),
    enabled: !!tenderId,
  });

  const { data: summary } = useQuery({
    queryKey: ['tender-summary', tenderId],
    queryFn: () => apiClient.getSummary(tenderId!),
    enabled: !!tenderId,
  });

  const { data: compliance } = useQuery({
    queryKey: ['tender-compliance', tenderId],
    queryFn: () => apiClient.getCompliance(tenderId!),
    enabled: !!tenderId,
  });

  const { data: eligibility } = useQuery({
    queryKey: ['tender-eligibility', tenderId],
    queryFn: () => apiClient.getEligibility(tenderId!),
    enabled: !!tenderId,
  });

  const generateSummaryMutation = useMutation({
    mutationFn: () => apiClient.generateSummary(tenderId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tender-summary', tenderId] });
    },
  });

  const generateComplianceMutation = useMutation({
    mutationFn: () => apiClient.generateCompliance(tenderId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tender-compliance', tenderId] });
    },
  });

  const generateEligibilityMutation = useMutation({
    mutationFn: () => apiClient.generateEligibility(tenderId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tender-eligibility', tenderId] });
    },
  });

  const generateProposalMutation = useMutation({
    mutationFn: () => apiClient.generateProposal(tenderId!),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['proposals'] });
      navigate(`/proposals/${data.id}`);
    },
  });

  const uploadDocumentMutation = useMutation({
    mutationFn: ({ file, documentType }: { file: File; documentType: string }) =>
      apiClient.uploadDocument(file, tenderId!, documentType),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tender-documents', tenderId] });
    },
  });

  const deleteDocumentMutation = useMutation({
    mutationFn: (docId: string) => apiClient.deleteDocument(docId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tender-documents', tenderId] });
    },
  });

  if (tenderLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-10 w-32" />
        </div>
        <div className="grid gap-4 md:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i}><CardContent className="py-6"><Skeleton className="h-8 w-24" /><Skeleton className="h-4 w-1/2" /></CardContent></Card>
          ))}
        </div>
        <Card><CardContent className="py-8"><Skeleton className="h-64 w-full" /></CardContent></Card>
      </div>
    );
  }

  if (tenderError || !tender) {
    return (
      <Alert variant="destructive" className="mb-6">
        <AlertTitle>Tender not found</AlertTitle>
        <AlertDescription>The tender you're looking for doesn't exist or you don't have access to it.</AlertDescription>
      </Alert>
    );
  }

  const statusInfo = statusConfig[tender.status] || { label: tender.status, variant: 'default' };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-3xl font-bold tracking-tight">{tender.title}</h1>
              <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>
            </div>
            <p className="text-muted-foreground">{tender.reference_number}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline">
                <MoreVertical className="mr-2 h-4 w-4" />
                Actions
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem asChild>
                <Link to={`/tenders/${tender.id}/edit`}>
                  <Edit className="mr-2 h-4 w-4" />
                  Edit Tender
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link to={`/chat?context=${tender.id}`}>
                  <MessageSquare className="mr-2 h-4 w-4" />
                  Chat about this Tender
                </Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="text-destructive">
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Meta Info */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid gap-4 md:grid-cols-4">
            <div className="flex items-center gap-3 p-4 bg-muted/50 rounded-lg">
              <FileText className="h-6 w-6 text-primary" />
              <div>
                <p className="text-sm text-muted-foreground">Issuing Authority</p>
                <p className="font-medium">{tender.issuing_authority || '—'}</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-4 bg-muted/50 rounded-lg">
              <Clock className="h-6 w-6 text-primary" />
              <div>
                <p className="text-sm text-muted-foreground">Submission Deadline</p>
                <p className="font-medium">
                  {tender.submission_deadline
                    ? format(new Date(tender.submission_deadline), 'MMM d, yyyy HH:mm')
                    : '—'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-4 bg-muted/50 rounded-lg">
              <FileCheck className="h-6 w-6 text-primary" />
              <div>
                <p className="text-sm text-muted-foreground">Estimated Value</p>
                <p className="font-medium">{tender.estimated_value || '—'}</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-4 bg-muted/50 rounded-lg">
              <BarChart2 className="h-6 w-6 text-primary" />
              <div>
                <p className="text-sm text-muted-foreground">Contract Duration</p>
                <p className="font-medium">{tender.contract_duration || '—'}</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="documents">Documents</TabsTrigger>
          <TabsTrigger value="summary">AI Summary</TabsTrigger>
          <TabsTrigger value="compliance">Compliance Matrix</TabsTrigger>
          <TabsTrigger value="eligibility">Eligibility</TabsTrigger>
          <TabsTrigger value="proposal">Generate Proposal</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview">
          <Card>
            <CardHeader>
              <CardTitle>Tender Description</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="prose max-w-none">
                {tender.description ? (
                  <p className="whitespace-pre-wrap">{tender.description}</p>
                ) : (
                  <p className="text-muted-foreground">No description provided.</p>
                )}
              </div>
            </CardContent>
          </Card>

          {tender.submission_deadline && (
            <Alert>
              <AlertTitle>Submission Deadline</AlertTitle>
              <AlertDescription>
                This tender must be submitted by <strong>{format(new Date(tender.submission_deadline), 'MMMM d, yyyy HH:mm')}</strong>.
                {new Date(tender.submission_deadline) < new Date() && ' This deadline has passed.'}
              </AlertDescription>
            </Alert>
          )}
        </TabsContent>

        {/* Documents Tab */}
        <TabsContent value="documents">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Tender Documents</CardTitle>
                <CardDescription>Upload and manage RFP documents</CardDescription>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => document.getElementById('doc-upload')?.click()}
              >
                <Plus className="mr-2 h-4 w-4" />
                Upload Document
              </Button>
            </CardHeader>
            <CardContent>
              <input
                id="doc-upload"
                type="file"
                accept=".pdf,.docx,.txt"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) uploadDocumentMutation.mutate({ file, documentType: 'TENDER' });
                }}
              />
              {docsLoading ? (
                <div className="space-y-3">
                  {[...Array(3)].map((_, i) => (
                    <div key={i} className="flex items-center gap-4 p-3">
                      <Skeleton className="h-10 w-10 rounded" />
                      <div className="flex-1">
                        <Skeleton className="h-4 w-3/4 mb-2" />
                        <Skeleton className="h-3 w-1/2" />
                      </div>
                    </div>
                  ))}
                </div>
              ) : documents?.length === 0 ? (
                <div className="text-center py-8">
                  <FileText className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
                  <h3 className="text-lg font-medium mb-2">No documents uploaded</h3>
                  <p className="text-muted-foreground mb-4">Upload RFP documents to enable AI analysis</p>
                  <Button
                    variant="outline"
                    onClick={() => document.getElementById('doc-upload')?.click()}
                  >
                    <Plus className="mr-2 h-4 w-4" />
                    Upload Document
                  </Button>
                </div>
              ) : (
                <div className="space-y-3">
                  {documents?.map((td: TenderDocument & { document?: TenderDocument['document'] }) => (
                    <div
                      key={td.id}
                      className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <FileText className="h-8 w-8 text-primary" />
                        <div>
                          <p className="font-medium">{td.document?.original_filename || 'Document'}</p>
                          <p className="text-sm text-muted-foreground">
                            {td.document ? `${formatFileSize(td.document.file_size)} • ${format(new Date(td.document.created_at), 'MMM d, yyyy')}` : ''}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button variant="ghost" size="icon" asChild>
                          <a href={`${apiClient['API_BASE_URL']?.replace('/api/v1', '') || 'http://localhost:8000'}/api/v1/documents/${td.document_id}`} target="_blank" download>
                            <Download className="h-4 w-4" />
                          </a>
                        </Button>
                        <Button variant="ghost" size="icon" onClick={() => deleteDocumentMutation.mutate(td.document_id)}>
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Summary Tab */}
        <TabsContent value="summary">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Executive Summary</CardTitle>
                <CardDescription>AI-generated summary of the tender</CardDescription>
              </div>
              {!summary && (
                <Button onClick={() => generateSummaryMutation.mutate()} loading={generateSummaryMutation.isPending}>
                  <Sparkles className="mr-2 h-4 w-4" />
                  Generate Summary
                </Button>
              )}
              {summary && (
                <Button variant="outline" onClick={() => queryClient.invalidateQueries({ queryKey: ['tender-summary', tenderId] })}>
                  <Loader2 className="mr-2 h-4 w-4" />
                  Regenerate
                </Button>
              )}
            </CardHeader>
            <CardContent>
              {generateSummaryMutation.isPending ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                </div>
              ) : summary ? (
                <div className="prose max-w-none whitespace-pre-wrap">{summary.content}</div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <Sparkles className="mx-auto h-12 w-12 mb-4 opacity-50" />
                  <p>No summary generated yet. Click "Generate Summary" to create one.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Compliance Tab */}
        <TabsContent value="compliance">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Compliance Matrix</CardTitle>
                <CardDescription>AI-generated compliance analysis</CardDescription>
              </div>
              {!compliance && (
                <Button onClick={() => generateComplianceMutation.mutate()} loading={generateComplianceMutation.isPending} disabled={!documents?.length}>
                  <Sparkles className="mr-2 h-4 w-4" />
                  Generate Matrix
                </Button>
              )}
              {compliance && (
                <Button variant="outline" onClick={() => queryClient.invalidateQueries({ queryKey: ['tender-compliance', tenderId] })} disabled={!documents?.length}>
                  <Loader2 className="mr-2 h-4 w-4" />
                  Regenerate
                </Button>
              )}
            </CardHeader>
            <CardContent>
              {generateComplianceMutation.isPending ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                </div>
              ) : compliance ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium">Overall Compliance: <span className="text-primary">{compliance.matrix.filter(m => m.status === 'COMPLIANT').length}/{compliance.matrix.length}</span></h4>
                    <Badge variant="success">{Math.round((compliance.matrix.filter(m => m.status === 'COMPLIANT').length / compliance.matrix.length) * 100)}%</Badge>
                  </div>
                  <ScrollArea className="max-h-[600px]">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b text-left text-muted-foreground">
                          <th className="pb-2 pr-4">Requirement</th>
                          <th className="pb-2 pr-4">Category</th>
                          <th className="pb-2 pr-4">Status</th>
                          <th className="pb-2">Gap</th>
                        </tr>
                      </thead>
                      <tbody>
                        {compliance.matrix.map((item, i) => (
                          <tr key={i} className="border-b last:border-0">
                            <td className="py-2 pr-4 max-w-[300px] truncate">{item.requirement_text}</td>
                            <td className="py-2 pr-4">{item.category}</td>
                            <td className="py-2 pr-4">
                              <Badge variant={getComplianceStatusVariant(item.status)}>{item.status}</Badge>
                            </td>
                            <td className="py-2 text-muted-foreground max-w-[200px] truncate">{item.gap || '—'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </ScrollArea>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <AlertTriangle className="mx-auto h-12 w-12 mb-4 opacity-50" />
                  <p>No compliance matrix generated. Upload documents first, then click "Generate Matrix".</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Eligibility Tab */}
        <TabsContent value="eligibility">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Eligibility Assessment</CardTitle>
                <CardDescription>AI-powered GO/NO-GO analysis</CardDescription>
              </div>
              {!eligibility && (
                <Button onClick={() => generateEligibilityMutation.mutate()} loading={generateEligibilityMutation.isPending} disabled={!documents?.length}>
                  <Sparkles className="mr-2 h-4 w-4" />
                  Assess Eligibility
                </Button>
              )}
              {eligibility && (
                <Button variant="outline" onClick={() => queryClient.invalidateQueries({ queryKey: ['tender-eligibility', tenderId] })} disabled={!documents?.length}>
                  <Loader2 className="mr-2 h-4 w-4" />
                  Re-assess
                </Button>
              )}
            </CardHeader>
            <CardContent>
              {generateEligibilityMutation.isPending ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                </div>
              ) : eligibility ? (
                <div className="space-y-6">
                  <div className="flex items-center justify-between p-4 rounded-lg bg-muted/50">
                    <div>
                      <p className="text-sm text-muted-foreground">Recommendation</p>
                      <p className="text-2xl font-bold">{eligibility.decision}</p>
                    </div>
                    <Badge variant={eligibility.decision === 'GO' ? 'success' : 'destructive'} className="text-lg px-4 py-2">
                      {eligibility.decision}
                    </Badge>
                  </div>

                  <div className="grid gap-4 md:grid-cols-3">
                    <Card>
                      <CardContent className="pt-6">
                        <p className="text-sm text-muted-foreground">Confidence</p>
                        <p className="text-3xl font-bold">{Math.round(eligibility.confidence * 100)}%</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="pt-6">
                        <p className="text-sm text-muted-foreground">Missing Requirements</p>
                        <p className="text-3xl font-bold">{eligibility.missing_requirements.length}</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="pt-6">
                        <p className="text-sm text-muted-foreground">Criteria Analyzed</p>
                        <p className="text-3xl font-bold">{eligibility.criteria_analysis.length}</p>
                      </CardContent>
                    </Card>
                  </div>

                  <div>
                    <h4 className="font-medium mb-3">Criteria Analysis</h4>
                    <div className="space-y-3">
                      {eligibility.criteria_analysis.map((c, i) => (
                        <div key={i} className="p-3 rounded-lg border">
                          <div className="flex items-center justify-between">
                            <p className="font-medium">{c.criterion}</p>
                            <Badge variant={c.met ? 'success' : 'destructive'}>{c.met ? 'Met' : 'Not Met'}</Badge>
                          </div>
                          <p className="text-sm text-muted-foreground mt-1">{c.evidence}</p>
                          {c.gap && <p className="text-sm text-destructive mt-1">Gap: {c.gap}</p>}
                        </div>
                      ))}
                    </div>
                  </div>

                  {eligibility.recommendations.length > 0 && (
                    <div>
                      <h4 className="font-medium mb-3">Recommendations</h4>
                      <ul className="space-y-2">
                        {eligibility.recommendations.map((r, i) => (
                          <li key={i} className="flex items-center gap-2 text-sm">
                            <CheckCircle className="h-4 w-4 text-green-500" />
                            {r}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div>
                    <h4 className="font-medium mb-3">Overall Assessment</h4>
                    <p className="text-muted-foreground">{eligibility.reasoning}</p>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <AlertTriangle className="mx-auto h-12 w-12 mb-4 opacity-50" />
                  <p>No eligibility assessment yet. Upload documents and click "Assess Eligibility".</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Proposal Tab */}
        <TabsContent value="proposal">
          <Card>
            <CardHeader>
              <CardTitle>Generate Proposal Draft</CardTitle>
              <CardDescription>AI-powered proposal generation based on tender requirements and your company profile</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Alert>
                  <AlertTitle>Prerequisites</AlertTitle>
                  <AlertDescription>
                    For best results, ensure you have:
                    <ul className="list-disc list-inside mt-2 space-y-1">
                      <li>Uploaded tender documents</li>
                      <li>Completed company profile</li>
                      <li>Generated compliance matrix (recommended)</li>
                    </ul>
                  </AlertDescription>
                </Alert>

                <Button
                  size="lg"
                  className="w-full"
                  onClick={() => generateProposalMutation.mutate()}
                  loading={generateProposalMutation.isPending}
                  disabled={!documents?.length}
                >
                  <Sparkles className="mr-2 h-4 w-4" />
                  {generateProposalMutation.isPending ? 'Generating Proposal...' : 'Generate Proposal Draft'}
                </Button>

                {generateProposalMutation.isError && (
                  <Alert variant="destructive">
                    <AlertDescription>Failed to generate proposal: {generateProposalMutation.error?.message}</AlertDescription>
                  </Alert>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getComplianceStatusVariant(status: string): 'default' | 'success' | 'warning' | 'destructive' {
  switch (status) {
    case 'COMPLIANT':
      return 'success';
    case 'PARTIAL':
      return 'warning';
    case 'NON-COMPLIANT':
      return 'destructive';
    default:
      return 'default';
  }
}