import React from 'react';
import '@/app/globals.css';
import { AuthProvider } from '@/lib/auth/auth-context';
import { ThemeProvider } from '@/lib/theme/theme-context';

export const metadata = {
  title: 'CivicLens | Operations Console',
  description: 'Authoritative operational admin, case worker, and CSC console for CivicLens backend.',
  robots: {
    index: false,
    follow: false,
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning className="dark">
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem('civiclens_admin_theme');if(t==='light'){document.documentElement.classList.remove('dark');document.documentElement.classList.add('light');}else{document.documentElement.classList.add('dark');}}catch(e){}})();`
          }}
        />
      </head>
      <body className="bg-slate-50 text-slate-900 dark:bg-console-bg dark:text-console-text min-h-screen font-sans antialiased transition-colors duration-200">
        <ThemeProvider defaultTheme="dark">
          <AuthProvider>{children}</AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
