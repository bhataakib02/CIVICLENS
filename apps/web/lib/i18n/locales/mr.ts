import { en } from './en';

export const mr: typeof en = {
  ...en,
  common: {
    ...en.common,
    appName: 'CivicLens',
    tagline: 'लोकसेवा नॅव्हिगेशन',
    loading: 'लोड होत आहे...',
    save: 'जतन करा',
    cancel: 'रद्द करा',
    submit: 'सादर करा',
    back: 'मागे',
    next: 'पुढे',
    close: 'बंद करा',
    search: 'शोधा',
    filter: 'फिल्टर',
    viewDetails: 'तपशील पहा',
    required: 'आवश्यक',
    optional: 'ऐच्छिक',
    status: 'स्थिती',
    actions: 'कृती',
    download: 'डाउनलोड',
    upload: 'अपलोड',
    confirm: 'निश्चित करा',
    edit: 'संपादित करा',
    delete: 'हटवा',
    success: 'यशस्वी',
    error: 'त्रुटी',
    warning: 'तकीद',
    info: 'माहिती',
    noData: 'कोणतीही माहिती आढळली नाही.'
  },
  nav: {
    ...en.nav,
    dashboard: 'डॅशबोर्ड',
    schemes: 'योजना',
    eligibility: 'पात्रता',
    assistant: 'CivicLens ला विचारा',
    documents: 'कागदपत्रे',
    applications: 'अर्ज',
    notifications: 'सूचना',
    profile: 'प्रोफाइल',
    settings: 'सेटिंग्ज',
    logout: 'साइन आउट',
    login: 'साइन इन'
  }
};
