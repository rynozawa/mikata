import { createRequire } from 'node:module';
import { describe, expect, it } from 'vitest';

const require = createRequire(import.meta.url);
const { buildDashboardWindowOptions, buildCompanionWindowOptions, revealWindow } = require('./windowConfig.cjs');

describe('Electron window visibility helpers', () => {
  it('creates windows hidden first so they can be explicitly revealed after load', () => {
    expect(buildDashboardWindowOptions()).toMatchObject({
      show: false,
      width: 1280,
      height: 860
    });
    expect(buildCompanionWindowOptions({ x: 100, y: 200 })).toMatchObject({
      show: false,
      alwaysOnTop: true,
      frame: false,
      x: 100,
      y: 200
    });
  });

  it('reveals and raises a window when ready', () => {
    const calls: string[] = [];
    const fakeWindow = {
      isMinimized: () => true,
      restore: () => calls.push('restore'),
      show: () => calls.push('show'),
      moveTop: () => calls.push('moveTop'),
      focus: () => calls.push('focus')
    };

    revealWindow(fakeWindow, { focus: true });

    expect(calls).toEqual(['restore', 'show', 'moveTop', 'focus']);
  });
});
