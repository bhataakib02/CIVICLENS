'use client';

import React, { useState } from 'react';
import { CitizenDetail } from '@/types/api';
import { StatusBadge } from '@/components/ui/status-badge';
import { ConsentView } from './consent-view';
import { formatDate, formatCurrency, formatReadableId } from '@/lib/formatting';
import { updateCitizen, updateCitizenProfile, deleteCitizen, sendCitizenOtp } from '@/lib/api/citizens';
import { Modal } from '@/components/ui/modal';
import { Button } from '@/components/ui/button';
import { useRouter } from 'next/navigation';
import { Edit, Trash2, KeyRound, UserCheck, ShieldAlert, Sparkles, AlertCircle, Save, Lock, Send, CheckCircle2 } from 'lucide-react';

interface CitizenProfileViewProps {
  citizen: CitizenDetail;
  onRefresh?: () => void;
}

export function CitizenProfileView({ citizen, onRefresh }: CitizenProfileViewProps) {
  const router = useRouter();
  const p = citizen.profile;

  // Modals state
  const [showEditAccountModal, setShowEditAccountModal] = useState(false);
  const [showEditProfileModal, setShowEditProfileModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [otpDispatchStatus, setOtpDispatchStatus] = useState<string | null>(null);

  // Form states
  const [email, setEmail] = useState(citizen.email || '');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [password, setPassword] = useState('');
  const [status, setStatus] = useState(citizen.status || 'active');

  const [category, setCategory] = useState(p?.category || 'GENERAL');
  const [occupation, setOccupation] = useState(p?.occupation || '');
  const [gender, setGender] = useState(p?.gender || 'male');
  const [income, setIncome] = useState(p?.declared_annual_income || 0);
  const [disability, setDisability] = useState(p?.disability_status ?? false);
  const [familySize, setFamilySize] = useState(p?.family_size || 1);

  const handleSaveAccount = async () => {
    setIsSubmitting(true);
    try {
      await updateCitizen(citizen.user_id, {
        email: email || undefined,
        phone_number: phoneNumber || undefined,
        password: password || undefined,
        status,
      });
      setShowEditAccountModal(false);
      setPassword('');
      alert('Citizen account and password updated successfully.');
      if (onRefresh) onRefresh();
    } catch (err: any) {
      alert('Failed to update account: ' + err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSendRecoveryOtp = async () => {
    setIsSubmitting(true);
    setOtpDispatchStatus(null);
    try {
      const res = await sendCitizenOtp(citizen.user_id);
      setOtpDispatchStatus(res.message || `Real 6-digit OTP code sent to ${res.target}`);
    } catch (err: any) {
      alert('Failed to dispatch recovery OTP: ' + err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSaveProfile = async () => {
    setIsSubmitting(true);
    try {
      await updateCitizenProfile(citizen.user_id, {
        category,
        occupation,
        gender,
        declared_annual_income: Number(income),
        disability_status: Boolean(disability),
        family_size: Number(familySize),
      });
      setShowEditProfileModal(false);
      alert('Citizen profile details updated successfully.');
      if (onRefresh) onRefresh();
    } catch (err: any) {
      alert('Failed to update profile: ' + err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteAccount = async () => {
    setIsSubmitting(true);
    try {
      await deleteCitizen(citizen.user_id);
      alert('Citizen record deleted permanently.');
      router.push('/citizens');
    } catch (err: any) {
      alert('Failed to delete account: ' + err.message);
    } finally {
      setIsSubmitting(false);
      setShowDeleteModal(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Overview & Admin Action Toolbar */}
      <div className="bg-white dark:bg-slate-900/90 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="space-y-1">
          <div className="flex items-center space-x-3">
            <h2 className="text-xl font-extrabold text-slate-900 dark:text-white">
              {citizen.email || 'Citizen Account'}
            </h2>
            <StatusBadge status={citizen.status} />
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">
            Citizen Ref ID: <span className="text-indigo-600 dark:text-indigo-400 font-extrabold bg-indigo-500/10 border border-indigo-500/20 px-2 py-0.5 rounded-lg">{formatReadableId(citizen.email || citizen.user_id, 'CIT')}</span> | Masked Phone: <span className="text-slate-800 dark:text-slate-200 font-semibold">{citizen.phone_number_masked || 'N/A'}</span>
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={() => setShowEditAccountModal(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold bg-indigo-500/10 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-500/20 border border-indigo-500/30 transition-all"
          >
            <Edit className="w-3.5 h-3.5" />
            <span>Edit Account &amp; Password</span>
          </button>

          <button
            onClick={() => setShowEditProfileModal(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold bg-blue-500/10 text-blue-700 dark:text-blue-300 hover:bg-blue-500/20 border border-blue-500/30 transition-all"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Edit Profile Data</span>
          </button>

          <button
            onClick={handleSendRecoveryOtp}
            disabled={isSubmitting}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold bg-amber-500/10 text-amber-700 dark:text-amber-300 hover:bg-amber-500/20 border border-amber-500/30 transition-all"
          >
            <Send className="w-3.5 h-3.5" />
            <span>{isSubmitting ? 'Sending...' : 'Resend Recovery OTP'}</span>
          </button>

          <button
            onClick={() => setShowDeleteModal(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold bg-red-500/10 text-red-700 dark:text-red-300 hover:bg-red-500/20 border border-red-500/30 transition-all"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Delete User</span>
          </button>
        </div>
      </div>

      {/* OTP Dispatch Banner Notification */}
      {otpDispatchStatus && (
        <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-between text-xs text-emerald-700 dark:text-emerald-300 font-bold shadow-md">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-500" />
            <span>{otpDispatchStatus}</span>
          </div>
          <button onClick={() => setOtpDispatchStatus(null)} className="text-xs hover:underline font-mono">
            Dismiss
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Snapshot */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white dark:bg-slate-900/90 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800">
              <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                Profile Snapshot (v{p?.current_version_no || 1})
              </h3>
              <button
                onClick={() => setShowEditProfileModal(true)}
                className="text-xs font-bold text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1"
              >
                <Edit className="w-3.5 h-3.5" /> Modify Snapshot
              </button>
            </div>

            {p ? (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-5 text-xs">
                <div>
                  <p className="text-slate-400 font-medium">Date of Birth</p>
                  <p className="font-bold text-slate-900 dark:text-white mt-1">{p.date_of_birth || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-slate-400 font-medium">Gender</p>
                  <p className="font-bold text-slate-900 dark:text-white capitalize mt-1">{p.gender || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-slate-400 font-medium">Social Category</p>
                  <p className="font-bold text-slate-900 dark:text-white uppercase mt-1">{p.category || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-slate-400 font-medium">Occupation</p>
                  <p className="font-bold text-slate-900 dark:text-white capitalize mt-1">{p.occupation || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-slate-400 font-medium">Declared Annual Income</p>
                  <p className="font-bold text-slate-900 dark:text-white mt-1 font-mono">{formatCurrency(p.declared_annual_income)}</p>
                </div>
                <div>
                  <p className="text-slate-400 font-medium">Disability Status</p>
                  <p className="font-bold text-slate-900 dark:text-white mt-1">
                    {p.disability_status === true ? 'Yes' : p.disability_status === false ? 'No' : 'N/A'}
                  </p>
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-400 italic py-4">Citizen has not completed progressive profile setup.</p>
            )}
          </div>

          {/* Activity Metrics */}
          <div className="bg-white dark:bg-slate-900/90 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-xl grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-3xl font-mono font-extrabold text-indigo-600 dark:text-indigo-400">{citizen.applications_count}</p>
              <p className="text-xs font-bold text-slate-500 dark:text-slate-400 mt-1">Applications</p>
            </div>
            <div>
              <p className="text-3xl font-mono font-extrabold text-indigo-600 dark:text-indigo-400">{citizen.documents_count}</p>
              <p className="text-xs font-bold text-slate-500 dark:text-slate-400 mt-1">Documents</p>
            </div>
            <div>
              <p className="text-3xl font-mono font-extrabold text-indigo-600 dark:text-indigo-400">{citizen.active_consents_count}</p>
              <p className="text-xs font-bold text-slate-500 dark:text-slate-400 mt-1">Active Consents</p>
            </div>
          </div>
        </div>

        {/* Consents Card */}
        <div className="bg-white dark:bg-slate-900/90 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-xl space-y-4">
          <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider border-b border-slate-200 dark:border-slate-800 pb-3">
            Consents &amp; Authorization State
          </h3>
          <ConsentView consents={citizen.profile ? (citizen as any).consents || [] : []} />
        </div>
      </div>

      {/* Edit Account & Password Modal */}
      <Modal isOpen={showEditAccountModal} onClose={() => setShowEditAccountModal(false)} title="Edit Citizen Account & Password">
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1">Email Address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="e.g. citizen@gmail.com"
              className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2.5 text-sm text-slate-900 dark:text-white"
            />
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1">Phone Number (Direct Update)</label>
            <input
              type="text"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              placeholder="e.g. 9103882076"
              className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2.5 text-sm text-slate-900 dark:text-white font-mono"
            />
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1">Set New Password (Optional)</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Leave blank to keep existing password..."
              className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2.5 text-sm text-slate-900 dark:text-white font-mono"
            />
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1">Account Status</label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2.5 text-sm text-slate-900 dark:text-white"
            >
              <option value="active">Active</option>
              <option value="suspended">Suspended</option>
              <option value="unverified">Unverified</option>
            </select>
          </div>

          <div className="flex justify-end space-x-3 pt-2">
            <Button variant="outline" onClick={() => setShowEditAccountModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveAccount} disabled={isSubmitting} className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold">
              Save Account &amp; Password
            </Button>
          </div>
        </div>
      </Modal>

      {/* Edit Profile Data Modal */}
      <Modal isOpen={showEditProfileModal} onClose={() => setShowEditProfileModal(false)} title="Modify Citizen Demographic Profile">
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1">Social Category</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2.5 text-sm text-slate-900 dark:text-white"
              >
                <option value="GENERAL">General</option>
                <option value="OBC">OBC</option>
                <option value="SC">SC</option>
                <option value="ST">ST</option>
                <option value="EWS">EWS</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1">Gender</label>
              <select
                value={gender}
                onChange={(e) => setGender(e.target.value)}
                className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2.5 text-sm text-slate-900 dark:text-white"
              >
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1">Occupation</label>
            <input
              type="text"
              value={occupation}
              onChange={(e) => setOccupation(e.target.value)}
              placeholder="e.g. Student, Farmer, Merchant"
              className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2.5 text-sm text-slate-900 dark:text-white"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1">Annual Income (₹)</label>
              <input
                type="number"
                value={income}
                onChange={(e) => setIncome(Number(e.target.value))}
                placeholder="150000"
                className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2.5 text-sm text-slate-900 dark:text-white font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1">Family Members</label>
              <input
                type="number"
                value={familySize}
                onChange={(e) => setFamilySize(Number(e.target.value))}
                placeholder="4"
                className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2.5 text-sm text-slate-900 dark:text-white font-mono"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1">Disability Status</label>
            <select
              value={disability ? 'yes' : 'no'}
              onChange={(e) => setDisability(e.target.value === 'yes')}
              className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2.5 text-sm text-slate-900 dark:text-white"
            >
              <option value="no">No</option>
              <option value="yes">Yes (Differently Abled)</option>
            </select>
          </div>

          <div className="flex justify-end space-x-3 pt-2">
            <Button variant="outline" onClick={() => setShowEditProfileModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveProfile} disabled={isSubmitting} className="bg-blue-600 hover:bg-blue-700 text-white font-bold">
              Save Profile Data
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal isOpen={showDeleteModal} onClose={() => setShowDeleteModal(false)} title="Confirm Citizen Account Deletion">
        <div className="space-y-4">
          <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30 flex items-start gap-3">
            <ShieldAlert className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
            <div className="space-y-1 text-xs">
              <p className="font-extrabold text-red-700 dark:text-red-400 uppercase tracking-wider">Warning: Irreversible Action</p>
              <p className="text-slate-700 dark:text-slate-300">
                You are about to permanently delete citizen account <strong>{citizen.email || citizen.user_id}</strong>. All profile data and records will be deleted.
              </p>
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-2">
            <Button variant="outline" onClick={() => setShowDeleteModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleDeleteAccount} disabled={isSubmitting} className="bg-red-600 hover:bg-red-700 text-white font-bold">
              Delete Citizen Permanently
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
