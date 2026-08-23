'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  User,
  Bell,
  Shield,
  Key,
  Globe,
  Palette,
  Moon,
  Sun,
  Monitor,
  Save,
  Loader2,
  AlertCircle,
  CheckCircle,
  X,
  Eye,
  EyeOff,
  Mail,
  Phone,
  Lock,
  RotateCcw,
  Trash2,
  Plus,
  Download,
  FileText,
} from 'lucide-react';
import { apiClient } from '../api/client';
import type { User as UserType, CompanyProfile } from '../types';
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
  Input,
} from '../components/ui/input';
import {
  Label,
} from '../components/ui/label';
import {
  Badge,
} from '../components/ui/badge';
import {
  Separator,
} from '../components/ui/separator';
import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from '../components/ui/tabs';
import {
  Switch,
} from '../components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '../components/ui/dialog';
import {
  Avatar,
  AvatarImage,
  AvatarFallback,
} from '../components/ui/avatar';
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from '../components/ui/alert';
import { cn } from '../utils/cn';

const PLACEHOLDER_AVATAR = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTI4IiBoZWlnaHQ9IjEyOCIgdmlld0JveD0iMCAwIDEyOCAxMjgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIxMjgiIGhlaWdodD0iMTI4IiByeD0iMTYiIGZpbGw9IiNFNUU3ZWIiLz4KPHBhdGggZD0iTTY0IDQwQzU1LjcxNTcgNDAgNDggNDcuNzE1NyA0OCA1NlM1NS43MTU3IDcyIDY0IDcyUzc2IDY0LjI4NDMgNzYgNTZTNzAuMjg0MyA0MCA2NCA0MFoiIHN0cm9rZT0iIzk0QTNDNyIgc3Ryb2tlLXdpZHRoPSIyIi8+CjxwYXRoIGQ9Ik02NCA3NkM1NS43MTU3IDc2IDQ4IDY4LjI4NDMgNDggNjBTNTUuNzE1NyA0NCA2NCA0NEM3Mi4yODQzIDQ0IDgwIDUxLjcxNTcgODAgNjBTNzIuMjg0MyA3NiA2NCA3NloiIHN0cm9rZT0iIzk0QTNDNyIgc3Ryb2tlLXdpZHRoPSIyIi8+Cjwvc3ZnPgo=';

export function SettingsPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('profile');
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [showPasswordDialog, setShowPasswordDialog] = useState(false);
  const [showDeleteAccountDialog, setShowDeleteAccountDialog] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const { data: user, isLoading: userLoading } = useQuery({
    queryKey: ['current-user'],
    queryFn: () => apiClient.getCurrentUser(),
  });

  const { data: companyProfile } = useQuery({
    queryKey: ['company-profile'],
    queryFn: () => apiClient.getCompanyProfile(),
  });

  const updateProfileMutation = useMutation({
    mutationFn: (data: Partial<UserType>) => apiClient.updateCurrentUser(data),
    onSuccess: (updatedUser) => {
      queryClient.setQueryData(['current-user'], updatedUser);
    },
  });

  const updatePasswordMutation = useMutation({
    mutationFn: ({ current_password, new_password }: { current_password: string; new_password: string }) =>
      apiClient.changePassword(current_password, new_password),
    onSuccess: () => {
      setShowPasswordDialog(false);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    },
  });

  const deleteAccountMutation = useMutation({
    mutationFn: () => apiClient.deleteAccount(),
    onSuccess: () => {
      queryClient.clear();
      window.location.href = '/login';
    },
  });

  const uploadAvatarMutation = useMutation({
    mutationFn: (file: File) => apiClient.uploadAvatar(file),
    onSuccess: (response) => {
      queryClient.setQueryData(['current-user'], (old: UserType | undefined) =>
        old ? { ...old, avatar_url: response.url } : undefined
      );
      setAvatarPreview(null);
    },
  });

  const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.type.startsWith('image/')) {
        alert('Please select an image file');
        return;
      }
      if (file.size > 2 * 1024 * 1024) {
        alert('Image size must be less than 2MB');
        return;
      }
      const reader = new FileReader();
      reader.onload = (event) => {
        setAvatarPreview(event.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const confirmAvatarUpload = () => {
    const input = document.getElementById('avatar-upload') as HTMLInputElement;
    if (input?.files?.[0]) {
      uploadAvatarMutation.mutate(input.files[0]);
    }
  };

  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      alert('Passwords do not match');
      return;
    }
    if (newPassword.length < 8) {
      alert('Password must be at least 8 characters');
      return;
    }
    updatePasswordMutation.mutate({ current_password: currentPassword, new_password: newPassword });
  };

  const handleDeleteAccount = () => {
    if (deleteConfirmText !== 'DELETE') {
      alert('Please type "DELETE" to confirm');
      return;
    }
    deleteAccountMutation.mutate();
  };

  if (userLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <Skeleton className="h-8 w-48" />
        </div>
        <Card><CardContent className="py-8"><Skeleton className="h-64 w-full" /></CardContent></Card>
      </div>
    );
  }

  if (!user) {
    return (
      <Alert variant="destructive" className="mb-6">
        <AlertTitle>Unable to load settings</AlertTitle>
        <AlertDescription>Please try refreshing the page.</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground">Manage your account, preferences, and security</p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="profile">Profile</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
          <TabsTrigger value="appearance">Appearance</TabsTrigger>
          <TabsTrigger value="danger">Danger Zone</TabsTrigger>
        </TabsList>

        {/* Profile Tab */}
        <TabsContent value="profile" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Profile Information</CardTitle>
              <CardDescription>Update your personal information</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col md:flex-row gap-8">
                <div className="flex flex-col items-center md:w-48 md:shrink-0">
                  <div className="relative w-24 h-24 rounded-full overflow-hidden bg-muted border-2 border-dashed">
                    {avatarPreview ? (
                      <img src={avatarPreview} alt="Avatar preview" className="w-full h-full object-cover" />
                    ) : user.avatar_url ? (
                      <img src={user.avatar_url} alt="Avatar" className="w-full h-full object-cover" />
                    ) : (
                      <Avatar className="w-full h-full">
                        <AvatarFallback>{user.email.charAt(0).toUpperCase()}</AvatarFallback>
                      </Avatar>
                    )}
                  </div>
                  <div className="flex gap-2 mt-4">
                    <Button variant="outline" size="sm" onClick={() => document.getElementById('avatar-upload')?.click()}>
                      <Upload className="mr-2 h-4 w-4" />
                      Change
                    </Button>
                    {(avatarPreview || user.avatar_url) && (
                      <Button variant="ghost" size="sm" onClick={() => { setAvatarPreview(null); const input = document.getElementById('avatar-upload') as HTMLInputElement; if (input) input.value = ''; updateProfileMutation.mutate({ avatar_url: null }); }} className="text-destructive">
                        <X className="mr-2 h-4 w-4" />
                        Remove
                      </Button>
                    )}
                  </div>
                  <input id="avatar-upload" type="file" accept="image/*" onChange={handleAvatarChange} className="hidden" />
                  {avatarPreview && (
                    <div className="flex gap-2 mt-2">
                      <Button size="sm" onClick={confirmAvatarUpload} loading={uploadAvatarMutation.isPending}>
                        <Save className="mr-2 h-4 w-4" />
                        Save
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => { setAvatarPreview(null); const input = document.getElementById('avatar-upload') as HTMLInputElement; if (input) input.value = ''; }}>
                        Cancel
                      </Button>
                    </div>
                  )}
                </div>

                <div className="flex-1 space-y-4">
                  <form onSubmit={(e) => { e.preventDefault(); updateProfileMutation.mutate(new FormData(e.currentTarget) as any); }}>
                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="space-y-2">
                        <Label htmlFor="full_name">Full Name</Label>
                        <Input id="full_name" name="full_name" defaultValue={user.full_name || ''} placeholder="Enter your name" />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="email">Email</Label>
                        <Input id="email" name="email" type="email" defaultValue={user.email} disabled />
                        <p className="text-sm text-muted-foreground">Email cannot be changed here</p>
                      </div>
                      <div className="space-y-2 md:col-span-2">
                        <Label htmlFor="phone">Phone Number</Label>
                        <Input id="phone" name="phone" defaultValue={user.phone || ''} placeholder="Enter phone number" />
                      </div>
                      <div className="space-y-2 md:col-span-2">
                        <Label htmlFor="timezone">Timezone</Label>
                        <Select name="timezone" defaultValue={user.timezone || 'UTC'}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select timezone" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="UTC">UTC</SelectItem>
                            <SelectItem value="America/New_York">Eastern Time (US)</SelectItem>
                            <SelectItem value="America/Chicago">Central Time (US)</SelectItem>
                            <SelectItem value="America/Denver">Mountain Time (US)</SelectItem>
                            <SelectItem value="America/Los_Angeles">Pacific Time (US)</SelectItem>
                            <SelectItem value="Europe/London">London (GMT/BST)</SelectItem>
                            <SelectItem value="Europe/Paris">Paris (CET/CEST)</SelectItem>
                            <SelectItem value="Asia/Tokyo">Tokyo (JST)</SelectItem>
                            <SelectItem value="Asia/Singapore">Singapore (SGT)</SelectItem>
                            <SelectItem value="Australia/Sydney">Sydney (AEST/AEDT)</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2 md:col-span-2">
                        <Label htmlFor="language">Language</Label>
                        <Select name="language" defaultValue={user.language || 'en'}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select language" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="en">English</SelectItem>
                            <SelectItem value="es">Spanish</SelectItem>
                            <SelectItem value="fr">French</SelectItem>
                            <SelectItem value="de">German</SelectItem>
                            <SelectItem value="zh">Chinese</SelectItem>
                            <SelectItem value="ja">Japanese</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    <div className="flex justify-end gap-3 pt-4 border-t mt-6">
                      <Button type="submit" loading={updateProfileMutation.isPending}>
                        <Save className="mr-2 h-4 w-4" />
                        Save Changes
                      </Button>
                    </div>
                  </form>
                </div>
              </div>
            </CardContent>
          </Card>

          {companyProfile && (
            <Card>
              <CardHeader>
                <CardTitle>Company Information</CardTitle>
                <CardDescription>Your company profile details</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Company Name</p>
                    <p className="font-medium">{companyProfile.name}</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Registration Number</p>
                    <p className="font-medium">{companyProfile.registration_number || 'Not set'}</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Industry</p>
                    <p className="font-medium">{companyProfile.industry || 'Not set'}</p>
                  </div>
                </div>
                <div className="mt-4 flex justify-end">
                  <Button variant="outline" asChild>
                    <a href="/company-profile">
                      <Edit className="mr-2 h-4 w-4" />
                      Edit Company Profile
                    </a>
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Notifications Tab */}
        <TabsContent value="notifications" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Email Notifications</CardTitle>
              <CardDescription>Choose what email notifications you want to receive</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {[
                { id: 'tender_updates', label: 'Tender Updates', description: 'New tenders matching your interests' },
                { id: 'proposal_updates', label: 'Proposal Updates', description: 'Status changes on your proposals' },
                { id: 'deadline_reminders', label: 'Deadline Reminders', description: 'Upcoming tender and proposal deadlines' },
                { id: 'team_activity', label: 'Team Activity', description: 'Actions by team members on shared resources' },
                { id: 'weekly_digest', label: 'Weekly Digest', description: 'Summary of weekly activity and opportunities' },
                { id: 'marketing', label: 'Marketing Emails', description: 'Product updates, tips, and announcements' },
              ].map(item => (
                <div key={item.id} className="flex items-center justify-between py-3 border-b last:border-0">
                  <div>
                    <p className="font-medium">{item.label}</p>
                    <p className="text-sm text-muted-foreground">{item.description}</p>
                  </div>
                  <Switch checked={true} onCheckedChange={() => {}} />
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>In-App Notifications</CardTitle>
              <CardDescription>Configure real-time notifications within the app</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {[
                { id: 'mentions', label: 'Mentions', description: 'When someone mentions you in comments' },
                { id: 'comments', label: 'Comments', description: 'New comments on your proposals or tenders' },
                { id: 'assignments', label: 'Assignments', description: 'When tasks are assigned to you' },
                { id: 'approvals', label: 'Approvals', description: 'When your approval is needed' },
              ].map(item => (
                <div key={item.id} className="flex items-center justify-between py-3 border-b last:border-0">
                  <div>
                    <p className="font-medium">{item.label}</p>
                    <p className="text-sm text-muted-foreground">{item.description}</p>
                  </div>
                  <Switch checked={true} onCheckedChange={() => {}} />
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Security Tab */}
        <TabsContent value="security" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Two-Factor Authentication</CardTitle>
              <CardDescription>Add an extra layer of security to your account</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-primary/10 rounded-lg">
                    <Shield className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium">Authenticator App</p>
                    <p className="text-sm text-muted-foreground">Use Google Authenticator, Authy, or similar</p>
                  </div>
                </div>
                <Button variant="outline">Enable 2FA</Button>
              </div>
              <div className="p-4 bg-muted/50 rounded-lg">
                <p className="text-sm text-muted-foreground">
                  <strong>Recovery Codes:</strong> Store these in a safe place. They can be used to access your account if you lose your authenticator device.
                </p>
                <Button variant="ghost" size="sm" className="mt-2">View Recovery Codes</Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Change Password</CardTitle>
              <CardDescription>Update your password regularly for security</CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" onClick={() => setShowPasswordDialog(true)}>
                <Lock className="mr-2 h-4 w-4" />
                Change Password
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Active Sessions</CardTitle>
              <CardDescription>Manage your active login sessions</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Monitor className="h-5 w-5 text-primary" />
                  <div>
                    <p className="font-medium">Current Session</p>
                    <p className="text-sm text-muted-foreground">Chrome on Windows • Active now</p>
                  </div>
                </div>
                <Badge variant="success">Current</Badge>
              </div>
              <div className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center gap-3">
                  <Monitor className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="font-medium">Mobile App</p>
                    <p className="text-sm text-muted-foreground">iOS • Last active 2 hours ago</p>
                  </div>
                </div>
                <Button variant="ghost" size="icon" className="text-destructive">
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
              <Button variant="ghost" size="sm" className="w-full text-destructive">
                <RotateCcw className="mr-2 h-4 w-4" />
                Log Out of All Other Sessions
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>API Keys</CardTitle>
              <CardDescription>Manage API keys for integrations</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center gap-3">
                  <Key className="h-5 w-5 text-primary" />
                  <div>
                    <p className="font-medium">Production API Key</p>
                    <p className="text-sm text-muted-foreground font-mono">tk_live_••••••••••••••••</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="ghost" size="icon"><Copy className="h-4 w-4" /></Button>
                  <Button variant="ghost" size="icon" className="text-destructive"><Trash2 className="h-4 w-4" /></Button>
                </div>
              </div>
              <Button variant="outline" size="sm">
                <Plus className="mr-2 h-4 w-4" />
                Generate New API Key
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Appearance Tab */}
        <TabsContent value="appearance" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Theme</CardTitle>
              <CardDescription>Choose your preferred color theme</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-3">
                {[
                  { value: 'light', label: 'Light', icon: Sun, description: 'Always use light mode' },
                  { value: 'dark', label: 'Dark', icon: Moon, description: 'Always use dark mode' },
                  { value: 'system', label: 'System', icon: Monitor, description: 'Match your system setting' },
                ].map(theme => (
                  <Button
                    key={theme.value}
                    variant="outline"
                    className="h-24 flex-col items-start text-left gap-3 p-4"
                    onClick={() => {}}
                  >
                    <theme.icon className="h-8 w-8" />
                    <div>
                      <p className="font-medium">{theme.label}</p>
                      <p className="text-sm text-muted-foreground">{theme.description}</p>
                    </div>
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Density</CardTitle>
              <CardDescription>Adjust the spacing and density of the interface</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-3">
                {[
                  { value: 'comfortable', label: 'Comfortable', description: 'More spacing, easier to read' },
                  { value: 'compact', label: 'Compact', description: 'More content on screen' },
                  { value: 'cozy', label: 'Cozy', description: 'Balanced spacing' },
                ].map(density => (
                  <Button
                    key={density.value}
                    variant="outline"
                    className="h-24 flex-col items-start text-left gap-3 p-4"
                    onClick={() => {}}
                  >
                    <div className="w-full h-8 bg-muted rounded" />
                    <div>
                      <p className="font-medium">{density.label}</p>
                      <p className="text-sm text-muted-foreground">{density.description}</p>
                    </div>
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Sidebar</CardTitle>
              <CardDescription>Configure sidebar behavior</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Collapse Sidebar</p>
                  <p className="text-sm text-muted-foreground">Automatically collapse sidebar on small screens</p>
                </div>
                <Switch checked={true} onCheckedChange={() => {}} />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Show Tooltips</p>
                  <p className="text-sm text-muted-foreground">Show tooltip labels when sidebar is collapsed</p>
                </div>
                <Switch checked={true} onCheckedChange={() => {}} />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Danger Zone Tab */}
        <TabsContent value="danger" className="space-y-6">
          <Card className="border-destructive/50">
            <CardHeader>
              <CardTitle className="text-destructive flex items-center gap-2">
                <AlertCircle className="h-5 w-5" />
                Danger Zone
              </CardTitle>
              <CardDescription>Irreversible and destructive actions</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="p-4 border border-destructive/20 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-destructive">Delete Account</p>
                    <p className="text-sm text-muted-foreground">Permanently delete your account and all associated data. This action cannot be undone.</p>
                  </div>
                  <Button variant="destructive" onClick={() => setShowDeleteAccountDialog(true)}>
                    <Trash2 className="mr-2 h-4 w-4" />
                    Delete Account
                  </Button>
                </div>
              </div>

              <div className="p-4 border border-destructive/20 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-destructive">Export Data</p>
                    <p className="text-sm text-muted-foreground">Download all your data in JSON format</p>
                  </div>
                  <Button variant="outline" className="border-destructive/50 text-destructive hover:bg-destructive/10">
                    <Download className="mr-2 h-4 w-4" />
                    Export Data
                  </Button>
                </div>
              </div>

              <div className="p-4 border border-destructive/20 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-destructive">Revoke All Sessions</p>
                    <p className="text-sm text-muted-foreground">Log out of all devices and invalidate all tokens</p>
                  </div>
                  <Button variant="outline" className="border-destructive/50 text-destructive hover:bg-destructive/10">
                    <RotateCcw className="mr-2 h-4 w-4" />
                    Revoke All Sessions
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Password Change Dialog */}
      <Dialog open={showPasswordDialog} onOpenChange={setShowPasswordDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Change Password</DialogTitle>
            <DialogDescription>Enter your current password and a new password</DialogDescription>
          </DialogHeader>
          <form onSubmit={handlePasswordSubmit}>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="current_password">Current Password</Label>
                <Input id="current_password" type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="new_password">New Password</Label>
                <Input id="new_password" type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required minLength={8} />
                <p className="text-sm text-muted-foreground">Must be at least 8 characters</p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirm_password">Confirm New Password</Label>
                <Input id="confirm_password" type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowPasswordDialog(false)}>Cancel</Button>
              <Button type="submit" loading={updatePasswordMutation.isPending}>
                <Save className="mr-2 h-4 w-4" />
                Update Password
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Account Dialog */}
      <Dialog open={showDeleteAccountDialog} onOpenChange={setShowDeleteAccountDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="text-destructive">Delete Account</DialogTitle>
            <DialogDescription>
              This action is irreversible. All your data, including tenders, proposals, chat history, and team memberships will be permanently deleted.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Please type <code className="bg-muted px-1.5 py-0.5 rounded">DELETE</code> to confirm.
            </p>
            <Input
              value={deleteConfirmText}
              onChange={(e) => setDeleteConfirmText(e.target.value)}
              placeholder="Type DELETE to confirm"
              className="font-mono"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowDeleteAccountDialog(false); setDeleteConfirmText(''); }}>Cancel</Button>
            <Button variant="destructive" onClick={handleDeleteAccount} disabled={deleteConfirmText !== 'DELETE'} loading={deleteAccountMutation.isPending}>
              <Trash2 className="mr-2 h-4 w-4" />
              Delete Account Permanently
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}