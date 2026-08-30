import { en } from './en';

export const bn: typeof en = {
  ...en,
  common: {
    ...en.common,
    appName: 'CivicLens',
    tagline: 'জনসেবা নেভিগেশন',
    loading: 'লোড হচ্ছে...',
    save: 'সংরক্ষণ করুন',
    cancel: 'বাতিল করুন',
    submit: 'জমা দিন',
    back: 'ফিরে যান',
    next: 'পরবর্তী',
    close: 'বন্ধ করুন',
    search: 'অনুসন্ধান করুন',
    filter: 'ফিল্টার',
    viewDetails: 'বিস্তারিত দেখুন',
    required: 'প্রয়োজনীয়',
    optional: 'ঐচ্ছিক',
    status: 'অবস্থা',
    actions: 'পদক্ষেপ',
    download: 'ডাউনলোড',
    upload: 'আপলোড',
    confirm: 'নিশ্চিত করুন',
    edit: 'সম্পাদনা',
    delete: 'মুছে ফেলুন',
    success: 'সফলতা',
    error: 'ত্রুটি',
    warning: 'সতর্কতা',
    info: 'তথ্য',
    noData: 'কোন তথ্য পাওয়া যায়নি।'
  },
  nav: {
    ...en.nav,
    dashboard: 'ড্যাশবোর্ড',
    schemes: 'প্রকল্প',
    eligibility: 'যোগ্যতা',
    assistant: 'CivicLens কে জিজ্ঞাসা করুন',
    documents: 'নথিপত্র',
    applications: 'আবেদনপত্র',
    notifications: 'বিজ্ঞপ্তি',
    profile: 'প্রোফাইল',
    settings: 'সেটিংস',
    logout: 'সাইন আউট',
    login: 'সাইন ইন'
  }
};
