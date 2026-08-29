import { describe, it, expect } from 'vitest';
import { en } from '../../lib/i18n/locales/en';
import { hi } from '../../lib/i18n/locales/hi';

describe('Internationalization Dictionaries', () => {
  it('contains English and Hindi translations for essential UI elements', () => {
    expect(en.common.appName).toBe('CivicLens');
    expect(hi.common.appName).toBe('सिविकलेंस');

    expect(en.eligibility.eligible).toBe('Eligible');
    expect(hi.eligibility.eligible).toBe('पात्र');

    expect(en.nav.dashboard).toBe('Dashboard');
    expect(hi.nav.dashboard).toBe('डैशबोर्ड');
  });
});
