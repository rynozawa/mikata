import { spawn } from 'node:child_process';
import type { OpenClawJob } from '../src/domain/types';
import { advanceOpenClawJob, getOpenClawCommand } from '../src/domain/openclaw';

export interface OpenClawRunPlan {
  mode: 'demo' | 'real';
  cwd: string;
  command: string[];
}

interface BuildOpenClawRunPlanInput {
  job: OpenClawJob;
  workspacePath: string;
  realMode: boolean;
}

interface DemoOptions {
  delayMs?: number;
  onState?: (job: OpenClawJob) => void;
}

interface RealOptions {
  onState?: (job: OpenClawJob) => void;
}

export function buildOpenClawRunPlan(input: BuildOpenClawRunPlanInput): OpenClawRunPlan {
  return {
    mode: input.realMode ? 'real' : 'demo',
    cwd: input.workspacePath,
    command: input.realMode ? getOpenClawCommand(input.job) : ['demo-openclaw', input.job.id]
  };
}

export async function runDemoOpenClawJob(job: OpenClawJob, options: DemoOptions = {}): Promise<OpenClawJob[]> {
  const delayMs = options.delayMs ?? 900;
  const stages = [
    ['working', 'OpenClaw is editing the requested code in demo mode.'],
    ['testing', 'OpenClaw is running the test checklist in demo mode.'],
    ['committing', 'OpenClaw created a demo commit: demo1234.'],
    ['creating_pr', 'OpenClaw created a demo pull request: https://example.local/pr/demo1234.'],
    ['complete', 'OpenClaw demo pull request is ready.']
  ] as const;

  let current = job;
  const states: OpenClawJob[] = [];

  for (const [status, message] of stages) {
    await sleep(delayMs);
    current = advanceOpenClawJob(current, { status, message });
    states.push(current);
    options.onState?.(current);
  }

  return states;
}

export async function runRealOpenClawJob(
  job: OpenClawJob,
  plan: OpenClawRunPlan,
  options: RealOptions = {}
): Promise<OpenClawJob> {
  let current = advanceOpenClawJob(job, {
    status: 'working',
    message: `Starting OpenClaw in ${plan.cwd}`
  });
  options.onState?.(current);

  await new Promise<void>((resolve, reject) => {
    const [command, ...args] = plan.command;
    const child = spawn(command, args, {
      cwd: plan.cwd,
      env: process.env,
      shell: false
    });

    child.stdout.on('data', (chunk: Buffer) => {
      current = advanceOpenClawJob(current, {
        status: inferStatusFromOutput(chunk.toString(), current.status),
        message: chunk.toString().trim()
      });
      options.onState?.(current);
    });

    child.stderr.on('data', (chunk: Buffer) => {
      current = advanceOpenClawJob(current, {
        status: current.status,
        message: chunk.toString().trim()
      });
      options.onState?.(current);
    });

    child.on('error', reject);
    child.on('close', (code) => {
      if (code === 0) {
        resolve();
        return;
      }
      reject(new Error(`OpenClaw exited with code ${code}`));
    });
  });

  current = advanceOpenClawJob(current, {
    status: 'complete',
    message: 'OpenClaw finished. Check the commit and pull request details in the logs.'
  });
  options.onState?.(current);

  return current;
}

function inferStatusFromOutput(output: string, fallback: OpenClawJob['status']): OpenClawJob['status'] {
  const normalized = output.toLowerCase();
  if (normalized.includes('test')) return 'testing';
  if (normalized.includes('commit')) return 'committing';
  if (normalized.includes('pull request') || normalized.includes('pr ')) return 'creating_pr';
  return fallback === 'queued' ? 'working' : fallback;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
