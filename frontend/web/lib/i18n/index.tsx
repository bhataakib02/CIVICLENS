'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { en } from './locales/en';
import { hi } from './locales/hi';
import { ur } from './locales/ur';
import { bn } from './locales/bn';
import { mr } from './locales/mr';
import { ta } from './locales/ta';
import { te } from './locales/te';
import { gu } from './locales/gu';
import { kn } from './locales/kn';

export type Language = 'en' | 'hi' | 'ur' | 'bn' | 'mr' | 'ta' | 'te' | 'gu' | 'kn';
type TranslationKeys = typeof en;

interface I18nContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: TranslationKeys;
}

const translations: Record<Language, TranslationKeys> = {
  en,
  hi,
  ur,
  bn,
  mr,
  ta,
  te,
  gu,
  kn
};

const I18nContext = createContext<I18nContextType | undefined>(undefined);

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<Language>('en');

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedLang = localStorage.getItem('civiclens_lang') as Language;
      if (savedLang && translations[savedLang]) {
        setLanguageState(savedLang);
      }
    }
  }, []);

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    if (typeof window !== 'undefined') {
      localStorage.setItem('civiclens_lang', lang);
    }
  };

  return (
    <I18nContext.Provider value={{ language, setLanguage, t: translations[language] }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useTranslation() {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error('useTranslation must be used within an I18nProvider');
  }
  return context;
}
