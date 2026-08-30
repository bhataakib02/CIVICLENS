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
    <html lang="en" className="dark">
      <body className="bg-console-bg text-console-text min-h-screen font-sans antialiased transition-colors duration-200">
        <ThemeProvider defaultTheme="dark">
          <AuthProvider>{children}</AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
