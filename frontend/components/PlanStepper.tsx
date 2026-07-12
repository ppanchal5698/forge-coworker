import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { TaskStatus } from '@/lib/types';
import { cn } from '@/lib/utils';

interface PlanStepperProps {
  status: TaskStatus;
  activeNode?: string;
}

const STEPS = ['pending', 'running', 'awaiting_approval', 'completed'] as const;

function getStepState(step: (typeof STEPS)[number], status: TaskStatus) {
  if (status === 'failed' || status === 'cancelled') {
    return step === 'running' ? 'failed' : 'idle';
  }

  const currentIndex = STEPS.indexOf(status === 'awaiting_approval' ? 'awaiting_approval' : status);
  const stepIndex = STEPS.indexOf(step);

  if (stepIndex < currentIndex) return 'done';
  if (stepIndex === currentIndex) return 'active';
  return 'idle';
}

export default function PlanStepper({ status, activeNode }: PlanStepperProps) {
  return (
    <Card className="border-stone-200 bg-white/90">
      <CardHeader>
        <CardTitle className="text-base">Execution Plan</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {STEPS.map((step) => {
          const state = getStepState(step, status);
          return (
            <div key={step} className="flex items-center justify-between rounded-lg border border-stone-200 px-3 py-2">
              <span className="text-sm capitalize text-stone-700">{step.replace('_', ' ')}</span>
              <Badge
                variant={state === 'active' ? 'default' : 'secondary'}
                className={cn(
                  state === 'done' && 'bg-emerald-100 text-emerald-700',
                  state === 'failed' && 'bg-red-100 text-red-700'
                )}
              >
                {state}
              </Badge>
            </div>
          );
        })}
        {activeNode ? (
          <p className="text-xs text-stone-500">Current graph node: {activeNode}</p>
        ) : null}
      </CardContent>
    </Card>
  );
}
