import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { TimelineEvent } from '@/lib/types';

interface TaskTimelineProps {
  events: TimelineEvent[];
}

export default function TaskTimeline({ events }: TaskTimelineProps) {
  return (
    <Card className="border-stone-200 bg-white/90">
      <CardHeader>
        <CardTitle className="text-base">Task Timeline</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {events.length === 0 ? (
          <p className="text-sm text-stone-500">No task events yet. Start streaming to populate timeline.</p>
        ) : (
          events.map((event) => (
            <div key={event.id} className="rounded-lg border border-stone-200 p-3">
              <div className="mb-2 flex items-center justify-between gap-2">
                <p className="text-sm font-medium text-stone-900">{event.title}</p>
                <Badge variant="secondary">{event.source}</Badge>
              </div>
              <p className="mb-2 text-xs text-stone-500">{new Date(event.createdAt).toLocaleString()}</p>
              <pre className="overflow-x-auto rounded bg-stone-100 p-2 text-xs text-stone-700">
                {event.details}
              </pre>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
