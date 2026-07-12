"use client";

import { useState } from 'react';

import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';

interface ApprovalModalProps {
  open: boolean;
  approvalId: string | null;
  actionDescription: string;
  onResolve: (decision: 'approved' | 'rejected', note: string) => Promise<void>;
}

export default function ApprovalModal({
  open,
  approvalId,
  actionDescription,
  onResolve,
}: ApprovalModalProps) {
  const [operatorNote, setOperatorNote] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleResolve = async (decision: 'approved' | 'rejected') => {
    if (!approvalId) {
      return;
    }
    setSubmitting(true);
    try {
      await onResolve(decision, operatorNote);
      setOperatorNote('');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Human Approval Required</DialogTitle>
          <DialogDescription>
            This task requested approval for a potentially destructive action.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <p className="rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
            {actionDescription || 'Action description unavailable from event payload.'}
          </p>
          <div className="grid gap-2">
            <Label htmlFor="approval-note">Operator note (optional)</Label>
            <Textarea
              id="approval-note"
              value={operatorNote}
              onChange={(event) => setOperatorNote(event.target.value)}
              placeholder="Add audit context for this decision"
            />
          </div>
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            variant="destructive"
            disabled={!approvalId || submitting}
            onClick={() => handleResolve('rejected')}
          >
            Reject
          </Button>
          <Button disabled={!approvalId || submitting} onClick={() => handleResolve('approved')}>
            Approve and Resume
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
