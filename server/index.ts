import express from 'express';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import path from 'node:path';
import { classifyActivity } from '../src/domain/activity';
import { deriveCompanionState } from '../src/domain/companion';
import { parseGitStatus } from '../src/domain/git';
import { createOpenClawJob } from '../src/domain/openclaw';
import { createTask, getCurrentTask, selectCurrentTask } from '../src/domain/tasks';
import type {
  ActivityClassification,
  FocusTask,
  GitMetadata,
  OpenClawJob
} from '../src/domain/types';
import {
  buildOpenClawRunPlan,
  runDemoOpenClawJob,
  runRealOpenClawJob
} from './openclawRunner';

const execFileAsync = promisify(execFile);
const app = express();
const port = Number(process.env.PORT ?? 4177);
const workspacePath = process.env.OPENCLAW_WORKSPACE ?? process.cwd();

let tasks: FocusTask[] = selectCurrentTask(
  [
    createTask({
      id: 'task-demo-ui',
      title: 'AIペットのデモを仕上げる',
      priority: 'high',
      estimateMinutes: 25
    }),
    createTask({
      id: 'task-openclaw',
      title: 'OpenClawにREADME改善を依頼する',
      estimateMinutes: 20
    })
  ],
  'task-demo-ui'
);

let latestActivity: ActivityClassification = {
  state: 'focused',
  reason: 'Visual Studio Code matches the current focus'
};
const activityEvents: Array<ActivityClassification & { at: string; activeAppName: string; idleSeconds: number }> = [];
const jobs = new Map<string, OpenClawJob>();
let recentUserMessage = '';

app.use(express.json());

app.get('/api/state', async (_req, res) => {
  const gitStatus = await readGitStatus(workspacePath);
  const latestJob = [...jobs.values()].at(-1);
  res.json({
    tasks,
    latestActivity,
    activityEvents,
    jobs: [...jobs.values()],
    gitStatus,
    workspacePath,
    realOpenClawMode: process.env.OPENCLAW_REAL === '1',
    companion: deriveCompanionState({
      currentTask: getCurrentTask(tasks),
      activityState: latestActivity.state,
      openClawStatus: latestJob?.status,
      recentUserMessage
    })
  });
});

app.post('/api/tasks', (req, res) => {
  const task = createTask({
    id: `task-${Date.now()}`,
    title: String(req.body.title ?? '新しいタスク'),
    description: String(req.body.description ?? ''),
    priority: req.body.priority ?? 'medium',
    estimateMinutes: Number(req.body.estimateMinutes ?? 25)
  });
  tasks = [...tasks, task];
  res.status(201).json(task);
});

app.patch('/api/tasks/:id/current', (req, res) => {
  tasks = selectCurrentTask(tasks, req.params.id);
  res.json({ tasks });
});

app.patch('/api/tasks/:id/status', (req, res) => {
  tasks = tasks.map((task) =>
    task.id === req.params.id ? { ...task, status: req.body.status ?? task.status } : task
  );
  res.json({ tasks });
});

app.post('/api/activity', (req, res) => {
  const activeAppName = String(req.body.activeAppName ?? 'Visual Studio Code');
  const idleSeconds = Number(req.body.idleSeconds ?? 0);
  latestActivity = classifyActivity({
    activeAppName,
    idleSeconds,
    expectedAppNames: ['Visual Studio Code', 'Cursor', 'Terminal', 'iTerm', 'Codex', 'OpenClaw'],
    idleThresholdSeconds: Number(req.body.idleThresholdSeconds ?? 300)
  });
  activityEvents.unshift({
    ...latestActivity,
    at: new Date().toISOString(),
    activeAppName,
    idleSeconds
  });
  res.json(latestActivity);
});

app.post('/api/context', (req, res) => {
  recentUserMessage = String(req.body.message ?? '').slice(0, 240);
  res.json({ recentUserMessage });
});

app.get('/api/activity/probe', async (_req, res) => {
  const [activeAppName, idleSeconds] = await Promise.all([readActiveMacApp(), readIdleSeconds()]);
  res.json({ activeAppName, idleSeconds });
});

app.get('/api/git/status', async (req, res) => {
  res.json(await readGitStatus(String(req.query.path ?? workspacePath)));
});

app.get('/api/openclaw/jobs', (_req, res) => {
  res.json([...jobs.values()]);
});

app.post('/api/openclaw/jobs', async (req, res) => {
  const job = createOpenClawJob({
    id: `job-${Date.now()}`,
    taskId: String(req.body.taskId ?? getCurrentTask(tasks)?.id ?? 'task-demo-ui'),
    prompt: String(req.body.prompt ?? 'READMEを改善して、テストを実行し、commitとpull requestを作成して')
  });
  jobs.set(job.id, job);
  res.status(202).json(job);

  const plan = buildOpenClawRunPlan({
    job,
    workspacePath: path.resolve(String(req.body.workspacePath ?? workspacePath)),
    realMode: process.env.OPENCLAW_REAL === '1'
  });

  const onState = (updated: OpenClawJob) => jobs.set(updated.id, updated);

  if (plan.mode === 'real') {
    runRealOpenClawJob(job, plan, { onState }).catch((error) => {
      const failed = {
        ...jobs.get(job.id)!,
        status: 'failed' as const,
        logs: [
          ...jobs.get(job.id)!.logs,
          {
            at: new Date().toISOString(),
            status: 'failed' as const,
            message: error instanceof Error ? error.message : String(error)
          }
        ]
      };
      jobs.set(job.id, failed);
    });
    return;
  }

  runDemoOpenClawJob(job, { onState }).catch((error) => {
    const failed = {
      ...jobs.get(job.id)!,
      status: 'failed' as const,
      logs: [
        ...jobs.get(job.id)!.logs,
        {
          at: new Date().toISOString(),
          status: 'failed' as const,
          message: error instanceof Error ? error.message : String(error)
        }
      ]
    };
    jobs.set(job.id, failed);
  });
});

app.listen(port, '127.0.0.1', () => {
  console.log(`ADHD OpenClaw Pet API listening on http://127.0.0.1:${port}`);
});

async function readGitStatus(cwd: string): Promise<GitMetadata> {
  try {
    const [statusResult, commitResult] = await Promise.all([
      execFileAsync('git', ['status', '--short', '--branch'], { cwd }),
      execFileAsync('git', ['log', '-1', '--oneline'], { cwd }).catch(() => ({ stdout: 'No commits yet' }))
    ]);
    return parseGitStatus({
      statusText: statusResult.stdout,
      lastCommitText: commitResult.stdout
    });
  } catch {
    return {
      branch: 'not-a-git-workspace',
      dirtyCount: 0,
      lastCommit: 'Git metadata unavailable'
    };
  }
}

async function readActiveMacApp(): Promise<string> {
  try {
    const result = await execFileAsync('osascript', [
      '-e',
      'tell application "System Events" to get name of first application process whose frontmost is true'
    ]);
    return result.stdout.trim() || 'Unknown';
  } catch {
    return 'Unknown';
  }
}

async function readIdleSeconds(): Promise<number> {
  try {
    const result = await execFileAsync('sh', [
      '-lc',
      "ioreg -c IOHIDSystem | awk '/HIDIdleTime/ {print int($NF/1000000000); exit}'"
    ]);
    return Number(result.stdout.trim() || 0);
  } catch {
    return 0;
  }
}
