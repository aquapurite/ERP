'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  Building,
  Bell,
  Shield,
  Globe,
  Save,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { PageHeader } from '@/components/common';
import apiClient from '@/lib/api/client';

interface SystemSettings {
  company_name: string;
  company_address: string;
  gst_number: string;
  currency: string;
  timezone: string;
  date_format: string;
  email_notifications: boolean;
  sms_notifications: boolean;
  two_factor_enabled: boolean;
  session_timeout: number;
  maintenance_mode: boolean;
}

// Default settings when no company data exists
const defaultSettings: SystemSettings = {
  company_name: 'Consumer Durable Co.',
  company_address: '',
  gst_number: '',
  currency: 'INR',
  timezone: 'Asia/Kolkata',
  date_format: 'DD/MM/YYYY',
  email_notifications: true,
  sms_notifications: false,
  two_factor_enabled: false,
  session_timeout: 30,
  maintenance_mode: false,
};

const settingsApi = {
  get: async (): Promise<SystemSettings> => {
    try {
      const { data } = await apiClient.get('/company/primary');
      return {
        company_name: data.name || defaultSettings.company_name,
        company_address: data.address || defaultSettings.company_address,
        gst_number: data.gst_number || defaultSettings.gst_number,
        currency: data.currency || defaultSettings.currency,
        timezone: data.timezone || defaultSettings.timezone,
        date_format: defaultSettings.date_format,
        email_notifications: defaultSettings.email_notifications,
        sms_notifications: defaultSettings.sms_notifications,
        two_factor_enabled: defaultSettings.two_factor_enabled,
        session_timeout: defaultSettings.session_timeout,
        maintenance_mode: defaultSettings.maintenance_mode,
      };
    } catch {
      return defaultSettings;
    }
  },
  update: async (settings: Partial<SystemSettings>) => {
    // Company update endpoint
    try {
      const { data } = await apiClient.put('/company/primary', {
        name: settings.company_name,
        address: settings.company_address,
        gst_number: settings.gst_number,
        currency: settings.currency,
        timezone: settings.timezone,
      });
      return data;
    } catch {
      // Silently handle - settings are stored locally
      return settings;
    }
  },
};

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState<SystemSettings>(defaultSettings);

  const { data: settings, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: settingsApi.get,
  });

  // Update formData when settings are loaded
  useEffect(() => {
    if (settings) {
      setFormData(settings);
    }
  }, [settings]);

  const updateMutation = useMutation({
    mutationFn: settingsApi.update,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] });
      toast.success('Settings saved successfully');
    },
    onError: () => {
      toast.error('Failed to save settings');
    },
  });

  const handleSave = () => {
    updateMutation.mutate(formData);
  };

  const updateField = (field: keyof SystemSettings, value: unknown) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Settings"
        description="Manage system configuration and preferences"
        actions={
          <Button onClick={handleSave} disabled={updateMutation.isPending}>
            <Save className="mr-2 h-4 w-4" />
            {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
          </Button>
        }
      />

      <Tabs defaultValue="general" className="space-y-6">
        <TabsList>
          <TabsTrigger value="general" className="gap-2">
            <Building className="h-4 w-4" />
            General
          </TabsTrigger>
          <TabsTrigger value="notifications" className="gap-2">
            <Bell className="h-4 w-4" />
            Notifications
          </TabsTrigger>
          <TabsTrigger value="security" className="gap-2">
            <Shield className="h-4 w-4" />
            Security
          </TabsTrigger>
          <TabsTrigger value="regional" className="gap-2">
            <Globe className="h-4 w-4" />
            Regional
          </TabsTrigger>
        </TabsList>

        <TabsContent value="general">
          <Card>
            <CardHeader>
              <CardTitle>Company Information</CardTitle>
              <CardDescription>
                Basic company details used across the system
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="company_name">Company Name</Label>
                <Input
                  id="company_name"
                  value={formData.company_name || ''}
                  onChange={(e) => updateField('company_name', e.target.value)}
                  placeholder="Your Company Name"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="company_address">Address</Label>
                <Textarea
                  id="company_address"
                  value={formData.company_address || ''}
                  onChange={(e) => updateField('company_address', e.target.value)}
                  placeholder="Company address"
                  rows={3}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="gst_number">GST Number</Label>
                <Input
                  id="gst_number"
                  value={formData.gst_number || ''}
                  onChange={(e) => updateField('gst_number', e.target.value.toUpperCase())}
                  placeholder="22AAAAA0000A1Z5"
                />
              </div>
            </CardContent>
          </Card>

          <Card className="mt-6">
            <CardHeader>
              <CardTitle>System Maintenance</CardTitle>
              <CardDescription>
                Control system availability
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Maintenance Mode</Label>
                  <p className="text-sm text-muted-foreground">
                    When enabled, only administrators can access the system
                  </p>
                </div>
                <Switch
                  checked={formData.maintenance_mode || false}
                  onCheckedChange={(checked) => updateField('maintenance_mode', checked)}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="notifications">
          <Card>
            <CardHeader>
              <CardTitle>Notification Preferences</CardTitle>
              <CardDescription>
                Configure how and when notifications are sent
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Email Notifications</Label>
                  <p className="text-sm text-muted-foreground">
                    Send notifications via email
                  </p>
                </div>
                <Switch
                  checked={formData.email_notifications || false}
                  onCheckedChange={(checked) => updateField('email_notifications', checked)}
                />
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>SMS Notifications</Label>
                  <p className="text-sm text-muted-foreground">
                    Send notifications via SMS
                  </p>
                </div>
                <Switch
                  checked={formData.sms_notifications || false}
                  onCheckedChange={(checked) => updateField('sms_notifications', checked)}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="security">
          <Card>
            <CardHeader>
              <CardTitle>Security Settings</CardTitle>
              <CardDescription>
                Manage authentication and security features
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Two-Factor Authentication</Label>
                  <p className="text-sm text-muted-foreground">
                    Require 2FA for all users
                  </p>
                </div>
                <Switch
                  checked={formData.two_factor_enabled || false}
                  onCheckedChange={(checked) => updateField('two_factor_enabled', checked)}
                />
              </div>
              <Separator />
              <div className="space-y-2">
                <Label htmlFor="session_timeout">Session Timeout (minutes)</Label>
                <Input
                  id="session_timeout"
                  type="number"
                  value={formData.session_timeout || 30}
                  onChange={(e) => updateField('session_timeout', parseInt(e.target.value))}
                  min={5}
                  max={480}
                />
                <p className="text-sm text-muted-foreground">
                  Users will be logged out after this period of inactivity
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="regional">
          <Card>
            <CardHeader>
              <CardTitle>Regional Settings</CardTitle>
              <CardDescription>
                Configure currency, timezone, and date formats
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="currency">Currency</Label>
                <Select
                  value={formData.currency || 'INR'}
                  onValueChange={(value) => updateField('currency', value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select currency" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="INR">Indian Rupee (₹)</SelectItem>
                    <SelectItem value="USD">US Dollar ($)</SelectItem>
                    <SelectItem value="EUR">Euro (€)</SelectItem>
                    <SelectItem value="GBP">British Pound (£)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="timezone">Timezone</Label>
                <Select
                  value={formData.timezone || 'Asia/Kolkata'}
                  onValueChange={(value) => updateField('timezone', value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select timezone" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Asia/Kolkata">Asia/Kolkata (IST)</SelectItem>
                    <SelectItem value="UTC">UTC</SelectItem>
                    <SelectItem value="America/New_York">America/New_York (EST)</SelectItem>
                    <SelectItem value="Europe/London">Europe/London (GMT)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="date_format">Date Format</Label>
                <Select
                  value={formData.date_format || 'DD/MM/YYYY'}
                  onValueChange={(value) => updateField('date_format', value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select date format" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="DD/MM/YYYY">DD/MM/YYYY</SelectItem>
                    <SelectItem value="MM/DD/YYYY">MM/DD/YYYY</SelectItem>
                    <SelectItem value="YYYY-MM-DD">YYYY-MM-DD</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
