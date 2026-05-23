import type {
  ActivityClassification,
  CompanionState,
  FocusTask,
  GitMetadata,
  OpenClawJob,
  OpenClawJobStatus
} from '../domain/types';
import { getCurrentTask } from '../domain/tasks';

interface BuildDashboardSummaryInput {
  tasks: FocusTask[];
  jobs: OpenClawJob[];
  latestActivity: ActivityClassification;
  gitStatus: GitMetadata;
  companion: CompanionState;
}

export interface DashboardSummary {
  currentTaskTitle: string;
  openClawLabel: string;
  privacyLabel: string;
  gitLabel: string;
  activityLabel: string;
  companionLine: string;
}

const openClawLabels: Record<OpenClawJobStatus | 'none', string> = {
  none: '待機中',
  queued: '待機中',
  working: '実装中',
  testing: 'テスト中',
  committing: 'commit中',
  creating_pr: 'PR作成中',
  complete: '完了',
  failed: '停止'
};

const activityLabels: Record<ActivityClassification['state'], string> = {
  focused: '集中',
  idle: '停止気味',
  off_task: '脱線気味'
};

export function buildDashboardSummary(input: BuildDashboardSummaryInput): DashboardSummary {
  const currentTask = getCurrentTask(input.tasks);
  const latestJob = input.jobs.at(-1);

  return {
    currentTaskTitle: currentTask?.title ?? '今やるタスクを選ぶ',
    openClawLabel: openClawLabels[latestJob?.status ?? 'none'],
    privacyLabel: 'メタ情報のみ',
    gitLabel: `${input.gitStatus.branch} / 未保存 ${input.gitStatus.dirtyCount}`,
    activityLabel: activityLabels[input.latestActivity.state],
    companionLine: input.companion.message
  };
}
