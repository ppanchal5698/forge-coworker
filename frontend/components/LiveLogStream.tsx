'use client';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useTaskStream } from '@/hooks/useTaskStream';

interface LiveLogStreamProps {
  taskId: string;
}

export default function LiveLogStream({ taskId }: LiveLogStreamProps) {
  const { events, sseEvents, isConnected, error } = useTaskStream(taskId);

  return (
    <Card aria-live="polite" className="border-stone-200 bg-white/90">
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle className="text-base">Live Log Stream</CardTitle>
        <Badge variant={isConnected ? 'default' : 'secondary'}>
          {isConnected ? 'connected' : 'disconnected'}
        </Badge>
      </CardHeader>
      <CardContent className="space-y-3">
        {error ? (
          <p role="alert" className="text-sm text-red-600">
            {error}
          </p>
        ) : null}

        <div className="max-h-[400px] space-y-2 overflow-y-auto pr-1">
          {events.map((event) => (
            <div key={event.id} className="rounded border border-stone-200 p-2">
              <p className="mb-1 text-xs font-semibold uppercase text-stone-600">{event.event_type}</p>
              <pre className="overflow-x-auto rounded bg-stone-100 p-2 text-xs text-stone-800">
                {JSON.stringify(event.payload, null, 2)}
              </pre>
            </div>
          ))}

          {sseEvents.map((event, idx) => (
            <div key={`${taskId}-sse-${idx}`} className="rounded border border-stone-200 p-2">
              <p className="mb-1 text-xs font-semibold uppercase text-stone-600">
                {Array.isArray(event.next) ? event.next.join(' -> ') : event.next || 'sse-event'}
              </p>
              <pre className="overflow-x-auto rounded bg-stone-100 p-2 text-xs text-stone-800">
                {JSON.stringify(event, null, 2)}
              </pre>
            </div>
          ))}

          {events.length === 0 && sseEvents.length === 0 ? (
            <p className="text-sm text-stone-500">Waiting for streamed task events...</p>
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
}
