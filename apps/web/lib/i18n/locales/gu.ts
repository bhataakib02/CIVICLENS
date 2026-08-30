import { en } from './en';

export const gu: typeof en = {
  ...en,
  common: {
    ...en.common,
    appName: 'CivicLens',
    tagline: 'જાહેર સેવા નેવિગેશન',
    loading: 'લોડ થઈ રહ્યું છે...',
    save: 'સાચવો',
    cancel: 'રદ કરો',
    submit: 'સબમિટ કરો',
    back: 'પાછા',
    next: 'આગળ',
    close: 'બંધ કરો',
    search: 'શોધો',
    filter: 'ફિલ્ટર',
    viewDetails: 'વિગતો જુઓ',
    required: 'જરૂરી',
    optional: 'વૈકલ્પિક',
    status: 'સ્થિતિ',
    actions: 'ક્રિયાઓ',
    download: 'ડાઉનલોડ',
    upload: 'અપલોડ',
    confirm: 'કન્ફર્મ કરો',
    edit: 'એડિટ',
    delete: 'હટાવો',
    success: 'સફળતા',
    error: 'ભૂલ',
    warning: 'ચેતવણી',
    info: 'માહિતી',
    noData: 'કોઈ રેકોર્ડ મળ્યો નથી.'
  },
  nav: {
    ...en.nav,
    dashboard: 'ડેશબોર્ડ',
    schemes: 'યોજનાઓ',
    eligibility: 'પાત્રતા',
    assistant: 'CivicLens ને પૂછો',
    documents: 'દસ્તાવેજો',
    applications: 'અરજીઓ',
    notifications: 'સૂચનાઓ',
    profile: 'પ્રોફાઇલ',
    settings: 'સેટિંગ્સ',
    logout: 'સાઇન આઉટ',
    login: 'સાઇન ઇન'
  }
};
