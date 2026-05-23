import type { OpenClawJob, OpenClawJobStatus } from './types';

interface CreateOpenClawJobInput {
  id: string;
  taskId: string;
  prompt: string;
}

interface AdvanceOpenClawJobInput {
  status: OpenClawJobStatus;
  message: string;
  at?: string;
}

export function createOpenClawJob(input: CreateOpenClawJobInput): OpenClawJob {
  return {
    id: input.id,
    taskId: input.taskId,
    prompt: buildCodingPrompt(input.prompt),
    status: 'queued',
    logs: [
      {
        at: new Date(0).toISOString(),
        status: 'queued',
        message: 'OpenClaw coding job queued'
      }
    ]
  };
}

export function advanceOpenClawJob(job: OpenClawJob, input: AdvanceOpenClawJobInput): OpenClawJob {
  return {
    ...job,
    status: input.status,
    logs: [
      ...job.logs,
      {
        at: input.at ?? new Date().toISOString(),
        status: input.status,
        message: input.message
      }
    ]
  };
}

export function getOpenClawCommand(job: OpenClawJob): string[] {
  return ['openclaw', 'agent', '--message', job.prompt, '--thinking', 'high'];
}

function buildCodingPrompt(userPrompt: string): string {
  return [
    userPrompt.trim(),
    '',
    'Work as the coding agent for this hackathon demo.',
    'You may edit code, run tests, create a git commit, push the branch, and create a pull request without extra confirmation.',
    'Keep changes scoped to the requested task and avoid destructive commands.',
    'When finished, summarize files changed, tests run, commit hash, and pull request URL.'
  ].join('\n');
}
