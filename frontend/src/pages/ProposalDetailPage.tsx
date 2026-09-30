'use client';

import { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  Edit,
  Trash2,
  Plus,
  Download,
  FileText,
  Sparkles,
  Loader2,
  Save,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  MoreVertical,
  ArrowUpRight,
  Type,
  Layout,
  FileCheck,
  Clock,
} from 'lucide-react';
import { apiClient } from '../api/client';
import type { Proposal, ProposalSection, Export } from '../types';
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
  Textarea,
} from '../components/ui/textarea';
import {
  Input,
} from '../components/ui/input';
import {
  Skeleton,
} from '../components/ui/skeleton';
import { Separator } from '../components/ui/separator';
import { ScrollArea } from '../components/ui/scroll-area';
import { cn } from '../utils/cn';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';

const statusConfig: Record<string, { label: string; variant: 'default' | 'success' | 'warning' | 'destructive' }> = {
  Draft: { label: 'Draft', variant: 'default' },
  'In Review': { label: 'In Review', variant: 'warning' },
  Finalized: { label: 'Finalized', variant: 'success' },
  Submitted: { label: 'Submitted', variant: 'success' },
  Won: { label: 'Won', variant: 'success' },
  Lost: { label: 'Lost', variant: 'destructive' },
  Archived: { label: 'Archived', variant: 'default' },
};

export function ProposalDetailPage() {
  const { proposalId } = useParams<{ proposalId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('editor');
  const [editingSectionId, setEditingSectionId] = useState<string | null>(null);
  const [sectionContent, setSectionContent] = useState('');

  const { data: proposal, isLoading: proposalLoading, error: proposalError } = useQuery({
    queryKey: ['proposal', proposalId],
    queryFn: () => apiClient.getProposal(proposalId!),
    enabled: !!proposalId,
  });

  const { data: sections, isLoading: sectionsLoading } = useQuery({
    queryKey: ['proposal-sections', proposalId],
    queryFn: () => apiClient.getProposalSections(proposalId!),
    enabled: !!proposalId,
  });

  const { data: exports } = useQuery({
    queryKey: ['proposal-exports', proposalId],
    queryFn: () => apiClient.listExports(proposalId!),
    enabled: !!proposalId,
  });

  const updateProposalMutation = useMutation({
    mutationFn: (data: Partial<Proposal>) => apiClient.updateProposal(proposalId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proposal', proposalId] });
    },
  });

  const updateSectionMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<ProposalSection> }) =>
      apiClient.updateProposalSection(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proposal-sections', proposalId] });
      setEditingSectionId(null);
    },
  });

  const createSectionMutation = useMutation({
    mutationFn: (data: Partial<ProposalSection>) => apiClient.createProposalSection(proposalId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proposal-sections', proposalId] });
    },
  });

  const deleteSectionMutation = useMutation({
    mutationFn: (sectionId: string) => apiClient.deleteProposalSection(sectionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proposal-sections', proposalId] });
    },
  });

  const exportMutation = useMutation({
    mutationFn: (format: 'PDF' | 'DOCX' | 'HTML') => apiClient.exportProposal(proposalId!, format),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proposal-exports', proposalId] });
    },
  });

  if (proposalLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-10 w-32" />
        </div>
        <Card><CardContent className="py-8"><Skeleton className="h-64 w-full" /></CardContent></Card>
      </div>
    );
  }

  if (proposalError || !proposal) {
    return (
      <Alert variant="destructive" className="mb-6">
        <AlertTitle>Proposal not found</AlertTitle>
        <AlertDescription>The proposal you're looking for doesn't exist or you don't have access to it.</AlertDescription>
      </Alert>
    );
  }

  const statusInfo = statusConfig[proposal.status] || { label: proposal.status, variant: 'default' };

  const handleAddSection = () => {
    const newSection = {
      title: 'New Section',
      content: '',
      order: (sections?.length || 0) + 1,
      section_type: 'custom',
    };
    createSectionMutation.mutate(newSection);
  };

  const handleSectionSave = (sectionId: string) => {
    updateSectionMutation.mutate({ id: sectionId, data: { content: sectionContent } });
  };

  const startEditing = (section: ProposalSection) => {
    setEditingSectionId(section.id);
    setSectionContent(section.content || '');
  };

  const handleReorder = (sectionId: string, direction: 'up' | 'down') => {
    const currentIndex = sections?.findIndex(s => s.id === sectionId) ?? -1;
    if (currentIndex === -1) return;

    const newIndex = direction === 'up' ? currentIndex - 1 : currentIndex + 1;
    if (newIndex < 0 || newIndex >= (sections?.length ?? 0)) return;

    const section = sections![currentIndex];
    const targetSection = sections![newIndex];

    updateSectionMutation.mutate({ id: sectionId, data: { order: newIndex + 1 } });
    updateSectionMutation.mutate({ id: targetSection.id, data: { order: currentIndex + 1 } });
  };

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
              <h1 className="text-3xl font-bold tracking-tight">{proposal.title}</h1>
              <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>
            </div>
            <p className="text-muted-foreground">Version {proposal.version} • {proposal.tender?.title || 'Unknown Tender'}</p>
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
              <DropdownMenuItem
                onClick={() => updateProposalMutation.mutate({ status: 'Finalized' })}
                disabled={proposal.status === 'Finalized'}
              >
                <Check className="mr-2 h-4 w-4" />
                Mark as Finalized
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link to={`/proposals/${proposal.id}/edit`}>
                  <Edit className="mr-2 h-4 w-4" />
                  Edit Proposal
                </Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="text-destructive">
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
          <Button variant="outline" asChild>
            <Link to={`/exports/new?proposal=${proposal.id}`}>
              <Download className="mr-2 h-4 w-4" />
              Export
            </Link>
          </Button>
        </div>
      </div>

      {/* Meta Info */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid gap-4 md:grid-cols-4">
            <div className="flex items-center gap-3 p-4 bg-muted/50 rounded-lg">
              <FileText className="h-6 w-6 text-primary" />
              <div>
                <p className="text-sm text-muted-foreground">Status</p>
                <p className="font-medium">{statusInfo.label}</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-4 bg-muted/50 rounded-lg">
              <FileCheck className="h-6 w-6 text-primary" />
              <div>
                <p className="text-sm text-muted-foreground">Compliance Score</p>
                <p className="font-medium">{proposal.compliance_score !== undefined ? `${proposal.compliance_score}%` : '—'}</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-4 bg-muted/50 rounded-lg">
              <Clock className="h-6 w-6 text-primary" />
              <div>
                <p className="text-sm text-muted-foreground">Created</p>
                <p className="font-medium">{format(new Date(proposal.created_at), 'MMM d, yyyy')}</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-4 bg-muted/50 rounded-lg">
              <Layout className="h-6 w-6 text-primary" />
              <div>
                <p className="text-sm text-muted-foreground">Sections</p>
                <p className="font-medium">{sections?.length || 0}</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="editor">Editor</TabsTrigger>
          <TabsTrigger value="preview">Preview</TabsTrigger>
          <TabsTrigger value="exports">Exports</TabsTrigger>
        </TabsList>

        {/* Editor Tab */}
        <TabsContent value="editor">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Proposal Sections</CardTitle>
                <CardDescription>Edit and reorder proposal sections</CardDescription>
              </div>
              <Button onClick={handleAddSection} size="sm">
                <Plus className="mr-2 h-4 w-4" />
                Add Section
              </Button>
            </CardHeader>
            <CardContent>
              {sectionsLoading ? (
                <div className="space-y-3">
                  {[...Array(3)].map((_, i) => (
                    <div key={i} className="p-4 border rounded-lg">
                      <Skeleton className="h-6 w-1/4 mb-2" />
                      <Skeleton className="h-32 w-full" />
                    </div>
                  ))}
                </div>
              ) : sections?.length === 0 ? (
                <div className="text-center py-8">
                  <Type className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
                  <h3 className="text-lg font-medium mb-2">No sections yet</h3>
                  <p className="text-muted-foreground mb-4">Add sections to build your proposal</p>
                  <Button onClick={handleAddSection}>
                    <Plus className="mr-2 h-4 w-4" />
                    Add First Section
                  </Button>
                </div>
              ) : (
                <div className="space-y-3">
                  {sections?.map((section, index) => (
                    <div
                      key={section.id}
                      className="border rounded-lg overflow-hidden"
                    >
                      <div className="flex items-center gap-3 p-3 bg-muted/30 border-b">
                        <span className="text-sm text-muted-foreground w-8 text-center">{index + 1}</span>
                        {editingSectionId === section.id ? (
                          <>
                            <Input
                              value={section.title}
                              onChange={(e) => updateSectionMutation.mutate({ id: section.id, data: { title: e.target.value } })}
                              className="flex-1 max-w-md"
                            />
                            <Button variant="ghost" size="icon" onClick={() => handleSectionSave(section.id)}>
                              <Save className="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" size="icon" onClick={() => setEditingSectionId(null)}>
                              <ChevronDown className="h-4 w-4" />
                            </Button>
                          </>
                        ) : (
                          <>
                            <span className="font-medium flex-1" onDoubleClick={() => startEditing(section)}>{section.title}</span>
                            <div className="flex items-center gap-1">
                              <Button variant="ghost" size="icon" onClick={() => handleReorder(section.id, 'up')} disabled={index === 0}>
                                <ChevronUp className="h-4 w-4" />
                              </Button>
                              <Button variant="ghost" size="icon" onClick={() => handleReorder(section.id, 'down')} disabled={index === sections!.length - 1}>
                                <ChevronDown className="h-4 w-4" />
                              </Button>
                              <Button variant="ghost" size="icon" onClick={() => startEditing(section)}>
                                <Edit className="h-4 w-4" />
                              </Button>
                              <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                  <Button variant="ghost" size="icon">
                                    <MoreVertical className="h-4 w-4" />
                                  </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end">
                                  <DropdownMenuItem onClick={() => startEditing(section)}>
                                    <Edit className="mr-2 h-4 w-4" />
                                    Edit Title
                                  </DropdownMenuItem>
                                  <DropdownMenuSeparator />
                                  <DropdownMenuItem
                                    onClick={() => deleteSectionMutation.mutate(section.id)}
                                    className="text-destructive focus:text-destructive"
                                  >
                                    <Trash2 className="mr-2 h-4 w-4" />
                                    Delete Section
                                  </DropdownMenuItem>
                                </DropdownMenuContent>
                              </DropdownMenu>
                            </div>
                          </>
                        )}
                      </div>
                      <div className="p-3">
                        {editingSectionId === section.id ? (
                          <Textarea
                            value={sectionContent}
                            onChange={(e) => setSectionContent(e.target.value)}
                            className="min-h-[200px] font-mono text-sm"
                            placeholder="Write your section content here..."
                          />
                        ) : (
                          <div className="prose max-w-none min-h-[100px]">
                            {section.content ? (
                              <div className="whitespace-pre-wrap">{section.content}</div>
                            ) : (
                              <p className="text-muted-foreground italic">Click to edit or double-click title to edit content</p>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Preview Tab */}
        <TabsContent value="preview">
          <Card>
            <CardHeader>
              <CardTitle>Proposal Preview</CardTitle>
              <CardDescription>Full proposal rendered as it would appear in export</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="prose max-w-3xl mx-auto p-8 border rounded-lg bg-background">
                <h1 className="text-3xl font-bold text-center mb-2">{proposal.title}</h1>
                <p className="text-center text-muted-foreground mb-8">Version {proposal.version} • {statusInfo.label}</p>

                {proposal.executive_summary && (
                  <div className="mb-8 p-4 bg-muted/50 rounded-lg">
                    <h2 className="text-xl font-bold mb-2">Executive Summary</h2>
                    <div className="whitespace-pre-wrap">{proposal.executive_summary}</div>
                  </div>
                )}

                {sections?.map((section, index) => (
                  <div key={section.id} className="mb-8">
                    <h2 className="text-xl font-bold border-b pb-2 mb-3">{index + 1}. {section.title}</h2>
                    <div className="whitespace-pre-wrap text-base leading-relaxed">
                      {section.content || <span className="text-muted-foreground italic">[Section content pending]</span>}
                    </div>
                  </div>
                ))}

                {sections?.length === 0 && (
                  <p className="text-center text-muted-foreground py-12">No sections added yet. Switch to the Editor tab to add content.</p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Exports Tab */}
        <TabsContent value="exports">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Export History</CardTitle>
                <CardDescription>Download previous exports or generate new ones</CardDescription>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => exportMutation.mutate('PDF')} loading={exportMutation.isPending}>
                  <FileText className="mr-2 h-4 w-4" />
                  Export PDF
                </Button>
                <Button variant="outline" size="sm" onClick={() => exportMutation.mutate('DOCX')} loading={exportMutation.isPending}>
                  <FileCheck className="mr-2 h-4 w-4" />
                  Export DOCX
                </Button>
                <Button variant="outline" size="sm" onClick={() => exportMutation.mutate('HTML')} loading={exportMutation.isPending}>
                  <Layout className="mr-2 h-4 w-4" />
                  Export HTML
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {exports?.length === 0 ? (
                <div className="text-center py-8">
                  <Download className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
                  <h3 className="text-lg font-medium mb-2">No exports yet</h3>
                  <p className="text-muted-foreground mb-4">Generate exports to download your proposal in various formats</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {exports?.map((exp: Export) => (
                    <div
                      key={exp.id}
                      className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <FileText className="h-8 w-8 text-primary" />
                        <div>
                          <p className="font-medium capitalize">{exp.export_format.toLowerCase()} Export</p>
                          <p className="text-sm text-muted-foreground">
                            {format(new Date(exp.created_at), 'MMM d, yyyy HH:mm')} • {exp.status}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {exp.status === 'Completed' && exp.file_path && (
                          <Button variant="ghost" size="icon" asChild>
                            <a href={exp.file_path} download>
                              <Download className="h-4 w-4" />
                            </a>
                          </Button>
                        )}
                        <Badge variant={exp.status === 'Completed' ? 'success' : exp.status === 'Failed' ? 'destructive' : 'warning'}>
                          {exp.status}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}