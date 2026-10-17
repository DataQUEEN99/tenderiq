'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
import {
  Plus,
  Search,
  Filter,
  Download,
  MoreVertical,
  Edit,
  Trash2,
  Eye,
  FileText,
  AlertTriangle,
  CheckCircle,
  Clock,
  Archive,
  XCircle,
} from 'lucide-react';
import { apiClient } from '../api/client';
import type { Tender, PaginatedResponse } from '../types';
import {
  Button,
} from '../components/ui/button';
import {
  Input,
} from '../components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from '../components/ui/table';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from '../components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import {
  Badge,
} from '../components/ui/badge';
import {
  Skeleton,
} from '../components/ui/skeleton';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { format } from 'date-fns';
import { cn } from '../utils/cn';

const statusOptions = [
  { value: 'all', label: 'All Statuses' },
  { value: 'Draft', label: 'Draft' },
  { value: 'Published', label: 'Published' },
  { value: 'In Progress', label: 'In Progress' },
  { value: 'Submitted', label: 'Submitted' },
  { value: 'Awarded', label: 'Awarded' },
  { value: 'Lost', label: 'Lost' },
  { value: 'Archived', label: 'Archived' },
];

function getStatusBadge(status: string) {
  const variants: Record<string, 'default' | 'success' | 'warning' | 'destructive'> = {
    Draft: 'default',
    Published: 'success',
    'In Progress': 'success',
    Submitted: 'warning',
    Awarded: 'success',
    Lost: 'destructive',
    Archived: 'default',
  };
  return <Badge variant={variants[status] || 'default'}>{status}</Badge>;
}

export function TendersPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  // New Tender Modal State
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [formTitle, setFormTitle] = useState('');
  const [formRefNumber, setFormRefNumber] = useState('');
  const [formIssuingAuth, setFormIssuingAuth] = useState('');
  const [formEstimatedVal, setFormEstimatedVal] = useState('');
  const [formContractDuration, setFormContractDuration] = useState('');
  const [formDeadline, setFormDeadline] = useState('');
  const [formDescription, setFormDescription] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { data, isLoading, error } = useQuery({
    queryKey: ['tenders', page, pageSize],
    queryFn: () => apiClient.listTenders({ page, page_size: pageSize }),
  });

  const createTenderMutation = useMutation({
    mutationFn: async () => {
      setIsSubmitting(true);
      try {
        const tender = await apiClient.createTender({
          title: formTitle,
          reference_number: formRefNumber,
          issuing_authority: formIssuingAuth || undefined,
          estimated_value: formEstimatedVal || undefined,
          contract_duration: formContractDuration || undefined,
          description: formDescription || undefined,
          submission_deadline: formDeadline ? new Date(formDeadline).toISOString() : undefined,
          status: 'Draft',
        });

        if (selectedFile && tender.id) {
          await apiClient.uploadDocument(selectedFile, tender.id, 'Tender');
        }

        return tender;
      } finally {
        setIsSubmitting(false);
      }
    },
    onSuccess: (tender) => {
      queryClient.invalidateQueries({ queryKey: ['tenders'] });
      setShowCreateDialog(false);
      // Reset form
      setFormTitle('');
      setFormRefNumber('');
      setFormIssuingAuth('');
      setFormEstimatedVal('');
      setFormContractDuration('');
      setFormDeadline('');
      setFormDescription('');
      setSelectedFile(null);
      if (tender?.id) {
        navigate(`/tenders/${tender.id}`);
      }
    },
    onError: (err: any) => {
      alert(`Failed to create tender: ${err?.message || 'Unknown error'}`);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (tenderId: string) => apiClient.deleteTender(tenderId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tenders'] });
    },
  });

  const handleDelete = (tenderId: string) => {
    if (confirm('Are you sure you want to delete this tender? This action cannot be undone.')) {
      deleteMutation.mutate(tenderId);
    }
  };

  if (error) {
    return (
      <Card>
        <CardContent className="py-8 text-center">
          <p className="text-destructive">Failed to load tenders: {error.message}</p>
        </CardContent>
      </Card>
    );
  }

  const filteredTenders = (data?.items || []).filter((tender) => {
    if (statusFilter && statusFilter !== 'all' && tender.status !== statusFilter) return false;
    if (search) {
      const q = search.toLowerCase();
      const matchTitle = tender.title?.toLowerCase().includes(q);
      const matchRef = tender.reference_number?.toLowerCase().includes(q);
      if (!matchTitle && !matchRef) return false;
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Tenders</h1>
          <p className="text-muted-foreground">Manage your tender opportunities</p>
        </div>
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="mr-2 h-4 w-4" />
          New Tender
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search tenders..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-full sm:w-[180px]">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                {statusOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Tenders Table */}
      <Card>
        <CardContent className="pt-0">
          {isLoading ? (
            <div className="p-6">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Title</TableHead>
                    <TableHead>Reference</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Deadline</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {[...Array(5)].map((_, i) => (
                    <TableRow key={i}>
                      <TableCell><Skeleton className="h-4 w-3/4" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-1/2" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-20" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-24" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-24" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-16" /></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <>
              {filteredTenders.length === 0 ? (
                <div className="p-12 text-center">
                  <FileText className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
                  <h3 className="text-lg font-medium mb-2">No tenders found</h3>
                  <p className="text-muted-foreground mb-4">
                    {search || statusFilter !== 'all' ? 'Try adjusting your filters' : 'Get started by creating your first tender'}
                  </p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Title</TableHead>
                      <TableHead>Reference</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Deadline</TableHead>
                      <TableHead>Created</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredTenders.map((tender: Tender) => (
                      <TableRow key={tender.id}>
                        <TableCell>
                          <Link to={`/tenders/${tender.id}`} className="font-medium hover:text-primary">
                            {tender.title}
                          </Link>
                        </TableCell>
                        <TableCell className="font-mono text-sm">{tender.reference_number}</TableCell>
                        <TableCell>{getStatusBadge(tender.status)}</TableCell>
                        <TableCell>
                          {tender.submission_deadline ? (
                            format(new Date(tender.submission_deadline), 'MMM d, yyyy')
                          ) : (
                            <span className="text-muted-foreground">—</span>
                          )}
                        </TableCell>
                        <TableCell>
                          {format(new Date(tender.created_at), 'MMM d, yyyy')}
                        </TableCell>
                        <TableCell className="text-right">
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon">
                                <MoreVertical className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem asChild>
                                <Link to={`/tenders/${tender.id}`}>
                                  <Eye className="mr-2 h-4 w-4" />
                                  View Details
                                </Link>
                              </DropdownMenuItem>
                              <DropdownMenuItem asChild>
                                <Link to={`/tenders/${tender.id}/edit`}>
                                  <Edit className="mr-2 h-4 w-4" />
                                  Edit
                                </Link>
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                onClick={() => handleDelete(tender.id)}
                                className="text-destructive focus:text-destructive"
                              >
                                <Trash2 className="mr-2 h-4 w-4" />
                                Delete
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </>
          )}

          {/* Pagination */}
          {data && data.total > pageSize && (
            <div className="flex items-center justify-between px-4 py-4 border-t">
              <div className="text-sm text-muted-foreground">
                Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, data.total)} of {data.total} results
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => p + 1)}
                  disabled={page * pageSize >= data.total}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* New Tender Modal */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create New Tender</DialogTitle>
            <DialogDescription>
              Enter the RFP details and optionally attach the RFP document to start AI analysis.
            </DialogDescription>
          </DialogHeader>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (!formTitle.trim() || !formRefNumber.trim()) {
                alert('Title and Reference Number are required.');
                return;
              }
              createTenderMutation.mutate();
            }}
            className="space-y-4 py-2"
          >
            <div className="space-y-2">
              <label className="text-sm font-medium">Tender Title *</label>
              <Input
                placeholder="e.g. Healthcare IT Cloud Modernization RFP"
                value={formTitle}
                onChange={(e) => setFormTitle(e.target.value)}
                required
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Reference Number *</label>
                <Input
                  placeholder="e.g. RFP-2026-HC-101"
                  value={formRefNumber}
                  onChange={(e) => setFormRefNumber(e.target.value)}
                  required
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Issuing Authority</label>
                <Input
                  placeholder="e.g. Ministry of Health"
                  value={formIssuingAuth}
                  onChange={(e) => setFormIssuingAuth(e.target.value)}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Estimated Value</label>
                <Input
                  placeholder="e.g. 5000000"
                  value={formEstimatedVal}
                  onChange={(e) => setFormEstimatedVal(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Contract Duration</label>
                <Input
                  placeholder="e.g. 24 Months"
                  value={formContractDuration}
                  onChange={(e) => setFormContractDuration(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Submission Deadline</label>
                <Input
                  type="date"
                  value={formDeadline}
                  onChange={(e) => setFormDeadline(e.target.value)}
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Description / Scope Summary</label>
              <Textarea
                placeholder="Brief summary of tender scope, objectives, or key deliverables..."
                value={formDescription}
                onChange={(e) => setFormDescription(e.target.value)}
                rows={3}
              />
            </div>

            <div className="space-y-2 p-3 bg-muted/50 rounded-lg border">
              <label className="text-sm font-medium block">Attach Tender RFP Document (.pdf, .docx, .txt)</label>
              <Input
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  setSelectedFile(file || null);
                }}
              />
              <p className="text-xs text-muted-foreground">
                Document will be chunked, embedded, and indexed into the Chroma vector database automatically.
              </p>
            </div>

            <DialogFooter className="pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowCreateDialog(false)}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? 'Creating Tender...' : 'Create Tender'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}