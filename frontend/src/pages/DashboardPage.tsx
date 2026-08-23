'use client';

import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  FileText,
  Briefcase,
  TrendingUp,
  Clock,
  Plus,
  ArrowUpRight,
  FileCheck,
  AlertTriangle,
  Trophy,
} from 'lucide-react';
import { apiClient } from '../api/client';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Skeleton } from '../components/ui/skeleton';
import { format } from 'date-fns';

interface DashboardStats {
  total_tenders: number;
  active_tenders: number;
  total_proposals: number;
  won_proposals: number;
  pending_ai_tasks: number;
  win_rate: number;
}

interface RecentTender {
  id: string;
  title: string;
  reference_number: string;
  status: string;
  submission_deadline?: string;
  created_at: string;
}

interface RecentProposal {
  id: string;
  title: string;
  version: number;
  status: string;
  compliance_score?: number;
  tender_id: string;
  tender_title?: string;
  created_at: string;
}

function StatCard({
  title,
  value,
  change,
  icon: Icon,
  color = 'primary',
  href,
}: {
  title: string;
  value: number | string;
  change?: { value: number; label: string };
  icon: React.ComponentType<{ className?: string }>;
  color?: 'primary' | 'success' | 'warning' | 'destructive';
  href?: string;
}) {
  const colorClasses = {
    primary: 'bg-blue-500 text-white',
    success: 'bg-green-500 text-white',
    warning: 'bg-yellow-500 text-white',
    destructive: 'bg-red-500 text-white',
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <div className={`${colorClasses[color]} p-2 rounded-lg`}>
          <Icon className="h-4 w-4" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {change && (
          <p className="text-xs text-muted-foreground mt-1">
            {change.value > 0 ? '+' : ''}{change.value}% {change.label}
          </p>
        )}
      </CardContent>
      {href && (
        <CardFooter className="pt-0">
          <Button variant="ghost" size="sm" className="w-full" asChild>
            <Link to={href}>
              View details <ArrowUpRight className="ml-1 h-3 w-3" />
            </Link>
          </Button>
        </CardFooter>
      )}
    </Card>
  );
}

function RecentTendersTable({ tenders, isLoading }: { tenders: RecentTender[]; isLoading: boolean }) {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="flex items-center gap-4">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-1/4" />
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-4 w-24" />
          </div>
        ))}
      </div>
    );
  }

  if (tenders.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No tenders yet. <Link to="/tenders" className="text-primary hover:underline">Create your first tender</Link>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {tenders.map((tender) => (
        <Link
          key={tender.id}
          to={`/tenders/${tender.id}`}
          className="flex items-center justify-between p-3 rounded-lg hover:bg-accent transition-colors"
        >
          <div className="flex items-center gap-3 min-w-0">
            <FileText className="h-5 w-5 text-muted-foreground flex-shrink-0" />
            <div className="min-w-0">
              <p className="font-medium truncate">{tender.title}</p>
              <p className="text-sm text-muted-foreground">{tender.reference_number}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant={getStatusVariant(tender.status)}>{tender.status}</Badge>
            {tender.submission_deadline && (
              <span className="text-sm text-muted-foreground">
                Due: {format(new Date(tender.submission_deadline), 'MMM d, yyyy')}
              </span>
            )}
          </div>
        </Link>
      ))}
    </div>
  );
}

function RecentProposalsTable({ proposals, isLoading }: { proposals: RecentProposal[]; isLoading: boolean }) {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="flex items-center gap-4">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-1/4" />
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-4 w-24" />
          </div>
        ))}
      </div>
    );
  }

  if (proposals.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No proposals yet. <Link to="/proposals" className="text-primary hover:underline">Create your first proposal</Link>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {proposals.map((proposal) => (
        <Link
          key={proposal.id}
          to={`/proposals/${proposal.id}`}
          className="flex items-center justify-between p-3 rounded-lg hover:bg-accent transition-colors"
        >
          <div className="flex items-center gap-3 min-w-0">
            <Briefcase className="h-5 w-5 text-muted-foreground flex-shrink-0" />
            <div className="min-w-0">
              <p className="font-medium truncate">{proposal.title}</p>
              <p className="text-sm text-muted-foreground">v{proposal.version} • {proposal.tender_title || 'Unknown tender'}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant={getProposalStatusVariant(proposal.status)}>{proposal.status}</Badge>
            {proposal.compliance_score !== undefined && (
              <span className="text-sm font-medium">
                {proposal.compliance_score}%
              </span>
            )}
          </div>
        </Link>
      ))}
    </div>
  );
}

function getStatusVariant(status: string): 'default' | 'success' | 'warning' | 'destructive' {
  switch (status) {
    case 'Published':
    case 'In Progress':
      return 'success';
    case 'Draft':
      return 'default';
    case 'Submitted':
      return 'warning';
    case 'Awarded':
    case 'Won':
      return 'success';
    case 'Lost':
    case 'Archived':
      return 'destructive';
    default:
      return 'default';
  }
}

function getProposalStatusVariant(status: string): 'default' | 'success' | 'warning' | 'destructive' {
  switch (status) {
    case 'Finalized':
    case 'Submitted':
      return 'success';
    case 'Draft':
    case 'In Review':
      return 'default';
    case 'Won':
      return 'success';
    case 'Lost':
    case 'Archived':
      return 'destructive';
    default:
      return 'default';
  }
}

export function DashboardPage() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      // Fetch stats from multiple endpoints
      const [tenders, proposals] = await Promise.all([
        apiClient.listTenders({ page_size: 100 }),
        apiClient.listProposals({ page_size: 100 }),
      ]);

      const totalTenders = tenders.total;
      const activeTenders = tenders.items.filter((t) => ['Published', 'In Progress'].includes(t.status)).length;
      const totalProposals = proposals.total;
      const wonProposals = proposals.items.filter((p) => p.status === 'Won').length;
      const winRate = totalProposals > 0 ? Math.round((wonProposals / totalProposals) * 100) : 0;

      return {
        total_tenders: totalTenders,
        active_tenders: activeTenders,
        total_proposals: totalProposals,
        won_proposals: wonProposals,
        win_rate: winRate,
        pending_ai_tasks: 0, // Would need separate endpoint
      } as DashboardStats;
    },
  });

  const { data: recentTenders, isLoading: tendersLoading } = useQuery({
    queryKey: ['recent-tenders'],
    queryFn: () => apiClient.listTenders({ page_size: 5 }),
  });

  const { data: recentProposals, isLoading: proposalsLoading } = useQuery({
    queryKey: ['recent-proposals'],
    queryFn: () => apiClient.listProposals({ page_size: 5 }),
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">Overview of your tender and proposal activity</p>
        </div>
        <Button asChild>
          <Link to="/tenders">
            <Plus className="mr-2 h-4 w-4" />
            New Tender
          </Link>
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Tenders"
          value={stats?.total_tenders || 0}
          icon={FileText}
          color="primary"
          href="/tenders"
        />
        <StatCard
          title="Active Tenders"
          value={stats?.active_tenders || 0}
          icon={TrendingUp}
          color="success"
          href="/tenders"
        />
        <StatCard
          title="Total Proposals"
          value={stats?.total_proposals || 0}
          icon={Briefcase}
          color="warning"
          href="/proposals"
        />
        <StatCard
          title="Win Rate"
          value={`${stats?.win_rate || 0}%`}
          icon={Trophy}
          color="primary"
          href="/proposals"
        />
      </div>

      {/* Recent Activity */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Recent Tenders */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Recent Tenders</CardTitle>
                <CardDescription>Latest tender opportunities</CardDescription>
              </div>
              <Button variant="ghost" size="sm" asChild>
                <Link to="/tenders">View all</Link>
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <RecentTendersTable tenders={recentTenders?.items || []} isLoading={tendersLoading} />
          </CardContent>
        </Card>

        {/* Recent Proposals */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Recent Proposals</CardTitle>
                <CardDescription>Your latest proposal drafts</CardDescription>
              </div>
              <Button variant="ghost" size="sm" asChild>
                <Link to="/proposals">View all</Link>
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <RecentProposalsTable proposals={recentProposals?.items || []} isLoading={proposalsLoading} />
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Common tasks to get you started</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Button variant="outline" asChild className="h-auto p-4 flex flex-col items-center gap-2">
              <Link to="/tenders">
                <FileText className="h-8 w-8" />
                <span className="font-medium">Upload Tender</span>
                <span className="text-xs text-muted-foreground">Process a new RFP document</span>
              </Link>
            </Button>
            <Button variant="outline" asChild className="h-auto p-4 flex flex-col items-center gap-2">
              <Link to="/company-profile">
                <FileCheck className="h-8 w-8" />
                <span className="font-medium">Company Profile</span>
                <span className="text-xs text-muted-foreground">Update your company info</span>
              </Link>
            </Button>
            <Button variant="outline" asChild className="h-auto p-4 flex flex-col items-center gap-2">
              <Link to="/chat">
                <ArrowUpRight className="h-8 w-8 rotate-45" />
                <span className="font-medium">AI Chat</span>
                <span className="text-xs text-muted-foreground">Ask questions about tenders</span>
              </Link>
            </Button>
            <Button variant="outline" asChild className="h-auto p-4 flex flex-col items-center gap-2">
              <Link to="/proposals">
                <Briefcase className="h-8 w-8" />
                <span className="font-medium">Create Proposal</span>
                <span className="text-xs text-muted-foreground">Generate a new proposal draft</span>
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}