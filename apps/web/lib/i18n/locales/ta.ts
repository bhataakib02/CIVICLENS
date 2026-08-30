import { en } from './en';

export const ta: typeof en = {
  ...en,
  common: {
    ...en.common,
    appName: 'CivicLens',
    tagline: 'பொது சேவை வழிகாட்டி',
    loading: 'ஏற்றப்படுகிறது...',
    save: 'சேமிக்க',
    cancel: 'ரத்து செய்ய',
    submit: 'சமர்ப்பிக்க',
    back: 'பின்னால்',
    next: 'அடுத்து',
    close: 'மூடு',
    search: 'தேடு',
    filter: 'வடிகட்டி',
    viewDetails: 'விவரங்களை பார்க்க',
    required: 'தேவையான',
    optional: 'விருப்ப தேர்வு',
    status: 'நிலை',
    actions: 'செயல்கள்',
    download: 'பதிவிறக்கு',
    upload: 'பதிவேற்று',
    confirm: 'உறுதிப்படுத்து',
    edit: 'திருத்து',
    delete: 'நீக்கு',
    success: 'வெற்றி',
    error: 'பிழை',
    warning: 'எச்சரிக்கை',
    info: 'தகவல்',
    noData: 'தகவல்கள் எதுவும் இல்லை.'
  },
  nav: {
    ...en.nav,
    dashboard: 'டாஷ்போர்டு',
    schemes: 'திட்டங்கள்',
    eligibility: 'தகுதி',
    assistant: 'CivicLens இடம் கேட்கவும்',
    documents: 'ஆவணங்கள்',
    applications: 'விண்ணப்பங்கள்',
    notifications: 'அறிவிப்புகள்',
    profile: 'சுயவிவரம்',
    settings: 'அமைப்புகள்',
    logout: 'வெளியேறு',
    login: 'உள்நுழை'
  }
};
