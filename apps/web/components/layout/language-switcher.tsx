'use client';

import React from 'react';
import { useTranslation, Language } from '@/lib/i18n';
import { Globe } from 'lucide-react';

const LANGUAGES: { code: Language; label: string }[] = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'हिन्दी' },
  { code: 'ur', label: 'اردو' },
  { code: 'bn', label: 'বাংলা' },
  { code: 'mr', label: 'मराठी' },
  { code: 'ta', label: 'தமிழ்' },
  { code: 'te', label: 'తెలుగు' },
  { code: 'gu', label: 'ગુજરાતી' },
  { code: 'kn', label: 'ಕನ್ನಡ' }
];

export function LanguageSwitcher() {
  const { language, setLanguage } = useTranslation();

  return (
    <div className="relative inline-flex items-center">
      <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded-xl text-xs font-semibold border border-slate-200 dark:border-slate-700">
        <Globe className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400 mr-0.5" />
        <select
          value={language}
          onChange={(e) => setLanguage(e.target.value as Language)}
          className="bg-transparent text-slate-700 dark:text-slate-200 font-semibold text-xs focus:outline-none cursor-pointer pr-1"
          aria-label="Select Language"
        >
          {LANGUAGES.map((lang) => (
            <option key={lang.code} value={lang.code} className="bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100">
              {lang.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
