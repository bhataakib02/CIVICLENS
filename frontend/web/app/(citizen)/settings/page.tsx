'use client';

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { LanguageSwitcher } from '@/components/layout/language-switcher';
import { Settings as SettingsIcon, Bell } from 'lucide-react';

export default function SettingsPage() {
  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900">Settings</h1>
        <p className="text-sm text-slate-500 mt-1">Manage application preferences and security settings.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
            <SettingsIcon className="w-5 h-5 text-blue-600" />
            Language & Interface
          </CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-between">
          <div>
            <h4 className="font-semibold text-sm text-slate-900">Preferred Language</h4>
            <p className="text-xs text-slate-500">Select language for navigation, scheme details, and AI responses.</p>
          </div>
          <LanguageSwitcher />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Bell className="w-5 h-5 text-blue-600" />
            Notification Preferences
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-xs text-slate-700">
          <label className="flex items-center justify-between p-3 bg-slate-50 rounded-xl border border-slate-200">
            <span>SMS Notifications for Application Status Changes</span>
            <input type="checkbox" defaultChecked className="w-4 h-4 text-blue-600 rounded" />
          </label>
          <label className="flex items-center justify-between p-3 bg-slate-50 rounded-xl border border-slate-200">
            <span>In-App Notifications for New Scheme Matches</span>
            <input type="checkbox" defaultChecked className="w-4 h-4 text-blue-600 rounded" />
          </label>
        </CardContent>
      </Card>
    </div>
  );
}
