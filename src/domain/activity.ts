import type { ActivityClassification } from './types';

interface ActivityInput {
  activeAppName: string;
  idleSeconds: number;
  expectedAppNames: string[];
  idleThresholdSeconds: number;
}

export function classifyActivity(input: ActivityInput): ActivityClassification {
  if (input.idleSeconds >= input.idleThresholdSeconds) {
    const minutes = Math.round(input.idleSeconds / 60);
    return {
      state: 'idle',
      reason: `No activity for ${minutes} minutes`
    };
  }

  const activeAppName = input.activeAppName.toLowerCase();
  const isExpected = input.expectedAppNames.some((name) => activeAppName.includes(name.toLowerCase()));

  if (!isExpected) {
    return {
      state: 'off_task',
      reason: `${input.activeAppName} is not part of the current focus apps`
    };
  }

  return {
    state: 'focused',
    reason: `${input.activeAppName} matches the current focus`
  };
}
