import { describe, expect, it } from 'vitest';
import { createTask, selectCurrentTask } from './tasks';
import type { FocusTask } from './types';

describe('task focus selection', () => {
  it('creates a todo task with a stable title and default medium priority', () => {
    const task = createTask({
      id: 'task-1',
      title: 'PR説明を整える',
      estimateMinutes: 25
    });

    expect(task).toMatchObject({
      id: 'task-1',
      title: 'PR説明を整える',
      priority: 'medium',
      status: 'todo',
      estimateMinutes: 25,
      isCurrent: false
    });
  });

  it('marks only one task as the current focus task', () => {
    const tasks: FocusTask[] = [
      createTask({ id: 'a', title: 'UIを作る', priority: 'high', estimateMinutes: 40 }),
      createTask({ id: 'b', title: 'OpenClaw連携', priority: 'medium', estimateMinutes: 30 })
    ];

    const updated = selectCurrentTask(tasks, 'b');

    expect(updated.find((task) => task.id === 'a')?.isCurrent).toBe(false);
    expect(updated.find((task) => task.id === 'b')).toMatchObject({
      isCurrent: true,
      status: 'doing'
    });
  });
});
