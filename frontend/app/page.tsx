"use client";

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';

import { useAuthToken } from '@/components/AuthTokenProvider';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { buttonVariants } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { api } from '@/lib/api';
import type { Task, Workspace } from '@/lib/types';
import { cn } from '@/lib/utils';

export default function HomePage() {
  const { hasToken } = useAuthToken();
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!hasToken) {
      setLoading(false);
      return;
    }

    const run = async () => {
      setLoading(true);
      setError(null);
      try {
        const [nextWorkspaces, nextTasks] = await Promise.all([
          api.listWorkspaces(),
          api.listTasks(),
        ]);
        setWorkspaces(nextWorkspaces);
        setTasks(nextTasks);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error while loading dashboard');
      } finally {
        setLoading(false);
      }
    };

    void run();
  }, [hasToken]);

  const statusCounts = useMemo(() => {
    return tasks.reduce<Record<string, number>>((acc, task) => {
      acc[task.status] = (acc[task.status] ?? 0) + 1;
      return acc;
    }, {});
  }, [tasks]);

  if (!hasToken) {
    return (
      <Alert>
        <AlertTitle>Token Required</AlertTitle>
        <AlertDescription>
          Set the API token from the header to load data from the protected backend.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-stone-200 bg-white/80 p-6 shadow-sm">
        <h1 className="text-2xl font-semibold tracking-tight text-stone-900">Forge Dashboard</h1>
        <p className="mt-2 max-w-2xl text-sm text-stone-600">
          Monitor local autonomous runs, workspace health, approvals, and task progression in real time.
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <Link className={cn(buttonVariants())} href="/workspaces">
            Manage Workspaces
          </Link>
        </div>
      </section>

      {error ? (
        <Alert variant="destructive">
          <AlertTitle>Dashboard Load Failed</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {loading ? (
          Array.from({ length: 4 }).map((_, idx) => <Skeleton key={idx} className="h-28 rounded-xl" />)
        ) : (
          <>
            <StatCard title="Workspaces" value={String(workspaces.length)} />
            <StatCard title="Tasks" value={String(tasks.length)} />
            <StatCard title="Running" value={String(statusCounts.running ?? 0)} />
            <StatCard title="Awaiting Approval" value={String(statusCounts.awaiting_approval ?? 0)} />
          </>
        )}
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <Card className="border-stone-200 bg-white/90">
          <CardHeader>
            <CardTitle className="text-base">Recent Workspaces</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-stone-700">
            {workspaces.slice(0, 5).map((workspace) => (
              <div key={workspace.id} className="flex items-center justify-between rounded border border-stone-200 p-2">
                <span className="line-clamp-1">{workspace.name}</span>
                <Link
                  className={cn(buttonVariants({ variant: 'ghost', size: 'sm' }))}
                  href={`/workspaces/${workspace.id}`}
                >
                  Open
                </Link>
              </div>
            ))}
            {workspaces.length === 0 && !loading ? (
              <p className="text-sm text-stone-500">No workspaces created yet.</p>
            ) : null}
          </CardContent>
        </Card>

        <Card className="border-stone-200 bg-white/90">
          <CardHeader>
            <CardTitle className="text-base">Recent Tasks</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-stone-700">
            {tasks.slice(0, 5).map((task) => (
              <div key={task.id} className="flex items-center justify-between rounded border border-stone-200 p-2">
                <span className="line-clamp-1">{task.goal}</span>
                <Link
                  className={cn(buttonVariants({ variant: 'ghost', size: 'sm' }))}
                  href={`/workspaces/${task.workspace_id}/tasks/${task.id}`}
                >
                  Inspect
                </Link>
              </div>
            ))}
            {tasks.length === 0 && !loading ? <p className="text-sm text-stone-500">No tasks yet.</p> : null}
          </CardContent>
        </Card>
      </section>
    </div>
  );
}

function StatCard({ title, value }: { title: string; value: string }) {
  return (
    <Card className="border-stone-200 bg-white/90">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm text-stone-600">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-3xl font-semibold tracking-tight text-stone-900">{value}</p>
      </CardContent>
    </Card>
  );
}
