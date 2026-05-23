import type { GitMetadata } from './types';

interface ParseGitStatusInput {
  statusText: string;
  lastCommitText: string;
}

export function parseGitStatus(input: ParseGitStatusInput): GitMetadata {
  const lines = input.statusText.split('\n').filter(Boolean);
  const branchLine = lines.find((line) => line.startsWith('## ')) ?? '## unknown';
  const branch = branchLine.replace(/^##\s+/, '').split('...')[0].trim();
  const dirtyCount = lines.filter((line) => !line.startsWith('## ')).length;

  return {
    branch,
    dirtyCount,
    lastCommit: input.lastCommitText.trim()
  };
}
