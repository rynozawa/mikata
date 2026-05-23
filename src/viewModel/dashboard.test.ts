import { describe, expect, it } from 'vitest';
import { buildDashboardSummary } from './dashboard';
import { deriveCompanionState } from '../domain/companion';
import { createOpenClawJob, advanceOpenClawJob } from '../domain/openclaw';
import { createTask, selectCurrentTask } from '../domain/tasks';

describe('dashboard summary', () => {
  it('summarizes the current task, OpenClaw progress, privacy stance, and companion line', () => {
    const tasks = selectCurrentTask(
      [
        createTask({ id: 'task-1', title: 'AIペットを動かす', priority: 'high', estimateMinutes: 30 })
      ],
      'task-1'
    );
    const openClawJob = advanceOpenClawJob(
      createOpenClawJob({ id: 'job-1', taskId: 'task-1', prompt: 'UIを実装して' }),
      { status: 'creating_pr', message: 'PRを作っています' }
    );
    const companion = deriveCompanionState({
      currentTask: tasks[0],
      activityState: 'focused',
      openClawStatus: openClawJob.status
    });

    const summary = buildDashboardSummary({
      tasks,
      jobs: [openClawJob],
      latestActivity: { state: 'focused', reason: 'Visual Studio Code matches the current focus' },
      gitStatus: { branch: 'main', dirtyCount: 2, lastCommit: 'No commits yet' },
      companion
    });

    expect(summary.currentTaskTitle).toBe('AIペットを動かす');
    expect(summary.openClawLabel).toBe('PR作成中');
    expect(summary.privacyLabel).toBe('メタ情報のみ');
    expect(summary.companionLine).toContain('成果をまとめている');
  });
});
