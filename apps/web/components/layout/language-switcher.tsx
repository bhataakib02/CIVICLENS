'use client';

import React from 'react';
import { useTranslation, Language } from '@/lib/i18n';
import { Globe } from 'lucide-react';

export function LanguageSwitcher() {
  const { language, setLanguage } = useTranslation();

  return (
    <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg text-xs font-semibold">
      <Globe className="w-3.5 h-3.5 ml-1 text-slate-500" />
      <button
        onClick={() => setLanguage('en')}
        className={`px-2 py-1 rounded-md transition-colors ${
          language === 'en' ? 'bg-white text-blue-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
        }`}
        aria-label="Switch to English"
      >
        EN
      </button>
      <button
        onClick={() => setLanguage('hi')}
        className={`px-2 py-1 rounded-md transition-colors ${
          language === 'hi' ? 'bg-white text-blue-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
        }`}
        aria-label="हिन्दी में बदलें"
      >
        हिन्दी
      </button>
    </div>
  );
}
