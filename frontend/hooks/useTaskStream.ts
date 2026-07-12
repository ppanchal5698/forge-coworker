'use client';

import { useEffect, useMemo, useState } from 'react';

import type { StreamMessage, TaskEvent } from '@/lib/types';
import { useSupabaseRealtime } from '@/hooks/useSupabaseRealtime';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const STREAM_SOURCE = process.env.NEXT_PUBLIC_TASK_STREAM_SOURCE || 'supabase';

interface UseTaskStreamResult {
  events: TaskEvent[];
  sseEvents: StreamMessage[];
  isConnected: boolean;
  error: string | null;
}

export function useTaskStream(taskId: string): UseTaskStreamResult {
  const [sseEvents, setSseEvents] = useState<StreamMessage[]>([]);
  const [sseConnected, setSseConnected] = useState(false);
  const [sseError, setSseError] = useState<string | null>(null);

  const useSupabaseSource = useMemo(() => STREAM_SOURCE === 'supabase', []);

  const realtime = useSupabaseRealtime<TaskEvent>(`task-${taskId}`, {
    table: 'task_events',
    event: 'INSERT',
    filter: `task_id=eq.${taskId}`,
    enabled: useSupabaseSource,
    maxItems: 200,
  });

  const shouldUseSseFallback =
    !useSupabaseSource ||
    (!!realtime.error && realtime.error.toLowerCase().includes('supabase')) ||
    (!!realtime.error && !realtime.isConnected);

  useEffect(() => {
    if (!taskId || !shouldUseSseFallback) {
      return;
    }

    const eventSource = new EventSource(`${API_BASE}/tasks/${taskId}/stream`);

    eventSource.onopen = () => {
      setSseConnected(true);
      setSseError(null);
    };

    eventSource.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data) as StreamMessage;
        setSseEvents((prev) => {
          const next = [...prev, parsed];
          return next.slice(Math.max(next.length - 200, 0));
        });
      } catch {
        setSseError('Failed to parse SSE stream payload.');
      }
    };

    eventSource.onerror = () => {
      setSseConnected(false);
      setSseError('SSE stream disconnected.');
    };

    return () => {
      eventSource.close();
      setSseConnected(false);
    };
  }, [taskId, shouldUseSseFallback]);

  if (useSupabaseSource) {
    return {
      events: realtime.data,
      sseEvents,
      isConnected: realtime.isConnected || sseConnected,
      error: realtime.error ?? sseError,
    };
  }

  return {
    events: [],
    sseEvents,
    isConnected: sseConnected,
    error: sseError,
  };
}
