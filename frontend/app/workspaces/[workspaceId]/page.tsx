"use client";

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';

import { useAuthToken } from '@/components/AuthTokenProvider';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button, buttonVariants } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { api } from '@/lib/api';
import type { Task, Workspace } from '@/lib/types';
import { cn } from '@/lib/utils';

export default function WorkspaceDetailPage() {
  const { hasToken } = useAuthToken();
  const params = useParams<{ workspaceId: string }>();
  const workspaceId = params.workspaceId;

  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [goal, setGoal] = useState('');
  const [loading, setLoading] = useState(true);
  const [creatingTask, setCreatingTask] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [workspaceRow, taskRows] = await Promise.all([
        api.getWorkspace(workspaceId),
        api.listTasks(workspaceId),
      ]);
      setWorkspace(workspaceRow);
      setTasks(taskRows);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load workspace details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!hasToken) {
      setLoading(false);
      return;
    }
    if (!workspaceId) {
      return;
    }
    void load();
  }, [hasToken, workspaceId]);

  const onCreateTask = async () => {
    if (!goal.trim()) {
      setError('Task goal is required');
      return;
    }
    setCreatingTask(true);
    setError(null);
    try {
      await api.createTask({ workspace_id: workspaceId, goal: goal.trim() });
      setGoal('');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Task creation failed');
    } finally {
      setCreatingTask(false);
    }
  };

  if (!hasToken) {
    return (
      <Alert>
        <AlertTitle>Token Required</AlertTitle>
        <AlertDescription>Set API token to view this workspace.</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {error ? (
        <Alert variant="destructive">
          <AlertTitle>Request Failed</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      <Card className="border-stone-200 bg-white/90">
        <CardHeader>
          <CardTitle className="text-xl">{workspace?.name || 'Workspace'}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-stone-700">
          {loading ? <p>Loading workspace...</p> : null}
          {workspace ? (
            <>
              <p className="text-xs text-stone-500">{workspace.path}</p>
              <p>{workspace.custom_instructions || 'No custom instructions.'}</p>
              <p className="text-xs text-stone-500">
                Updated: {new Date(workspace.updated_at).toLocaleString()}
              </p>
            </>
          ) : null}
        </CardContent>
      </Card>

      <Card className="border-stone-200 bg-white/90">
        <CardHeader>
          <CardTitle className="text-base">Create Task</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid gap-2">
            <Label htmlFor="task-goal">Goal</Label>
            <Input
              id="task-goal"
              value={goal}
              onChange={(event) => setGoal(event.target.value)}
              placeholder="Implement endpoint contract checks"
            />
          </div>
          <Button onClick={onCreateTask} disabled={creatingTask}>
            {creatingTask ? 'Submitting...' : 'Create Task'}
          </Button>
        </CardContent>
      </Card>

      <Card className="border-stone-200 bg-white/90">
        <CardHeader>
          <CardTitle className="text-base">Tasks</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {tasks.length === 0 ? <p className="text-sm text-stone-500">No tasks created yet.</p> : null}
          {tasks.map((task) => (
            <div key={task.id} className="flex flex-wrap items-center justify-between gap-3 rounded border border-stone-200 p-3">
              <div className="space-y-1">
                <p className="text-sm font-medium text-stone-900">{task.goal}</p>
                <p className="text-xs text-stone-500">{new Date(task.created_at).toLocaleString()}</p>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="secondary">{task.status}</Badge>
                <Link
                  className={cn(buttonVariants({ variant: 'outline', size: 'sm' }))}
                  href={`/workspaces/${workspaceId}/tasks/${task.id}`}
                >
                  Open
                </Link>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
