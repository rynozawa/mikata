import { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  Bot,
  Brain,
  CheckCircle2,
  Circle,
  Code2,
  GitBranch,
  Play,
  Plus,
  RefreshCw,
  Send,
  ShieldCheck
} from 'lucide-react';
import type {
  ActivityClassification,
  CompanionState,
  FocusTask,
  GitMetadata,
  OpenClawJob
} from './domain/types';
import { getCurrentTask } from './domain/tasks';
import { buildDashboardSummary } from './viewModel/dashboard';

interface ApiState {
  tasks: FocusTask[];
  latestActivity: ActivityClassification;
  activityEvents: Array<ActivityClassification & { at: string; activeAppName: string; idleSeconds: number }>;
  jobs: OpenClawJob[];
  gitStatus: GitMetadata;
  workspacePath: string;
  realOpenClawMode: boolean;
  companion: CompanionState;
}

const taskPriorityLabel: Record<FocusTask['priority'], string> = {
  high: 'High',
  medium: 'Mid',
  low: 'Low'
};

export function App() {
  const [state, setState] = useState<ApiState | null>(null);
  const [taskTitle, setTaskTitle] = useState('');
  const [taskMinutes, setTaskMinutes] = useState(25);
  const [openClawPrompt, setOpenClawPrompt] = useState('READMEを改善して、テストを実行し、commitとpull requestを作成して');
  const [contextMessage, setContextMessage] = useState('');
  const [busy, setBusy] = useState(false);

  const companionOnly = window.location.hash === '#companion';

  const refresh = async () => {
    const response = await fetch('/api/state');
    setState(await response.json());
  };

  useEffect(() => {
    refresh();
    const id = window.setInterval(refresh, 1200);
    return () => window.clearInterval(id);
  }, []);

  useEffect(() => {
    const markFocused = () => {
      postJson('/api/activity', {
        activeAppName: document.visibilityState === 'visible' ? 'Visual Studio Code' : 'Background',
        idleSeconds: 0
      }).then(refresh);
    };
    window.addEventListener('keydown', markFocused);
    window.addEventListener('pointerdown', markFocused);
    return () => {
      window.removeEventListener('keydown', markFocused);
      window.removeEventListener('pointerdown', markFocused);
    };
  }, []);

  const summary = useMemo(() => {
    if (!state) return null;
    return buildDashboardSummary({
      tasks: state.tasks,
      jobs: state.jobs,
      latestActivity: state.latestActivity,
      gitStatus: state.gitStatus,
      companion: state.companion
    });
  }, [state]);

  if (!state || !summary) {
    return (
      <main className="loading-screen">
        <div className="loading-mark" />
        <p>起動中</p>
      </main>
    );
  }

  const currentTask = getCurrentTask(state.tasks);
  const latestJob = state.jobs.at(-1);
  const latestLogs = latestJob?.logs.slice(-7).reverse() ?? [];

  const addTask = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!taskTitle.trim()) return;
    setBusy(true);
    await postJson('/api/tasks', {
      title: taskTitle,
      estimateMinutes: taskMinutes,
      priority: 'medium'
    });
    setTaskTitle('');
    setTaskMinutes(25);
    await refresh();
    setBusy(false);
  };

  const selectTask = async (taskId: string) => {
    await fetch(`/api/tasks/${taskId}/current`, { method: 'PATCH' });
    await refresh();
  };

  const setActivity = async (activeAppName: string, idleSeconds: number) => {
    await postJson('/api/activity', { activeAppName, idleSeconds });
    await refresh();
  };

  const probeMacActivity = async () => {
    const probe = await fetch('/api/activity/probe').then((response) => response.json());
    await setActivity(probe.activeAppName, probe.idleSeconds);
  };

  const runOpenClaw = async () => {
    setBusy(true);
    await postJson('/api/openclaw/jobs', {
      taskId: currentTask?.id,
      prompt: openClawPrompt,
      workspacePath: state.workspacePath
    });
    await refresh();
    setBusy(false);
  };

  const sendContext = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!contextMessage.trim()) return;
    await postJson('/api/context', { message: contextMessage });
    setContextMessage('');
    await refresh();
  };

  if (companionOnly) {
    return (
      <main className="companion-window">
        <Companion state={state.companion} summary={summary} compact />
      </main>
    );
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">ADHD OpenClaw Pet</p>
          <h1>一緒に頑張る作業相棒</h1>
        </div>
        <div className="status-row">
          <StatusPill icon={<ShieldCheck size={16} />} label={summary.privacyLabel} tone="safe" />
          <StatusPill icon={<Activity size={16} />} label={summary.activityLabel} tone={state.latestActivity.state} />
          <StatusPill icon={<Bot size={16} />} label={summary.openClawLabel} tone={latestJob?.status ?? 'queued'} />
        </div>
      </header>

      <section className="workspace-grid">
        <section className="panel task-panel">
          <div className="panel-heading">
            <div>
              <p className="section-kicker">Focus</p>
              <h2>今やる1つ</h2>
            </div>
            <span className="metric">{state.tasks.length}</span>
          </div>

          <div className="current-task">
            <p>{summary.currentTaskTitle}</p>
            <span>{currentTask ? `${currentTask.estimateMinutes} min` : '未選択'}</span>
          </div>

          <form className="task-form" onSubmit={addTask}>
            <input
              value={taskTitle}
              onChange={(event) => setTaskTitle(event.target.value)}
              placeholder="タスク名"
              aria-label="タスク名"
            />
            <input
              value={taskMinutes}
              onChange={(event) => setTaskMinutes(Number(event.target.value))}
              type="number"
              min={5}
              max={180}
              step={5}
              aria-label="見積もり分"
            />
            <button className="icon-button primary" type="submit" disabled={busy} aria-label="タスクを追加">
              <Plus size={18} />
            </button>
          </form>

          <div className="task-list">
            {state.tasks.map((task) => (
              <button
                key={task.id}
                className={`task-row ${task.isCurrent ? 'selected' : ''}`}
                type="button"
                onClick={() => selectTask(task.id)}
              >
                {task.isCurrent ? <CheckCircle2 size={18} /> : <Circle size={18} />}
                <span>{task.title}</span>
                <small>{taskPriorityLabel[task.priority]}</small>
              </button>
            ))}
          </div>
        </section>

        <section className="stage">
          <Companion state={state.companion} summary={summary} />

          <form className="context-strip" onSubmit={sendContext}>
            <Brain size={18} />
            <input
              value={contextMessage}
              onChange={(event) => setContextMessage(event.target.value)}
              placeholder="今の気分や文脈"
              aria-label="今の気分や文脈"
            />
            <button className="icon-button" type="submit" aria-label="文脈を送る">
              <Send size={16} />
            </button>
          </form>

          <section className="openclaw-panel">
            <div className="panel-heading">
              <div>
                <p className="section-kicker">OpenClaw</p>
                <h2>コーディング担当</h2>
              </div>
              <span className={`mode-badge ${state.realOpenClawMode ? 'real' : 'demo'}`}>
                {state.realOpenClawMode ? 'Real' : 'Demo'}
              </span>
            </div>
            <textarea
              value={openClawPrompt}
              onChange={(event) => setOpenClawPrompt(event.target.value)}
              aria-label="OpenClawへの依頼"
            />
            <button className="command-button" type="button" onClick={runOpenClaw} disabled={busy}>
              <Play size={18} />
              <span>OpenClawに任せる</span>
            </button>
          </section>
        </section>

        <section className="panel telemetry-panel">
          <div className="panel-heading">
            <div>
              <p className="section-kicker">Signals</p>
              <h2>メタ情報</h2>
            </div>
            <button className="icon-button" type="button" onClick={refresh} aria-label="更新">
              <RefreshCw size={17} />
            </button>
          </div>

          <div className="signal-stack">
            <InfoLine icon={<GitBranch size={18} />} label="Git" value={summary.gitLabel} />
            <InfoLine icon={<Code2 size={18} />} label="Last" value={state.gitStatus.lastCommit} />
            <InfoLine icon={<Activity size={18} />} label="Activity" value={state.latestActivity.reason} />
          </div>

          <div className="quick-actions">
            <button type="button" onClick={() => setActivity('Visual Studio Code', 0)}>
              集中
            </button>
            <button type="button" onClick={() => setActivity('YouTube', 18)}>
              脱線
            </button>
            <button type="button" onClick={() => setActivity('Visual Studio Code', 720)}>
              停止
            </button>
            <button type="button" onClick={probeMacActivity}>
              macOS
            </button>
          </div>

          <div className="log-section">
            <h3>OpenClaw Log</h3>
            <div className="log-list">
              {latestLogs.length === 0 ? (
                <p className="empty">まだ実行はありません</p>
              ) : (
                latestLogs.map((log, index) => (
                  <div className="log-row" key={`${log.at}-${index}`}>
                    <span>{log.status}</span>
                    <p>{log.message}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </section>
      </section>
    </main>
  );
}

function Companion({
  state,
  summary,
  compact = false
}: {
  state: CompanionState;
  summary: ReturnType<typeof buildDashboardSummary>;
  compact?: boolean;
}) {
  return (
    <section className={`companion-card mode-${state.mode} mood-${state.mood} ${compact ? 'compact' : ''}`}>
      <div className={`mascot motion-${state.motion}`} aria-hidden="true">
        <div className="mascot-head">
          <span className="eye left" />
          <span className="eye right" />
          <span className="mouth" />
        </div>
        <div className="mascot-body">
          <span className="pulse-line" />
          <span className="pulse-line short" />
        </div>
        <span className="arm left" />
        <span className="arm right" />
      </div>
      <div className="speech">
        <p className="section-kicker">Companion</p>
        <h2>{summary.currentTaskTitle}</h2>
        <p>{summary.companionLine}</p>
      </div>
    </section>
  );
}

function StatusPill({
  icon,
  label,
  tone
}: {
  icon: React.ReactNode;
  label: string;
  tone: string;
}) {
  return (
    <span className={`status-pill tone-${tone}`}>
      {icon}
      {label}
    </span>
  );
}

function InfoLine({
  icon,
  label,
  value
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="info-line">
      {icon}
      <span>{label}</span>
      <p>{value}</p>
    </div>
  );
}

async function postJson(url: string, body: unknown) {
  return fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
}
