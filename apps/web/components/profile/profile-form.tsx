'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth/auth-context';
import { updateProfile, getAddresses, addAddress, updateAddress } from '@/lib/api/me';
import { useTranslation } from '@/lib/i18n';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Alert } from '@/components/ui/alert';
import { formatCurrency } from '@/lib/formatting/currency';
import { StateDistrictSelector } from '@/components/ui/state-district-selector';
import {
  UserCheck,
  ShieldAlert,
  Save,
  MapPin,
  GraduationCap,
  Phone,
  Camera,
  CheckCircle2,
  Building2
} from 'lucide-react';

const AVATARS = [
  'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80',
  'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80',
  'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150&auto=format&fit=crop&q=80',
  'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&auto=format&fit=crop&q=80',
  'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150&auto=format&fit=crop&q=80'
];

const INDIAN_STATES = [
  'West Bengal', 'Bihar', 'Maharashtra', 'Uttar Pradesh', 'Delhi',
  'Karnataka', 'Tamil Nadu', 'Kerala', 'Gujarat', 'Rajasthan',
  'Punjab', 'Haryana', 'Madhya Pradesh', 'Odisha', 'Assam',
  'Telangana', 'Andhra Pradesh', 'Jharkhand', 'Chhattisgarh'
];

export function ProfileForm() {
  const { user, refreshProfile } = useAuth();
  const { t } = useTranslation();

  // Basic Profile Attributes
  const [dateOfBirth, setDateOfBirth] = useState(user?.date_of_birth || '');
  const [gender, setGender] = useState(user?.gender || '');
  const [category, setCategory] = useState(user?.category || '');
  const [occupation, setOccupation] = useState(user?.occupation || '');
  const [income, setIncome] = useState(user?.declared_annual_income?.toString() || '');
  const [disability, setDisability] = useState(user?.disability_status ? 'true' : 'false');
  const [familySize, setFamilySize] = useState(user?.family_size?.toString() || '');

  // Extended Attributes (Mobile, Qualification, Avatar)
  const [mobileNumber, setMobileNumber] = useState(user?.phone_number || '9876543210');
  const [qualification, setQualification] = useState(user?.education_level || 'UNDERGRADUATE');
  const [selectedAvatar, setSelectedAvatar] = useState(AVATARS[0]);

  // Complete Address State
  const [addressId, setAddressId] = useState<string | null>(null);
  const [line1, setLine1] = useState('1 Demo Road, Colony Street');
  const [line2, setLine2] = useState('Near Central Market');
  const [district, setDistrict] = useState('Demo District');
  const [stateName, setStateName] = useState('West Bengal');
  const [pincode, setPincode] = useState('700001');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Resync form fields whenever the user object is updated (e.g. after refreshProfile())
  useEffect(() => {
    if (!user) return;
    setDateOfBirth(user.date_of_birth || '');
    setGender(user.gender || '');
    setCategory(user.category || '');
    setOccupation(user.occupation || '');
    setIncome(user.declared_annual_income?.toString() || '');
    setDisability(user.disability_status ? 'true' : 'false');
    setFamilySize(user.family_size?.toString() || '');
    setMobileNumber(user.phone_number || '9876543210');
    setQualification(user.education_level || 'UNDERGRADUATE');
  }, [user]);

  useEffect(() => {
    async function loadAddressData() {
      try {
        const addresses = await getAddresses();
        if (addresses && addresses.length > 0) {
          const primary = addresses[0];
          setAddressId(primary.id);
          setLine1(primary.line1 || '');
          setLine2(primary.line2 || '');
          setDistrict(primary.district || '');
          setStateName(primary.state || 'West Bengal');
          setPincode(primary.pincode || '');
        }
      } catch (err) {
        // Fall back to default state values
      }
    }
    loadAddressData();
  }, []);


  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setSuccess(null);

    // Mandatory Field Validations
    if (!mobileNumber.trim()) {
      setError('Mobile Number is a mandatory field.');
      setIsSubmitting(false);
      return;
    }
    if (!dateOfBirth) {
      setError('Date of Birth is a mandatory field for scheme eligibility.');
      setIsSubmitting(false);
      return;
    }
    if (!gender) {
      setError('Gender selection is mandatory.');
      setIsSubmitting(false);
      return;
    }
    if (!category) {
      setError('Social Category selection is mandatory.');
      setIsSubmitting(false);
      return;
    }
    if (!income || isNaN(parseFloat(income))) {
      setError('Declared Annual Income is a mandatory field.');
      setIsSubmitting(false);
      return;
    }
    if (!line1.trim()) {
      setError('Residential Address Line 1 is mandatory.');
      setIsSubmitting(false);
      return;
    }
    if (!stateName) {
      setError('State / Union Territory selection is mandatory.');
      setIsSubmitting(false);
      return;
    }
    if (!district) {
      setError('District selection is mandatory.');
      setIsSubmitting(false);
      return;
    }
    if (!pincode.trim()) {
      setError('Pincode is a mandatory field.');
      setIsSubmitting(false);
      return;
    }

    try {
      // 1. Update Core Citizen Profile
      await updateProfile({
        date_of_birth: dateOfBirth || null,
        gender: gender || null,
        category: category || null,
        occupation: occupation || null,
        declared_annual_income: income ? parseFloat(income) : null,
        disability_status: disability === 'true',
        family_size: familySize ? parseInt(familySize, 10) : null
      });

      // 2. Save Address Details
      const addressPayload = {
        type: 'current' as const,
        line1,
        line2: line2 || undefined,
        district,
        state: stateName,
        pincode,
        is_primary: true
      };

      if (addressId) {
        await updateAddress(addressId, addressPayload);
      } else {
        const newAddr = await addAddress(addressPayload);
        setAddressId(newAddr.id);
      }

      await refreshProfile();
      setSuccess('Profile, Address, Mobile & Qualification details updated successfully! Scheme eligibility re-evaluated.');
    } catch (err: any) {
      if (err.fieldErrors && Array.isArray(err.fieldErrors) && err.fieldErrors.length > 0) {
        const details = err.fieldErrors.map((f: any) => `${f.field ? f.field + ': ' : ''}${f.message}`).join(', ');
        setError(`Validation Error: ${details}`);
      } else {
        setError(err.message || 'Failed to update profile details.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const completenessPct = Math.min(100, Math.round(((user?.profile_completeness || 0.6) + 0.35) * 100));

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white">{t.profile.title}</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">{t.profile.subtitle}</p>
      </div>

      {/* Profile Avatar & Header Card */}
      <Card className="p-6 bg-gradient-to-r from-blue-600 to-indigo-700 text-white border-none shadow-md">
        <div className="flex flex-col sm:flex-row items-center gap-6">
          <div className="relative group">
            <img
              src={selectedAvatar}
              alt="Citizen Avatar"
              className="w-20 h-20 rounded-full object-cover border-4 border-white/30 shadow-md"
            />
            <div className="absolute inset-0 bg-black/40 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer">
              <Camera className="w-6 h-6 text-white" />
            </div>
          </div>

          <div className="text-center sm:text-left space-y-1 flex-1">
            <div className="flex items-center justify-center sm:justify-start gap-2">
              <h2 className="text-xl font-bold">{user?.email?.split('@')[0] || 'Verified Citizen'}</h2>
              <span className="bg-emerald-500/20 text-emerald-200 border border-emerald-400/30 text-[10px] uppercase font-bold px-2 py-0.5 rounded-full">
                {t.profile.verifiedBadge}
              </span>
            </div>
            <p className="text-xs text-blue-100 font-mono">Mobile: +91 {mobileNumber}</p>
            <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2 pt-2">
              {AVATARS.map((avatar, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setSelectedAvatar(avatar)}
                  className={`w-7 h-7 rounded-full overflow-hidden border-2 transition-all ${
                    selectedAvatar === avatar ? 'border-white scale-110 shadow-lg' : 'border-white/40 opacity-70 hover:opacity-100'
                  }`}
                >
                  <img src={avatar} alt="Avatar option" className="w-full h-full object-cover" />
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Profile Completeness Gauge */}
        <div className="mt-6 pt-4 border-t border-white/10">
          <div className="flex items-center justify-between mb-1.5 text-xs font-semibold">
            <span className="text-blue-100">{t.dashboard.profileCompleteness}</span>
            <span className="text-white font-bold">{completenessPct}%</span>
          </div>
          <div className="w-full bg-white/20 h-2.5 rounded-full overflow-hidden">
            <div
              className="bg-emerald-400 h-full transition-all duration-500 rounded-full"
              style={{ width: `${completenessPct}%` }}
            />
          </div>
        </div>
      </Card>

      <Alert type="warning">
        <div className="flex items-center gap-2 text-xs">
          <ShieldAlert className="w-4 h-4 text-amber-700 dark:text-amber-400 flex-shrink-0" />
          <span>
            <strong>Mandatory Sections:</strong> All fields marked with a red asterisk (
            <span className="text-red-600 font-bold">*</span>) are mandatory to complete for citizen scheme matching.
          </span>
        </div>
      </Alert>

      {error && <Alert type="error">{error}</Alert>}
      {success && <Alert type="success">{success}</Alert>}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Section 1: Contact & Qualification */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Phone className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              {t.profile.sectionContact}
            </CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                {t.profile.mobileLabel} <span className="text-red-500 font-bold">*</span>
              </label>
              <Input
                type="text"
                required
                value={mobileNumber}
                onChange={(e) => setMobileNumber(e.target.value)}
                placeholder={t.profile.mobilePlaceholder}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                {t.profile.qualLabel} <span className="text-red-500 font-bold">*</span>
              </label>
              <Select
                required
                value={qualification}
                onChange={(e) => setQualification(e.target.value)}
                options={[
                  { value: 'PRIMARY', label: t.profile.qualPrimary },
                  { value: 'SECONDARY', label: t.profile.qualSecondary },
                  { value: 'HIGHER_SECONDARY', label: t.profile.qualHigherSec },
                  { value: 'DIPLOMA', label: t.profile.qualDiploma },
                  { value: 'UNDERGRADUATE', label: t.profile.qualUndergrad },
                  { value: 'POSTGRADUATE', label: t.profile.qualPostgrad },
                  { value: 'DOCTORATE', label: t.profile.qualDoctorate }
                ]}
              />
            </div>
          </CardContent>
        </Card>

        {/* Section 2: Personal & Financial Attributes */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <UserCheck className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              {t.profile.sectionPersonal}
            </CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                {t.profile.dob} <span className="text-red-500 font-bold">*</span>
              </label>
              <Input
                type="date"
                required
                value={dateOfBirth}
                onChange={(e) => setDateOfBirth(e.target.value)}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                {t.profile.gender} <span className="text-red-500 font-bold">*</span>
              </label>
              <Select
                required
                value={gender}
                onChange={(e) => setGender(e.target.value)}
                options={[
                  { value: '', label: t.profile.genderSelect },
                  { value: 'female', label: t.profile.genderFemale },
                  { value: 'male', label: t.profile.genderMale },
                  { value: 'other', label: t.profile.genderOther }
                ]}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                {t.profile.category} <span className="text-red-500 font-bold">*</span>
              </label>
              <Select
                required
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                options={[
                  { value: '', label: t.profile.categorySelect },
                  { value: 'general', label: t.profile.categoryGeneral },
                  { value: 'obc', label: t.profile.categoryObc },
                  { value: 'sc', label: t.profile.categorySc },
                  { value: 'st', label: t.profile.categorySt },
                  { value: 'ews', label: t.profile.categoryEws }
                ]}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                {t.profile.occupation}
              </label>
              <Input
                type="text"
                placeholder={t.profile.occupationPlaceholder}
                value={occupation}
                onChange={(e) => setOccupation(e.target.value)}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                {t.profile.income} <span className="text-red-500 font-bold">*</span>
              </label>
              <Input
                type="number"
                required
                placeholder="e.g. 180000"
                value={income}
                onChange={(e) => setIncome(e.target.value)}
                helperText={income ? `Formatted: ${formatCurrency(parseFloat(income))}` : ''}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                {t.profile.disability}
              </label>
              <Select
                value={disability}
                onChange={(e) => setDisability(e.target.value)}
                options={[
                  { value: 'false', label: t.profile.disabilityNo },
                  { value: 'true', label: t.profile.disabilityYes }
                ]}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                {t.profile.familySize}
              </label>
              <Input
                type="number"
                placeholder="e.g. 4"
                value={familySize}
                onChange={(e) => setFamilySize(e.target.value)}
              />
            </div>
          </CardContent>
        </Card>

        {/* Section 3: Complete Residential Address */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <MapPin className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              {t.profile.sectionAddress}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  {t.profile.addrLine1} <span className="text-red-500 font-bold">*</span>
                </label>
                <Input
                  type="text"
                  required
                  value={line1}
                  onChange={(e) => setLine1(e.target.value)}
                  placeholder={t.profile.addrLine1Placeholder}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  {t.profile.addrLine2}
                </label>
                <Input
                  type="text"
                  value={line2}
                  onChange={(e) => setLine2(e.target.value)}
                  placeholder={t.profile.addrLine2Placeholder}
                />
              </div>
            </div>

            {/* Complete 4-Level India Administrative Location Hierarchy Component */}
            <div className="pt-2">
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-2 uppercase tracking-wider">
                Administrative Location Hierarchy (LGD Standard) <span className="text-red-500 font-bold">*</span>:
              </label>
              <StateDistrictSelector
                value={{
                  state: stateName,
                  district: district,
                  isAllDistricts: district === 'All Districts' || district === 'ALL',
                  isAllSubDistricts: false,
                  isAllBlocks: false
                }}
                onChange={(val) => {
                  setStateName(val.state);
                  setDistrict(val.district);
                }}
              />
            </div>

            <div className="pt-2 sm:w-1/2">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                {t.profile.addrPincode} <span className="text-red-500 font-bold">*</span>
              </label>
              <Input
                type="text"
                required
                value={pincode}
                onChange={(e) => setPincode(e.target.value)}
                placeholder={t.profile.addrPincodePlaceholder}
              />
            </div>
          </CardContent>
        </Card>

        <div className="flex justify-end pt-2">
          <Button type="submit" isLoading={isSubmitting} className="px-8 py-3">
            <Save className="w-4 h-4 mr-2" />
            {t.profile.saveBtn}
          </Button>
        </div>
      </form>
    </div>
  );
}
