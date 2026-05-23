import { describe, expect, it } from 'vitest';
import { classifyActivity } from './activity';

describe('metadata-only activity classification', () => {
  it('classifies long inactivity as idle without inspecting keystrokes or screen content', () => {
    const result = classifyActivity({
      activeAppName: 'Visual Studio Code',
      idleSeconds: 720,
      expectedAppNames: ['Visual Studio Code'],
      idleThresholdSeconds: 300
    });

    expect(result).toEqual({
      state: 'idle',
      reason: 'No activity for 12 minutes'
    });
  });

  it('classifies a non-matching active app as off task', () => {
    const result = classifyActivity({
      activeAppName: 'YouTube',
      idleSeconds: 12,
      expectedAppNames: ['Visual Studio Code', 'Terminal'],
      idleThresholdSeconds: 300
    });

    expect(result.state).toBe('off_task');
    expect(result.reason).toContain('YouTube');
  });
});
