export type Priority = 'low' | 'medium' | 'high';

export type TaskStatus = 'todo' | 'doing' | 'done';

export interface FocusTask {
  id: string;
  title: string;
  description: string;
  priority: Priority;
  status: TaskStatus;
  estimateMinutes: number;
  isCurrent: boolean;
}

export type ActivityState = 'focused' | 'idle' | 'off_task';

export interface ActivityClassification {
  state: ActivityState;
  reason: string;
}

export type OpenClawJobStatus =
  | 'queued'
  | 'working'
  | 'testing'
  | 'committing'
  | 'creating_pr'
  | 'complete'
  | 'failed';

export interface OpenClawLogEntry {
  at: string;
  status: OpenClawJobStatus;
  message: string;
}

export interface OpenClawJob {
  id: string;
  taskId: string;
  prompt: string;
  status: OpenClawJobStatus;
  logs: OpenClawLogEntry[];
}

export type CompanionMode = 'focus' | 'nudge' | 'working' | 'shipping' | 'cheer' | 'recover';

export type CompanionMood = 'calm' | 'concerned' | 'determined' | 'proud';

export type CompanionMotion = 'breathing' | 'typing' | 'shipping' | 'organizing' | 'resetting';

export interface CompanionState {
  mode: CompanionMode;
  mood: CompanionMood;
  motion: CompanionMotion;
  message: string;
}

export interface GitMetadata {
  branch: string;
  dirtyCount: number;
  lastCommit: string;
}
