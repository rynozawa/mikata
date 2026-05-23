# ADHD OpenClaw Pet Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a hackathon-ready macOS-first ADHD focus companion that shows an AI character, tracks task/activity metadata, and can hand coding work to OpenClaw.

**Architecture:** Use a local-first web app for the demo surface and a Node API for trusted local actions. Keep domain behavior in small tested modules, then wire it into React UI and an optional Electron shell for a floating companion.

**Tech Stack:** Vite, React, TypeScript, Vitest, Express, tsx, optional Electron.

---

### Task 1: Project Scaffold and Domain Tests

**Files:**
- Create: `package.json`
- Create: `index.html`
- Create: `tsconfig.json`
- Create: `vite.config.ts`
- Create: `vitest.config.ts`
- Create: `src/domain/*.test.ts`

- [ ] Add package scripts and dev dependencies.
- [ ] Write failing Vitest tests for task selection, companion mood, OpenClaw job transitions, activity classification, and Git status parsing.
- [ ] Run `npm test -- --run` and confirm tests fail because implementation files do not exist.

### Task 2: Domain Implementation

**Files:**
- Create: `src/domain/tasks.ts`
- Create: `src/domain/companion.ts`
- Create: `src/domain/openclaw.ts`
- Create: `src/domain/activity.ts`
- Create: `src/domain/git.ts`
- Create: `src/domain/types.ts`

- [ ] Implement the smallest pure TypeScript logic needed to pass the tests.
- [ ] Keep monitoring metadata-only: idle seconds, active app name, Git state, and job state.
- [ ] Run `npm test -- --run` and confirm the domain suite passes.

### Task 3: Local API and OpenClaw Runner

**Files:**
- Create: `server/index.ts`
- Create: `server/openclawRunner.ts`

- [ ] Expose APIs for tasks, activity events, Git status, and OpenClaw jobs.
- [ ] Support demo mode by default and real OpenClaw execution with `OPENCLAW_REAL=1`.
- [ ] Log OpenClaw stage changes and stdout/stderr for replay in the UI.

### Task 4: React Hackathon UI

**Files:**
- Create: `src/main.tsx`
- Create: `src/App.tsx`
- Create: `src/styles.css`

- [ ] Build a desktop-style dashboard with a persistent AI companion, task list, activity timeline, Git/OpenClaw panels, and live logs.
- [ ] Make the character react to idle, off-task, working, testing, commit, PR, complete, and failed states.
- [ ] Keep post-completion animation in companion/cheer mode so it feels like the character is still accompanying the user without hiding completion.

### Task 5: Optional macOS Desktop Shell and Docs

**Files:**
- Create: `electron/main.cjs`
- Create: `README.md`

- [ ] Add an optional Electron shell with a small always-on-top companion window and a main dashboard window.
- [ ] Document setup, dev scripts, OpenClaw real mode, demo mode, and privacy boundaries.

### Task 6: Verification

- [ ] Run `npm test -- --run`.
- [ ] Run `npm run build`.
- [ ] Start the local dev server and verify the UI in browser.
- [ ] Confirm the README explains that the app stores only metadata and does not save keystrokes, screenshots, emails, or chat contents.
