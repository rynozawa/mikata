import { describe, expect, it } from 'vitest';
import { advanceOpenClawJob, createOpenClawJob, getOpenClawCommand } from './openclaw';

describe('OpenClaw job state', () => {
  it('creates a queued coding job with a commit-and-PR instruction', () => {
    const job = createOpenClawJob({
      id: 'job-1',
      taskId: 'task-1',
      prompt: 'READMEを改善して'
    });

    expect(job.status).toBe('queued');
    expect(job.prompt).toContain('READMEを改善して');
    expect(getOpenClawCommand(job).join(' ')).toContain('commit');
    expect(getOpenClawCommand(job).join(' ')).toContain('pull request');
  });

  it('advances through work, test, commit, PR, and complete states with logs', () => {
    const job = createOpenClawJob({
      id: 'job-2',
      taskId: 'task-1',
      prompt: 'テストを追加して'
    });

    const complete = ['working', 'testing', 'committing', 'creating_pr', 'complete'].reduce(
      (current, status) =>
        advanceOpenClawJob(current, {
          status: status as Parameters<typeof advanceOpenClawJob>[1]['status'],
          message: `${status} stage`
        }),
      job
    );

    expect(complete.status).toBe('complete');
    expect(complete.logs.map((log) => log.message)).toContain('creating_pr stage');
  });
});
