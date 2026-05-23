import { describe, expect, it } from 'vitest';
import { parseGitStatus } from './git';

describe('git status parser', () => {
  it('extracts branch, dirty count, and last commit from metadata text', () => {
    const status = parseGitStatus({
      statusText: '## feat/openclaw...origin/feat/openclaw\n M src/App.tsx\n?? README.md\n',
      lastCommitText: 'abc1234 add companion shell'
    });

    expect(status).toEqual({
      branch: 'feat/openclaw',
      dirtyCount: 2,
      lastCommit: 'abc1234 add companion shell'
    });
  });
});
