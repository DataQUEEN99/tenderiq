'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Building2,
  User,
  Mail,
  Phone,
  MapPin,
  Globe,
  FileText,
  Save,
  Loader2,
  AlertCircle,
  CheckCircle,
  Edit2,
  X,
  Camera,
  Upload,
  Eye,
  EyeOff,
} from 'lucide-react';
import { apiClient } from '../api/client';
import type { CompanyProfile, User as UserType } from '../types';
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
  Textarea,
} from '../components/ui/textarea';
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
import { cn } from '../utils/cn';
import { Skeleton } from '../components/ui/skeleton';
import { Alert, AlertTitle, AlertDescription } from '../components/ui/alert';

const PLACEHOLDER_LOGO = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTI4IiBoZWlnaHQ9IjEyOCIgdmlld0JveD0iMCAwIDEyOCAxMjgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIxMjgiIGhlaWdodD0iMTI4IiByeD0iMTYiIGZpbGw9IiNFNUU3ZWIiLz4KPHBhdGggZD0iTTY0IDQwQzU1LjcxNTcgNDAgNDggNDcuNzE1NyA0OCA1NlM1NS43MTU3IDcyIDY0IDcyUzc2IDY0LjI4NDMgNzYgNTZTNzAuMjg0MyA0MCA2NCA0MFoiIHN0cm9rZT0iIzk0QTNDNyIgc3Ryb2tlLXdpZHRoPSIyIi8+CjxwYXRoIGQ9Ik02NCA3NkM1NS43MTU3IDc2IDQ4IDY4LjI4NDMgNDggNjBTNTUuNzE1NyA0NCA2NCA0NEM3Mi4yODQzIDQ0IDgwIDUxLjcxNTcgODAgNjBTNzIuMjg0MyA3NiA2NCA3NloiIHN0cm9rZT0iIzk0QTNDNyIgc3Ryb2tlLXdpZHRoPSIyIi8+Cjwvc3ZnPgo=';

export function CompanyProfilePage() {
  const queryClient = useQueryClient();
  const [logoPreview, setLogoPreview] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);

  const { data: profile, isLoading: profileLoading, error: profileError } = useQuery({
    queryKey: ['company-profile'],
    queryFn: () => apiClient.getCompanyProfile(),
  });

  const { data: currentUser } = useQuery({
    queryKey: ['current-user'],
    queryFn: () => apiClient.getCurrentUser(),
  });

  const updateProfileMutation = useMutation({
    mutationFn: (data: Partial<CompanyProfile>) => apiClient.updateCompanyProfile(data),
    onSuccess: (updatedProfile) => {
      queryClient.setQueryData(['company-profile'], updatedProfile);
      queryClient.invalidateQueries({ queryKey: ['company-profile'] });
    },
  });

  const uploadLogoMutation = useMutation({
    mutationFn: (file: File) => apiClient.uploadCompanyLogo(file),
    onSuccess: (response) => {
      queryClient.setQueryData(['company-profile'], (old: CompanyProfile | undefined) =>
        old ? { ...old, logo_url: response.url } : undefined
      );
      queryClient.invalidateQueries({ queryKey: ['company-profile'] });
      setLogoPreview(null);
    },
  });

  const handleLogoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.type.startsWith('image/')) {
        alert('Please select an image file');
        return;
      }
      if (file.size > 5 * 1024 * 1024) {
        alert('Image size must be less than 5MB');
        return;
      }
      const reader = new FileReader();
      reader.onload = (event) => {
        setLogoPreview(event.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleLogoUpload = () => {
    const input = document.getElementById('logo-upload') as HTMLInputElement;
    input?.click();
  };

  const confirmLogoUpload = () => {
    const input = document.getElementById('logo-upload') as HTMLInputElement;
    if (input?.files?.[0]) {
      uploadLogoMutation.mutate(input.files[0]);
    }
  };

  const removeLogo = () => {
    setLogoPreview(null);
    const input = document.getElementById('logo-upload') as HTMLInputElement;
    if (input) input.value = '';
    updateProfileMutation.mutate({ logo_url: null });
  };

  if (profileLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-4 w-64" />
          </div>
        </div>
        <Card><CardContent className="py-8"><Skeleton className="h-64 w-full" /></CardContent></Card>
      </div>
    );
  }

  if (profileError || !profile) {
    return (
      <Alert variant="destructive" className="mb-6">
        <AlertTitle>Unable to load profile</AlertTitle>
        <AlertDescription>Please try refreshing the page or contact support.</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Company Profile</h1>
          <p className="text-muted-foreground">Manage your company information and settings</p>
        </div>
      </div>

      {/* Profile Card */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-8">
            {/* Logo Section */}
            <div className="flex flex-col items-center md:w-64 md:shrink-0">
              <div className="relative w-32 h-32 rounded-xl overflow-hidden bg-muted border-2 border-dashed">
                {logoPreview ? (
                  <img
                    src={logoPreview}
                    alt="Logo preview"
                    className="w-full h-full object-cover"
                  />
                ) : profile.logo_url ? (
                  <img
                    src={profile.logo_url}
                    alt="Company logo"
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <Building2 className="h-12 w-12 text-muted-foreground/50" />
                  </div>
                )}
              </div>
              <div className="flex gap-2 mt-4">
                <Button variant="outline" size="sm" onClick={handleLogoUpload}>
                  <Upload className="mr-2 h-4 w-4" />
                  Change
                </Button>
                {(logoPreview || profile.logo_url) && (
                  <Button variant="ghost" size="sm" onClick={removeLogo} className="text-destructive">
                    <X className="mr-2 h-4 w-4" />
                    Remove
                  </Button>
                )}
              </div>
              <input
                id="logo-upload"
                type="file"
                accept="image/*"
                onChange={handleLogoChange}
                className="hidden"
              />
              {logoPreview && (
                <div className="flex gap-2 mt-2">
                  <Button size="sm" onClick={confirmLogoUpload} loading={uploadLogoMutation.isPending}>
                    <Save className="mr-2 h-4 w-4" />
                    Save
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => { setLogoPreview(null); const input = document.getElementById('logo-upload') as HTMLInputElement; if (input) input.value = ''; }}>
                    Cancel
                  </Button>
                </div>
              )}
            </div>

            {/* Form Section */}
            <div className="flex-1 space-y-6">
              <form onSubmit={(e) => {
                e.preventDefault();
                const formData = new FormData(e.currentTarget);
                const data = Object.fromEntries(formData.entries());
                updateProfileMutation.mutate(data as any);
              }}>
                <Tabs defaultValue="company" className="w-full">
                  <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger value="company">Company Info</TabsTrigger>
                    <TabsTrigger value="address">Address</TabsTrigger>
                    <TabsTrigger value="settings">Settings</TabsTrigger>
                  </TabsList>

                  <TabsContent value="company" className="space-y-4 mt-4">
                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="space-y-2">
                        <Label htmlFor="name">Company Name *</Label>
                        <Input
                          id="name"
                          name="name"
                          defaultValue={(profile as any)?.name || profile?.company_name || ''}
                          placeholder="Enter company name"
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="registration_number">Registration Number</Label>
                        <Input
                          id="registration_number"
                          name="registration_number"
                          defaultValue={profile.registration_number || ''}
                          placeholder="Enter registration number"
                        />
                      </div>
                      <div className="space-y-2 md:col-span-2">
                        <Label htmlFor="description">Description</Label>
                        <Textarea
                          id="description"
                          name="description"
                          defaultValue={profile.description || ''}
                          placeholder="Describe your company..."
                          rows={3}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="website">Website</Label>
                        <Input
                          id="website"
                          name="website"
                          type="url"
                          defaultValue={profile.website || ''}
                          placeholder="https://example.com"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="industry">Industry</Label>
                        <Input
                          id="industry"
                          name="industry"
                          defaultValue={profile.industry || ''}
                          placeholder="Enter industry"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="size">Company Size</Label>
                        <Input
                          id="size"
                          name="size"
                          defaultValue={profile.size || ''}
                          placeholder="e.g., 1-10, 11-50, 51-200"
                        />
                      </div>
                    </div>
                  </TabsContent>

                  <TabsContent value="address" className="space-y-4 mt-4">
                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="space-y-2 md:col-span-2">
                        <Label htmlFor="address_line1">Address Line 1 *</Label>
                        <Input
                          id="address_line1"
                          name="address_line1"
                          defaultValue={profile.address_line1 || ''}
                          placeholder="Street address"
                          required
                        />
                      </div>
                      <div className="space-y-2 md:col-span-2">
                        <Label htmlFor="address_line2">Address Line 2</Label>
                        <Input
                          id="address_line2"
                          name="address_line2"
                          defaultValue={profile.address_line2 || ''}
                          placeholder="Apartment, suite, etc."
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="city">City *</Label>
                        <Input
                          id="city"
                          name="city"
                          defaultValue={profile.city || ''}
                          placeholder="City"
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="state">State/Province *</Label>
                        <Input
                          id="state"
                          name="state"
                          defaultValue={profile.state || ''}
                          placeholder="State/Province"
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="postal_code">Postal Code *</Label>
                        <Input
                          id="postal_code"
                          name="postal_code"
                          defaultValue={profile.postal_code || ''}
                          placeholder="Postal code"
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="country">Country *</Label>
                        <Input
                          id="country"
                          name="country"
                          defaultValue={profile.country || ''}
                          placeholder="Country"
                          required
                        />
                      </div>
                    </div>
                  </TabsContent>

                  <TabsContent value="settings" className="space-y-4 mt-4">
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium">Two-Factor Authentication</h4>
                          <p className="text-sm text-muted-foreground">Add an extra layer of security to your account</p>
                        </div>
                        <Button variant="outline" size="sm">Enable 2FA</Button>
                      </div>
                      <Separator />
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium">Email Notifications</h4>
                          <p className="text-sm text-muted-foreground">Receive updates about tenders and proposals</p>
                        </div>
                        <Button variant="outline" size="sm">Configure</Button>
                      </div>
                      <Separator />
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium">API Access</h4>
                          <p className="text-sm text-muted-foreground">Manage API keys for integrations</p>
                        </div>
                        <Button variant="outline" size="sm">Manage Keys</Button>
                      </div>
                    </div>
                  </TabsContent>
                </Tabs>

                <div className="flex justify-end gap-3 pt-4 border-t mt-6">
                  <Button type="button" variant="outline" onClick={() => queryClient.invalidateQueries({ queryKey: ['company-profile'] })}>
                    Cancel
                  </Button>
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

      {/* Team Members */}
      <Card>
        <CardHeader>
          <CardTitle>Team Members</CardTitle>
          <CardDescription>Manage team members and their roles</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b text-left text-sm text-muted-foreground">
                  <th className="pb-3 font-medium">Member</th>
                  <th className="pb-3 font-medium">Role</th>
                  <th className="pb-3 font-medium">Status</th>
                  <th className="pb-3 font-medium">Joined</th>
                  <th className="pb-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {currentUser && (
                  <tr className="hover:bg-muted/50">
                    <td className="py-3">
                      <div className="flex items-center gap-3">
                        <Avatar className="h-8 w-8">
                          <AvatarFallback>{currentUser.email.charAt(0).toUpperCase()}</AvatarFallback>
                        </Avatar>
                        <div>
                          <p className="font-medium">{currentUser.full_name || currentUser.email}</p>
                          <p className="text-sm text-muted-foreground">{currentUser.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="py-3">
                      <Badge variant="default">{currentUser.role}</Badge>
                    </td>
                    <td className="py-3">
                      <Badge variant={currentUser.is_active ? 'success' : 'secondary'}>
                        {currentUser.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </td>
                    <td className="py-3 text-sm text-muted-foreground">
                      {currentUser?.created_at ? format(new Date(currentUser.created_at), 'MMM d, yyyy') : '—'}
                    </td>
                    <td className="py-3">
                      <Button variant="ghost" size="icon">
                        <Edit2 className="h-4 w-4" />
                      </Button>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <div className="mt-4 flex justify-end">
            <Button variant="outline" asChild>
              <a href="/settings/team/invite">
                <User className="mr-2 h-4 w-4" />
                Invite Team Member
              </a>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Subscription Info */}
      <Card>
        <CardHeader>
          <CardTitle>Subscription</CardTitle>
          <CardDescription>Current plan and usage</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="p-4 border rounded-lg">
              <p className="text-sm text-muted-foreground">Current Plan</p>
              <p className="text-2xl font-bold">Professional</p>
              <Badge variant="success">Active</Badge>
            </div>
            <div className="p-4 border rounded-lg">
              <p className="text-sm text-muted-foreground">Tenders This Month</p>
              <p className="text-2xl font-bold">12 / 50</p>
              <div className="w-full h-2 bg-muted rounded-full mt-2 overflow-hidden">
                <div className="h-full bg-primary rounded-full" style={{ width: '24%' }} />
              </div>
            </div>
            <div className="p-4 border rounded-lg">
              <p className="text-sm text-muted-foreground">Proposals This Month</p>
              <p className="text-2xl font-bold">8 / 30</p>
              <div className="w-full h-2 bg-muted rounded-full mt-2 overflow-hidden">
                <div className="h-full bg-primary rounded-full" style={{ width: '27%' }} />
              </div>
            </div>
          </div>
          <div className="mt-4">
            <Button variant="outline">Upgrade Plan</Button>
            <Button variant="ghost" className="ml-2">View Billing</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}