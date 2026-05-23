import type { ActivityState, CompanionState, FocusTask, OpenClawJobStatus } from './types';

interface DeriveCompanionInput {
  currentTask?: FocusTask;
  activityState: ActivityState;
  openClawStatus?: OpenClawJobStatus;
  recentUserMessage?: string;
}

const DEFAULT_TASK_NAME = '今やる1つ';

export function deriveCompanionState(input: DeriveCompanionInput): CompanionState {
  const taskName = input.currentTask?.title || DEFAULT_TASK_NAME;
  const recentContext = input.recentUserMessage ?? '';

  if (hasAnxiousSignal(recentContext) && input.openClawStatus !== 'complete') {
    return {
      mode: 'nudge',
      mood: 'concerned',
      motion: 'breathing',
      message: `不安がある時は、${taskName}を1分だけに小さくしよう。私は横で一緒に進めるよ。`
    };
  }

  if (input.openClawStatus === 'failed') {
    return {
      mode: 'recover',
      mood: 'concerned',
      motion: 'resetting',
      message: `OpenClawが止まったみたい。${taskName}に戻れるよう、ログを一緒に見よう。`
    };
  }

  if (input.activityState === 'idle') {
    return {
      mode: 'nudge',
      mood: 'concerned',
      motion: 'breathing',
      message: `${taskName}に戻る小さな一歩だけやってみよう。私も横で待ってるよ。`
    };
  }

  if (input.activityState === 'off_task') {
    return {
      mode: 'nudge',
      mood: 'concerned',
      motion: 'breathing',
      message: `今は${taskName}の時間かも。戻るなら、次の1分だけ一緒にやろう。`
    };
  }

  if (input.openClawStatus === 'complete') {
    return {
      mode: 'cheer',
      mood: 'proud',
      motion: 'organizing',
      message: `OpenClawの作業は完了。私は次の準備を整えながら、${taskName}を一緒に見守ってるよ。`
    };
  }

  if (input.openClawStatus === 'committing' || input.openClawStatus === 'creating_pr') {
    return {
      mode: 'shipping',
      mood: 'determined',
      motion: 'shipping',
      message: `OpenClawが成果をまとめているよ。${taskName}もあと少しで形になる。`
    };
  }

  if (input.openClawStatus === 'working' || input.openClawStatus === 'testing') {
    return {
      mode: 'working',
      mood: 'determined',
      motion: 'typing',
      message: `私もOpenClawと一緒に作業中。${taskName}を少しずつ進めよう。`
    };
  }

  return {
    mode: 'focus',
    mood: 'calm',
    motion: 'breathing',
    message: `${taskName}、いい感じ。私はここで一緒に集中してる。`
  };
}

function hasAnxiousSignal(message: string): boolean {
  return ['不安', '止まり', '無理', 'しんど', 'こわ', '怖'].some((word) => message.includes(word));
}
