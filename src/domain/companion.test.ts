import { describe, expect, it } from 'vitest';
import { deriveCompanionState } from './companion';
import { createTask } from './tasks';

describe('companion state', () => {
  it('nudges gently when the user is idle during a current task', () => {
    const currentTask = createTask({
      id: 'task-1',
      title: 'OpenClaw連携を作る',
      estimateMinutes: 30
    });
    currentTask.isCurrent = true;

    const state = deriveCompanionState({
      currentTask,
      activityState: 'idle',
      openClawStatus: 'queued',
      recentUserMessage: 'ちょっと止まった'
    });

    expect(state.mode).toBe('nudge');
    expect(state.message).toContain('OpenClaw連携を作る');
    expect(state.mood).toBe('concerned');
  });

  it('keeps cheering after OpenClaw completes without pretending it is still running', () => {
    const state = deriveCompanionState({
      currentTask: createTask({ id: 'task-2', title: 'PRを確認する', estimateMinutes: 15 }),
      activityState: 'focused',
      openClawStatus: 'complete',
      recentUserMessage: '終わった？'
    });

    expect(state.mode).toBe('cheer');
    expect(state.message).toContain('OpenClawの作業は完了');
    expect(state.motion).toBe('organizing');
  });

  it('still nudges if the user goes idle after OpenClaw has completed', () => {
    const state = deriveCompanionState({
      currentTask: createTask({ id: 'task-4', title: 'PRを確認する', estimateMinutes: 15 }),
      activityState: 'idle',
      openClawStatus: 'complete'
    });

    expect(state.mode).toBe('nudge');
    expect(state.message).toContain('PRを確認する');
  });

  it('responds to recent anxious context with a softer concerned tone', () => {
    const state = deriveCompanionState({
      currentTask: createTask({ id: 'task-3', title: 'テストを書く', estimateMinutes: 15 }),
      activityState: 'focused',
      openClawStatus: 'queued',
      recentUserMessage: 'ちょっと不安で止まりそう'
    });

    expect(state.mood).toBe('concerned');
    expect(state.message).toContain('不安');
  });
});
