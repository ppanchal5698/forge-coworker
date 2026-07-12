"use client";

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';

import ApprovalModal from '@/components/ApprovalModal';
import LiveLogStream from '@/components/LiveLogStream';
import PlanStepper from '@/components/PlanStepper';
import TaskTimeline from '@/components/TaskTimeline';
import { useAuthToken } from '@/components/AuthTokenProvider';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button, buttonVariants } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { api } from '@/lib/api';
import { useTaskStream } from '@/hooks/useTaskStream';
import type { Task, TimelineEvent } from '@/lib/types';
import { cn } from '@/lib/utils';

export default function TaskDetailPage() {
  const { hasToken } = useAuthToken();
  const params = useParams<{ workspaceId: string; taskId: string }>();
  const workspaceId = params.workspaceId;
  const taskId = params.taskId;

  const [task, setTask] = useState<Task | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshTick, setRefreshTick] = useState(0);

  const { events, sseEvents } = useTaskStream(taskId);

  useEffect(() => {
    if (!hasToken || !taskId) {
      return;
    }

    const loadTask = async () => {
      try {
        const row = await api.getTask(taskId);
        setTask(row);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load task');
      }
    };

    void loadTask();
  }, [hasToken, taskId, refreshTick]);

  const approvalContext = useMemo(() => {
    const realtimeApprovalEvent = [...events]
      .reverse()
      .find((event) => event.event_type.toLowerCase().includes('approval'));

    if (!realtimeApprovalEvent) {
      return { approvalId: null, actionDescription: '' };
    }

    const approvalId =
      typeof realtimeApprovalEvent.payload.approval_id === 'string'
        ? realtimeApprovalEvent.payload.approval_id
        : null;
    const actionDescription =
      typeof realtimeApprovalEvent.payload.action_description === 'string'
        ? realtimeApprovalEvent.payload.action_description
        : 'Approval requested by graph';

    return { approvalId, actionDescription };
  }, [events]);

  const latestNextNode = useMemo(() => {
    const lastSse = sseEvents[sseEvents.length - 1];
    if (!lastSse) {
      return undefined;
    }
    if (Array.isArray(lastSse.next)) {
      return lastSse.next.join(' -> ');
    }
    return lastSse.next || undefined;
  }, [sseEvents]);

  const timelineEvents = useMemo<TimelineEvent[]>(() => {
    const realtimeItems = events.map((event) => ({
      id: event.id,
      title: event.event_type,
      details: JSON.stringify(event.payload, null, 2),
      createdAt: event.created_at,
      source: 'realtime' as const,
    }));

    const sseItems = sseEvents.map((event, idx) => ({
      id: `${taskId}-sse-${idx}`,
      title: Array.isArray(event.next) ? event.next.join(' -> ') : event.next || 'sse event',
      details: JSON.stringify(event, null, 2),
      createdAt: new Date().toISOString(),
      source: 'sse' as const,
    }));

    return [...realtimeItems, ...sseItems].slice(-200);
  }, [events, sseEvents, taskId]);

  const handleResolveApproval = async (decision: 'approved' | 'rejected', note: string) => {
    if (!approvalContext.approvalId) {
      setError('Approval ID missing in event payload; cannot resolve from UI.');
      return;
    }
    try {
      await api.resolveApproval(approvalContext.approvalId, decision, note);
      setRefreshTick((prev) => prev + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Approval resolution failed');
    }
  };

  if (!hasToken) {
    return (
      <Alert>
        <AlertTitle>Token Required</AlertTitle>
        <AlertDescription>Set API token before opening task details.</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {error ? (
        <Alert variant="destructive">
          <AlertTitle>Task Request Failed</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      <Card className="border-stone-200 bg-white/90">
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <CardTitle className="text-lg">Task Detail</CardTitle>
          <Link
            className={cn(buttonVariants({ variant: 'outline', size: 'sm' }))}
            href={`/workspaces/${workspaceId}`}
          >
            Back to Workspace
          </Link>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-stone-700">
          <p>{task?.goal || 'Loading task...'}</p>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary">{task?.status || 'unknown'}</Badge>
            {task?.thread_id ? <Badge variant="outline">thread: {task.thread_id}</Badge> : null}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-3">
        <div className="space-y-4 xl:col-span-2">
          {task ? <PlanStepper status={task.status} activeNode={latestNextNode} /> : null}
          <TaskTimeline events={timelineEvents} />
        </div>
        <LiveLogStream taskId={taskId} />
      </div>

      <ApprovalModal
        open={task?.status === 'awaiting_approval'}
        approvalId={approvalContext.approvalId}
        actionDescription={approvalContext.actionDescription}
        onResolve={handleResolveApproval}
      />
    </div>
  );
}
