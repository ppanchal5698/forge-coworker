import Link from 'next/link';

import { Badge } from '@/components/ui/badge';
import { Button, buttonVariants } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import type { Workspace } from '@/lib/types';
import { cn } from '@/lib/utils';

interface WorkspaceCardProps {
  workspace: Workspace;
  taskCount: number;
  onDelete: (workspaceId: string) => Promise<void> | void;
}

export default function WorkspaceCard({ workspace, taskCount, onDelete }: WorkspaceCardProps) {
  return (
    <Card className="border-stone-200 bg-white/90 shadow-sm">
      <CardHeader className="space-y-3">
        <div className="flex items-start justify-between gap-3">
          <CardTitle className="line-clamp-2 text-lg font-semibold text-stone-900">
            {workspace.name}
          </CardTitle>
          <Badge variant="secondary">{taskCount} task(s)</Badge>
        </div>
        <p className="line-clamp-1 text-xs text-stone-500">{workspace.path}</p>
      </CardHeader>
      <CardContent className="space-y-3 text-sm text-stone-700">
        <p className="line-clamp-3">
          {workspace.custom_instructions || 'No workspace-specific instructions provided.'}
        </p>
        <p className="text-xs text-stone-500">
          Updated: {new Date(workspace.updated_at).toLocaleString()}
        </p>
      </CardContent>
      <CardFooter className="flex items-center justify-between gap-2">
        <Link className={cn(buttonVariants({ size: 'sm' }))} href={`/workspaces/${workspace.id}`}>
          Open Workspace
        </Link>
        <Button variant="outline" size="sm" onClick={() => onDelete(workspace.id)}>
          Delete
        </Button>
      </CardFooter>
    </Card>
  );
}
