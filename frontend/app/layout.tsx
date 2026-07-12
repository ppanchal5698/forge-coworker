import './globals.css';

import { Inter } from "next/font/google";
import { cn } from "@/lib/utils";
import AppShell from '@/components/AppShell';
import { AuthTokenProvider } from '@/components/AuthTokenProvider';

const inter = Inter({ subsets: ['latin'], variable: '--font-sans' });


// Root layout — global providers (theme, Supabase client)
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={cn("font-sans", inter.variable)}>
      <body>
        <AuthTokenProvider>
          <AppShell>{children}</AppShell>
        </AuthTokenProvider>
      </body>
    </html>
  );
}
