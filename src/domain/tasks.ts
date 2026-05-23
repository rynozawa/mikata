import type { FocusTask, Priority } from './types';

interface CreateTaskInput {
  id: string;
  title: string;
  description?: string;
  priority?: Priority;
  estimateMinutes: number;
}

export function createTask(input: CreateTaskInput): FocusTask {
  return {
    id: input.id,
    title: input.title.trim(),
    description: input.description?.trim() ?? '',
    priority: input.priority ?? 'medium',
    status: 'todo',
    estimateMinutes: input.estimateMinutes,
    isCurrent: false
  };
}

export function selectCurrentTask(tasks: FocusTask[], taskId: string): FocusTask[] {
  return tasks.map((task) => ({
    ...task,
    isCurrent: task.id === taskId,
    status: task.id === taskId ? 'doing' : task.status
  }));
}

export function getCurrentTask(tasks: FocusTask[]): FocusTask | undefined {
  return tasks.find((task) => task.isCurrent) ?? tasks.find((task) => task.status === 'doing');
}
