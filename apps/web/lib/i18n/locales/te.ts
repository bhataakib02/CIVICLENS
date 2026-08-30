import { en } from './en';

export const te: typeof en = {
  ...en,
  common: {
    ...en.common,
    appName: 'CivicLens',
    tagline: 'ప్రజా సేవల నావిగేషన్',
    loading: 'లోడ్ అవుతోంది...',
    save: 'సేవ్ చేయండి',
    cancel: 'రద్దు చేయండి',
    submit: 'సమర్పించండి',
    back: 'వెనుకకు',
    next: 'తరువాత',
    close: 'మూసివేయండి',
    search: 'శోధించండి',
    filter: 'ఫిల్టర్',
    viewDetails: 'వివరాలు చూడండి',
    required: 'అవసరం',
    optional: 'ఐచ్ఛికం',
    status: 'స్థితి',
    actions: 'చర్యలు',
    download: 'డౌన్‌లోడ్',
    upload: 'అప్‌లోడ్',
    confirm: 'నిర్ధారించండి',
    edit: 'సవరించు',
    delete: 'తొలగించు',
    success: 'విజయం',
    error: 'లోపం',
    warning: 'హెచ్చరిక',
    info: 'సమాచారం',
    noData: 'డేటా కనుగొనబడలేదు.'
  },
  nav: {
    ...en.nav,
    dashboard: 'డాష్‌బోర్డ్',
    schemes: 'పథకాలు',
    eligibility: 'అర్హత',
    assistant: 'CivicLens ను అడగండి',
    documents: 'పత్రాలు',
    applications: 'దరఖాస్తులు',
    notifications: 'నోటిఫికేషన్లు',
    profile: 'ప్రొఫైల్',
    settings: 'సెట్టింగ్‌లు',
    logout: 'లాగ్ అవుట్',
    login: 'లాగిన్'
  }
};
