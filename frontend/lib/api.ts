import type {
  Approval,
  ApprovalDecision,
  Task,
  TaskCreateInput,
  Workspace,
  WorkspaceCreateInput,
} from '@/lib/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export const API_TOKEN_KEY = 'forge_api_bearer_token';

let inMemoryToken: string | null = null;

function getToken(): string | null {
  if (inMemoryToken) {
    return inMemoryToken;
  }

  if (typeof window === 'undefined') {
    return null;
  }

  return window.localStorage.getItem(API_TOKEN_KEY);
}

export function setApiToken(token: string) {
  inMemoryToken = token;
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(API_TOKEN_KEY, token);
  }
}

export function clearApiToken() {
  inMemoryToken = null;
  if (typeof window !== 'undefined') {
    window.localStorage.removeItem(API_TOKEN_KEY);
  }
}

export function loadApiToken(): string | null {
  const token = getToken();
  if (token) {
    inMemoryToken = token;
  }
  return token;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers || {}),
    },
    cache: 'no-store',
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`API request failed (${response.status}): ${text}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export const api = {
  baseUrl: API_BASE,
  createWorkspace: (input: WorkspaceCreateInput) =>
    request<Workspace>('/workspaces', {
      method: 'POST',
      body: JSON.stringify({
        name: input.name,
        custom_instructions: input.custom_instructions ?? null,
      }),
    }),
  listWorkspaces: () => request<Workspace[]>('/workspaces'),
  getWorkspace: (workspaceId: string) => request<Workspace>(`/workspaces/${workspaceId}`),
  deleteWorkspace: (workspaceId: string) =>
    request<void>(`/workspaces/${workspaceId}`, {
      method: 'DELETE',
    }),
  listTasks: (workspaceId?: string) =>
    request<Task[]>(workspaceId ? `/tasks?workspace_id=${workspaceId}` : '/tasks'),
  createTask: (input: TaskCreateInput) =>
    request<Task>('/tasks', {
      method: 'POST',
      body: JSON.stringify(input),
    }),
  getTask: (taskId: string) => request<Task>(`/tasks/${taskId}`),
  resolveApproval: (approvalId: string, decision: ApprovalDecision, operatorNote?: string) =>
    request<Approval>(`/approvals/${approvalId}/resolve`, {
      method: 'POST',
      body: JSON.stringify({ decision, operator_note: operatorNote ?? null }),
    }),
};
