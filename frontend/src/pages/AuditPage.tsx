'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Search,
  Filter,
  Download,
  ChevronDown,
  ChevronUp,
  MoreHorizontal,
  Eye,
  FileText,
  User,
  Clock,
  AlertTriangle,
  CheckCircle,
  XCircle,
  HelpCircle,
  Loader2,
  Database,
  Shield,
  Activity,
  Terminal,
  Mail,
  Bell,
  Plus,
  Edit,
  Trash2,
  LogIn,
  LogOut,
  Upload,
  Send,
  FileCheck,
  Building2,
  MessageSquare,
  Settings,
} from 'lucide-react';
import { apiClient } from '../api/client';
import type { AuditLog } from '../types';
import { format, formatDistanceToNow, parseISO } from 'date-fns';
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
  Input,
} from '../components/ui/input';
import {
  Badge,
} from '../components/ui/badge';
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  TableCaption,
} from '../components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '../components/ui/dialog';
import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from '../components/ui/tabs';
import {
  Skeleton,
} from '../components/ui/skeleton';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '../components/ui/tooltip';
import { Separator } from '../components/ui/separator';
import { Pagination } from '../components/ui/pagination';
import { cn } from '../utils/cn';

const actionConfig: Record<string, { label: string; icon: React.ComponentType<{ className?: string }>; color: string }> = {
  CREATE: { label: 'Created', icon: Plus, color: 'text-green-600 bg-green-100' },
  UPDATE: { label: 'Updated', icon: Edit, color: 'text-blue-600 bg-blue-100' },
  DELETE: { label: 'Deleted', icon: Trash2, color: 'text-red-600 bg-red-100' },
  LOGIN: { label: 'Login', icon: LogIn, color: 'text-purple-600 bg-purple-100' },
  LOGOUT: { label: 'Logout', icon: LogOut, color: 'text-gray-600 bg-gray-100' },
  EXPORT: { label: 'Exported', icon: Download, color: 'text-orange-600 bg-orange-100' },
  IMPORT: { label: 'Imported', icon: Upload, color: 'text-cyan-600 bg-cyan-100' },
  VIEW: { label: 'Viewed', icon: Eye, color: 'text-indigo-600 bg-indigo-100' },
  SUBMIT: { label: 'Submitted', icon: Send, color: 'text-emerald-600 bg-emerald-100' },
  APPROVE: { label: 'Approved', icon: CheckCircle, color: 'text-green-600 bg-green-100' },
  REJECT: { label: 'Rejected', icon: XCircle, color: 'text-red-600 bg-red-100' },
  ERROR: { label: 'Error', icon: AlertTriangle, color: 'text-red-600 bg-red-100' },
};

const resourceConfig: Record<string, { label: string; icon: React.ComponentType<{ className?: string }> }> = {
  tender: { label: 'Tender', icon: FileText },
  proposal: { label: 'Proposal', icon: FileCheck },
  company: { label: 'Company', icon: Building2 },
  user: { label: 'User', icon: User },
  chat: { label: 'Chat', icon: MessageSquare },
  export: { label: 'Export', icon: Download },
  settings: { label: 'Settings', icon: Settings },
  auth: { label: 'Auth', icon: Shield },
};

export function AuditPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [actionFilter, setActionFilter] = useState<string>('all');
  const [resourceFilter, setResourceFilter] = useState<string>('all');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);
  const [showDetailsDialog, setShowDetailsDialog] = useState(false);

  const { data: auditData, isLoading, error } = useQuery({
    queryKey: ['audit-logs', { page, pageSize, search: searchQuery, action: actionFilter, resource: resourceFilter, dateFrom, dateTo }],
    queryFn: () => apiClient.listAuditLogs({ page, limit: pageSize, search: searchQuery, action: actionFilter, resource_type: resourceFilter, date_from: dateFrom, date_to: dateTo }),
  });

  const logs = auditData?.items || [];
  const total = auditData?.total || 0;
  const totalPages = Math.ceil(total / pageSize);

  const uniqueActions = [...new Set(logs.map(log => log.action).filter(Boolean))].sort();
  const uniqueResources = [...new Set(logs.map(log => log.resource_type).filter(Boolean))].sort();

  const handleExport = () => {
    apiClient.exportAuditLogs({ search: searchQuery, action: actionFilter, resource_type: resourceFilter, date_from: dateFrom, date_to: dateTo })
      .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `audit-logs-${format(new Date(), 'yyyy-MM-dd')}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      });
  };

  const getActionBadge = (action: string) => {
    const config = actionConfig[action] || { label: action, icon: Activity, color: 'text-gray-600 bg-gray-100' };
    const Icon = config.icon;
    return (
      <Badge variant="secondary" className={cn('gap-1', config.color)}>
        <Icon className="h-3 w-3" />
        {config.label}
      </Badge>
    );
  };

  const getResourceBadge = (resourceType: string) => {
    const config = resourceConfig[resourceType] || { label: resourceType, icon: Database };
    const Icon = config.icon;
    return (
      <Badge variant="outline" className="gap-1">
        <Icon className="h-3 w-3" />
        {config.label}
      </Badge>
    );
  };

  const formatDetails = (details: Record<string, any>) => {
    return Object.entries(details).map(([key, value]) => (
      <div key={key} className="flex gap-4 py-2 border-b last:border-0">
        <span className="text-sm font-medium text-muted-foreground w-40">{key}</span>
        <span className="text-sm font-mono text-xs break-all">{JSON.stringify(value, null, 2)}</span>
      </div>
    ));
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-4 w-64" />
          </div>
          <div className="flex gap-2">
            <Skeleton className="h-10 w-32" />
            <Skeleton className="h-10 w-32" />
          </div>
        </div>
        <Card>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="pb-3 text-left">Timestamp</th>
                    <th className="pb-3 text-left">Action</th>
                    <th className="pb-3 text-left">Resource</th>
                    <th className="pb-3 text-left">User</th>
                    <th className="pb-3 text-left">Details</th>
                  </tr>
                </thead>
                <tbody>
                  {[...Array(5)].map((_, i) => (
                    <tr key={i} className="border-b">
                      <td className="py-3"><Skeleton className="h-4 w-32" /></td>
                      <td className="py-3"><Skeleton className="h-4 w-24" /></td>
                      <td className="py-3"><Skeleton className="h-4 w-20" /></td>
                      <td className="py-3"><Skeleton className="h-4 w-28" /></td>
                      <td className="py-3"><Skeleton className="h-4 w-40" /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="mx-auto h-12 w-12 text-destructive mb-4" />
        <h3 className="text-lg font-medium mb-2">Failed to load audit logs</h3>
        <p className="text-muted-foreground mb-4">Please try refreshing the page</p>
        <Button onClick={() => window.location.reload()}>Retry</Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Audit Logs</h1>
          <p className="text-muted-foreground">Track all system activities and changes</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={handleExport}>
            <Download className="mr-2 h-4 w-4" />
            Export CSV
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1 relative max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search logs..."
                value={searchQuery}
                onChange={(e) => { setSearchQuery(e.target.value); setPage(1); }}
                className="pl-10"
              />
            </div>

            <Select value={actionFilter} onValueChange={(v) => { setActionFilter(v); setPage(1); }} className="w-full sm:w-48">
              <SelectTrigger>
                <SelectValue placeholder="All Actions" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Actions</SelectItem>
                {uniqueActions.map(action => (
                  <SelectItem key={action} value={action}>
                    {actionConfig[action]?.label || action}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={resourceFilter} onValueChange={(v) => { setResourceFilter(v); setPage(1); }} className="w-full sm:w-48">
              <SelectTrigger>
                <SelectValue placeholder="All Resources" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Resources</SelectItem>
                {uniqueResources.map(resource => (
                  <SelectItem key={resource} value={resource}>
                    {resourceConfig[resource]?.label || resource}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <div className="flex gap-2">
              <Input
                type="date"
                value={dateFrom}
                onChange={(e) => { setDateFrom(e.target.value); setPage(1); }}
                placeholder="From"
                className="w-40"
              />
              <Input
                type="date"
                value={dateTo}
                onChange={(e) => { setDateTo(e.target.value); setPage(1); }}
                placeholder="To"
                className="w-40"
              />
            </div>

            <Select value={pageSize} onValueChange={(v) => { setPageSize(Number(v)); setPage(1); }} className="w-36">
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="10">10 per page</SelectItem>
                <SelectItem value="25">25 per page</SelectItem>
                <SelectItem value="50">50 per page</SelectItem>
                <SelectItem value="100">100 per page</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Stats Summary */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-primary/10 rounded-lg">
                <Activity className="h-6 w-6 text-primary" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Events</p>
                <p className="text-2xl font-bold">{total.toLocaleString()}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-green-100 rounded-lg">
                <CheckCircle className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Successful Actions</p>
                <p className="text-2xl font-bold">
                  {logs.filter(l => !l.action.includes('ERROR') && !l.action.includes('REJECT') && !l.action.includes('DELETE')).length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-red-100 rounded-lg">
                <AlertTriangle className="h-6 w-6 text-red-600" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Errors & Failures</p>
                <p className="text-2xl font-bold">
                  {logs.filter(l => l.action.includes('ERROR') || l.action.includes('REJECT')).length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-100 rounded-lg">
                <User className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Unique Users</p>
                <p className="text-2xl font-bold">
                  {[...new Set(logs.map(l => l.user_id))].length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Logs Table */}
      <Card>
        <CardContent>
          {logs.length === 0 ? (
            <div className="text-center py-12">
              <Database className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
              <h3 className="text-lg font-medium mb-2">No audit logs found</h3>
              <p className="text-muted-foreground">Try adjusting your filters or search query</p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-40">Timestamp</TableHead>
                      <TableHead className="w-32">Action</TableHead>
                      <TableHead className="w-32">Resource</TableHead>
                      <TableHead className="w-40">User</TableHead>
                      <TableHead>Details</TableHead>
                      <TableHead className="w-32">IP Address</TableHead>
                      <TableHead className="w-24">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {logs.map((log) => (
                      <TableRow key={log.id} className="hover:bg-muted/50 cursor-pointer" onClick={() => { setSelectedLog(log); setShowDetailsDialog(true); }}>
                        <TableCell className="font-mono text-xs whitespace-nowrap">
                          {log.created_at ? format(new Date(log.created_at), 'MMM d, yyyy HH:mm:ss') : '—'}
                        </TableCell>
                        <TableCell>{getActionBadge(log.action)}</TableCell>
                        <TableCell>{getResourceBadge(log.resource_type)}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center">
                              <span className="text-xs font-medium text-primary">
                                {log.user_email?.charAt(0).toUpperCase() || '?'}
                              </span>
                            </div>
                            <div>
                              <p className="text-sm font-medium">{log.user_email || 'System'}</p>
                              <p className="text-xs text-muted-foreground">{log.user_role || ''}</p>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell className="max-w-xs">
                          <div className="text-sm text-muted-foreground truncate font-mono">
                            {log.resource_id ? `${log.resource_type}:${log.resource_id}` : 'N/A'}
                          </div>
                        </TableCell>
                        <TableCell className="font-mono text-xs text-muted-foreground">
                          {log.ip_address || '—'}
                        </TableCell>
                        <TableCell>
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button variant="ghost" size="icon" className="h-6 w-6">
                                  <MoreHorizontal className="h-4 w-4" />
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>View details</TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between pt-4 border-t">
                  <div className="text-sm text-muted-foreground">
                    Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, total)} of {total} results
                  </div>
                  <Pagination
                    currentPage={page}
                    totalPages={totalPages}
                    onPageChange={setPage}
                    showFirstLast
                    maxPages={5}
                  />
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Details Dialog */}
      <Dialog open={showDetailsDialog} onOpenChange={setShowDetailsDialog}>
        <DialogContent className="max-w-3xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle>Audit Log Details</DialogTitle>
            <DialogDescription>Complete information for this audit entry</DialogDescription>
          </DialogHeader>
          {selectedLog && (
            <div className="space-y-4 py-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Event ID</p>
                  <p className="font-mono text-xs break-all">{selectedLog.id}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Timestamp</p>
                  <p className="font-mono text-xs">{selectedLog.created_at ? format(new Date(selectedLog.created_at), 'MMMM d, yyyy HH:mm:ss') : '—'}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Action</p>
                  <p className="font-medium">{actionConfig[selectedLog.action]?.label || selectedLog.action}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Resource Type</p>
                  <p className="font-medium">{resourceConfig[selectedLog.resource_type]?.label || selectedLog.resource_type}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Resource ID</p>
                  <p className="font-mono text-xs">{selectedLog.resource_id || 'N/A'}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">User</p>
                  <p className="font-medium">{selectedLog.user_email || 'System'}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">User Role</p>
                  <p>{selectedLog.user_role || 'N/A'}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">IP Address</p>
                  <p className="font-mono text-xs">{selectedLog.ip_address || 'N/A'}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">User Agent</p>
                  <p className="font-mono text-xs truncate max-w-xs">{selectedLog.user_agent || 'N/A'}</p>
                </div>
              </div>

              {selectedLog.details && Object.keys(selectedLog.details).length > 0 && (
                <div className="space-y-2">
                  <p className="text-sm font-medium">Event Details</p>
                  <div className="bg-muted p-4 rounded-lg text-sm">
                    {formatDetails(selectedLog.details)}
                  </div>
                </div>
              )}

              {selectedLog.changes && Object.keys(selectedLog.changes).length > 0 && (
                <div className="space-y-2">
                  <p className="text-sm font-medium">Changes</p>
                  <div className="bg-muted p-4 rounded-lg text-sm">
                    {Object.entries(selectedLog.changes).map(([field, change]) => (
                      <div key={field} className="py-2 border-b last:border-0 flex gap-4">
                        <span className="font-medium text-muted-foreground w-40">{field}</span>
                        <div className="flex-1 flex gap-4">
                          <div className="flex-1">
                            <p className="text-xs text-red-600">Before: <span className="font-mono">{JSON.stringify(change.old)}</span></p>
                          </div>
                          <div className="flex-1">
                            <p className="text-xs text-green-600">After: <span className="font-mono">{JSON.stringify(change.new)}</span></p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}