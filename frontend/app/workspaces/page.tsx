"use client";

import { useEffect, useMemo, useState } from 'react';

import { useAuthToken } from '@/components/AuthTokenProvider';
import WorkspaceCard from '@/components/WorkspaceCard';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { api } from '@/lib/api';
import type { Task, Workspace } from '@/lib/types';

export default function WorkspacesPage() {
  const { hasToken } = useAuthToken();
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [name, setName] = useState('');
  const [customInstructions, setCustomInstructions] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [workspaceRows, taskRows] = await Promise.all([api.listWorkspaces(), api.listTasks()]);
      setWorkspaces(workspaceRows);
      setTasks(taskRows);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load workspaces');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!hasToken) {
      setLoading(false);
      return;
    }
    void load();
  }, [hasToken]);

  const tasksByWorkspace = useMemo(() => {
    return tasks.reduce<Record<string, number>>((acc, task) => {
      acc[task.workspace_id] = (acc[task.workspace_id] ?? 0) + 1;
      return acc;
    }, {});
  }, [tasks]);

  const onCreateWorkspace = async () => {
    if (!name.trim()) {
      setError('Workspace name is required');
      return;
    }

    setSaving(true);
    setError(null);
    try {
      await api.createWorkspace({
        name: name.trim(),
        custom_instructions: customInstructions.trim() || null,
      });
      setName('');
      setCustomInstructions('');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Workspace creation failed');
    } finally {
      setSaving(false);
    }
  };

  const onDeleteWorkspace = async (workspaceId: string) => {
    setError(null);
    try {
      await api.deleteWorkspace(workspaceId);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Workspace deletion failed');
    }
  };

  if (!hasToken) {
    return (
      <Alert>
        <AlertTitle>Token Required</AlertTitle>
        <AlertDescription>
          Set API token from the top bar before creating or listing workspaces.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-stone-900">Workspaces</h1>
        <p className="mt-1 text-sm text-stone-600">Manage isolated workspace directories and instructions.</p>
      </div>

      {error ? (
        <Alert variant="destructive">
          <AlertTitle>Request Failed</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      <Card className="border-stone-200 bg-white/90">
        <CardHeader>
          <CardTitle className="text-base">Create Workspace</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <div className="grid gap-2">
            <Label htmlFor="workspace-name">Name</Label>
            <Input
              id="workspace-name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Agent experiments"
            />
          </div>
          <div className="grid gap-2 md:col-span-2">
            <Label htmlFor="workspace-instructions">Custom instructions</Label>
            <Textarea
              id="workspace-instructions"
              value={customInstructions}
              onChange={(event) => setCustomInstructions(event.target.value)}
              placeholder="Optional: workspace-specific coding guidelines"
            />
          </div>
          <Button onClick={onCreateWorkspace} disabled={saving} className="w-fit">
            {saving ? 'Creating...' : 'Create Workspace'}
          </Button>
        </CardContent>
      </Card>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {!loading && workspaces.length === 0 ? (
          <p className="text-sm text-stone-500">No workspaces available yet.</p>
        ) : null}
        {workspaces.map((workspace) => (
          <WorkspaceCard
            key={workspace.id}
            workspace={workspace}
            taskCount={tasksByWorkspace[workspace.id] ?? 0}
            onDelete={onDeleteWorkspace}
          />
        ))}
      </section>
    </div>
  );
}
