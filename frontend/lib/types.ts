export type TaskStatus =
  | 'pending'
  | 'running'
  | 'awaiting_approval'
  | 'completed'
  | 'failed'
  | 'cancelled';

export type ApprovalDecision = 'pending' | 'approved' | 'rejected';

export interface Workspace {
  id: string;
  name: string;
  path: string;
  custom_instructions: string | null;
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: string;
  workspace_id: string;
  goal: string;
  status: TaskStatus;
  thread_id: string;
  created_at: string;
  updated_at: string;
}

export interface Approval {
  id: string;
  task_id: string;
  action_description: string;
  decision: ApprovalDecision;
  operator_note: string | null;
  created_at: string;
  resolved_at: string | null;
}

export interface WorkspaceCreateInput {
  name: string;
  custom_instructions?: string | null;
}

export interface TaskCreateInput {
  workspace_id: string;
  goal: string;
}

export interface TaskEvent {
  id: string;
  task_id: string;
  event_type: string;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface StreamMessage {
  next?: string | string[] | null;
  messages?: Array<{ type: string; content: string }>;
  error?: string;
  message?: string;
}

export interface TimelineEvent {
  id: string;
  title: string;
  details: string;
  createdAt: string;
  source: 'realtime' | 'sse';
}
