"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';

import { useAuthToken } from '@/components/AuthTokenProvider';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { token, hasToken, saveToken, clearToken } = useAuthToken();
  const [draftToken, setDraftToken] = useState(token);

  useEffect(() => {
    setDraftToken(token);
  }, [token]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-stone-50 via-amber-50/40 to-rose-50/20">
      <header className="sticky top-0 z-30 border-b border-stone-200/80 bg-white/90 backdrop-blur">
        <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-4 py-3 md:px-6">
          <div className="flex items-center gap-6">
            <Link href="/" className="text-lg font-semibold tracking-tight text-stone-900">
              Forge
            </Link>
            <nav className="flex items-center gap-2">
              <Link
                href="/"
                className={cn(
                  'rounded-md px-3 py-1.5 text-sm transition',
                  pathname === '/'
                    ? 'bg-stone-900 text-stone-50'
                    : 'text-stone-700 hover:bg-stone-100'
                )}
              >
                Dashboard
              </Link>
              <Link
                href="/workspaces"
                className={cn(
                  'rounded-md px-3 py-1.5 text-sm transition',
                  pathname.startsWith('/workspaces')
                    ? 'bg-stone-900 text-stone-50'
                    : 'text-stone-700 hover:bg-stone-100'
                )}
              >
                Workspaces
              </Link>
            </nav>
          </div>

          <div className="flex items-center gap-2">
            <Dialog>
              <DialogTrigger
                render={<Button variant={hasToken ? 'secondary' : 'default'} />}
              >
                {hasToken ? 'Update API Token' : 'Set API Token'}
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Backend Bearer Token</DialogTitle>
                  <DialogDescription>
                    All API calls require Authorization: Bearer token from backend auth settings.
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-2">
                  <Label htmlFor="api-token">Token</Label>
                  <Input
                    id="api-token"
                    type="password"
                    value={draftToken}
                    onChange={(event) => setDraftToken(event.target.value)}
                    placeholder="Paste API_BEARER_TOKEN"
                  />
                </div>
                <DialogFooter className="gap-2 sm:gap-0">
                  <Button variant="outline" onClick={clearToken}>
                    Clear
                  </Button>
                  <Button onClick={() => saveToken(draftToken)}>Save Token</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-7xl px-4 py-6 md:px-6 md:py-8">{children}</main>
    </div>
  );
}
