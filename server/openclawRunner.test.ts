import { describe, expect, it } from 'vitest';
import { buildOpenClawRunPlan, runDemoOpenClawJob } from './openclawRunner';
import { createOpenClawJob } from '../src/domain/openclaw';

describe('OpenClaw runner', () => {
  it('builds a safe real-mode execution plan scoped to the selected workspace', () => {
    const job = createOpenClawJob({
      id: 'job-1',
      taskId: 'task-1',
      prompt: 'フォームの文言を直して'
    });

    const plan = buildOpenClawRunPlan({
      job,
      workspacePath: '/tmp/demo-repo',
      realMode: true
    });

    expect(plan.cwd).toBe('/tmp/demo-repo');
    expect(plan.command[0]).toBe('openclaw');
    expect(plan.mode).toBe('real');
    expect(plan.command.join(' ')).toContain('pull request');
  });

  it('runs demo mode through coding, testing, commit, PR, and complete stages', async () => {
    const job = createOpenClawJob({
      id: 'job-2',
      taskId: 'task-2',
      prompt: 'READMEを改善して'
    });

    const states = await runDemoOpenClawJob(job, { delayMs: 0 });

    expect(states.map((state) => state.status)).toEqual([
      'working',
      'testing',
      'committing',
      'creating_pr',
      'complete'
    ]);
    expect(states.at(-1)?.logs.at(-1)?.message).toContain('demo pull request');
  });
});
