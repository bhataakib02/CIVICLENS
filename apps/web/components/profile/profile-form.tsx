'use client';

import React, { useState } from 'react';
import { useAuth } from '@/lib/auth/auth-context';
import { updateProfile } from '@/lib/api/me';
import { useTranslation } from '@/lib/i18n';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Alert } from '@/components/ui/alert';
import { formatCurrency } from '@/lib/formatting/currency';
import { UserCheck, ShieldAlert, Save } from 'lucide-react';

export function ProfileForm() {
  const { user, refreshProfile } = useAuth();
  const { t } = useTranslation();

  const [dateOfBirth, setDateOfBirth] = useState(user?.date_of_birth || '');
  const [gender, setGender] = useState(user?.gender || '');
  const [category, setCategory] = useState(user?.category || '');
  const [occupation, setOccupation] = useState(user?.occupation || '');
  const [income, setIncome] = useState(user?.declared_annual_income?.toString() || '');
  const [disability, setDisability] = useState(user?.disability_status ? 'true' : 'false');
  const [familySize, setFamilySize] = useState(user?.family_size?.toString() || '');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      await updateProfile({
        date_of_birth: dateOfBirth || null,
        gender: gender || null,
        category: category || null,
        occupation: occupation || null,
        declared_annual_income: income ? parseFloat(income) : null,
        disability_status: disability === 'true',
        family_size: familySize ? parseInt(familySize, 10) : null
      });

      await refreshProfile();
      setSuccess('Profile updated successfully! Scheme eligibility has been re-evaluated.');
    } catch (err: any) {
      setError(err.message || 'Failed to update profile.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const completenessPct = Math.round((user?.profile_completeness || 0) * 100);

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900">{t.profile.title}</h1>
        <p className="text-sm text-slate-500 mt-1">{t.profile.subtitle}</p>
      </div>

      {/* Progressive Profile Completeness Bar */}
      <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-bold text-blue-900">{t.dashboard.profileCompleteness}</span>
          <span className="text-sm font-extrabold text-blue-700">{completenessPct}%</span>
        </div>
        <div className="w-full bg-blue-200 h-2.5 rounded-full overflow-hidden">
          <div
            className="bg-blue-600 h-full transition-all duration-500 rounded-full"
            style={{ width: `${completenessPct}%` }}
          />
        </div>
      </Card>

      {/* Notice about Eligibility Recomputation */}
      <Alert type="warning">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-amber-700 flex-shrink-0" />
          <span>{t.profile.profileUpdatedNotice}</span>
        </div>
      </Alert>

      {error && <Alert type="error">{error}</Alert>}
      {success && <Alert type="success">{success}</Alert>}

      <Card>
        <CardHeader>
          <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
            <UserCheck className="w-5 h-5 text-blue-600" />
            Personal & Financial Attributes
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label={t.profile.dob}
                type="date"
                value={dateOfBirth}
                onChange={(e) => setDateOfBirth(e.target.value)}
              />

              <Select
                label={t.profile.gender}
                value={gender}
                onChange={(e) => setGender(e.target.value)}
                options={[
                  { value: '', label: 'Select Gender' },
                  { value: 'female', label: 'Female' },
                  { value: 'male', label: 'Male' },
                  { value: 'other', label: 'Other' }
                ]}
              />

              <Select
                label={t.profile.category}
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                options={[
                  { value: '', label: 'Select Category' },
                  { value: 'general', label: 'General' },
                  { value: 'obc', label: 'OBC (Other Backward Class)' },
                  { value: 'sc', label: 'SC (Scheduled Caste)' },
                  { value: 'st', label: 'ST (Scheduled Tribe)' },
                  { value: 'ews', label: 'EWS (Economically Weaker Section)' }
                ]}
              />

              <Input
                label={t.profile.occupation}
                type="text"
                placeholder="e.g. Farmer / Student / Self-Employed"
                value={occupation}
                onChange={(e) => setOccupation(e.target.value)}
              />

              <Input
                label={t.profile.income}
                type="number"
                placeholder="e.g. 180000"
                value={income}
                onChange={(e) => setIncome(e.target.value)}
                helperText={income ? `Formatted: ${formatCurrency(parseFloat(income))}` : ''}
              />

              <Select
                label={t.profile.disability}
                value={disability}
                onChange={(e) => setDisability(e.target.value)}
                options={[
                  { value: 'false', label: 'No' },
                  { value: 'true', label: 'Yes' }
                ]}
              />

              <Input
                label={t.profile.familySize}
                type="number"
                placeholder="e.g. 4"
                value={familySize}
                onChange={(e) => setFamilySize(e.target.value)}
              />
            </div>

            <div className="pt-4 border-t border-slate-100 flex justify-end">
              <Button type="submit" isLoading={isSubmitting}>
                <Save className="w-4 h-4 mr-2" />
                {t.common.save}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
