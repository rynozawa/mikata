const { app, BrowserWindow, screen } = require('electron');
const {
  buildCompanionWindowOptions,
  buildDashboardWindowOptions,
  revealWindow
} = require('./windowConfig.cjs');

const dashboardUrl = 'http://127.0.0.1:5173';
const windows = new Set();

function keepWindow(win) {
  windows.add(win);
  win.on('closed', () => windows.delete(win));
  return win;
}

function createDashboardWindow() {
  const win = new BrowserWindow(buildDashboardWindowOptions());

  win.once('ready-to-show', () => revealWindow(win, { focus: true }));
  win.webContents.on('did-fail-load', (_event, code, description) => {
    console.error(`Dashboard failed to load: ${code} ${description}`);
  });
  win.loadURL(dashboardUrl);
  return keepWindow(win);
}

function createCompanionWindow() {
  const display = screen.getPrimaryDisplay();
  const width = 420;
  const height = 360;
  const x = display.workArea.x + display.workArea.width - width - 24;
  const y = display.workArea.y + display.workArea.height - height - 24;

  const win = new BrowserWindow(buildCompanionWindowOptions({ x, y }));

  win.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
  win.setAlwaysOnTop(true, 'screen-saver');
  win.once('ready-to-show', () => revealWindow(win, { focus: false }));
  win.webContents.on('did-fail-load', (_event, code, description) => {
    console.error(`Companion failed to load: ${code} ${description}`);
  });
  win.loadURL(`${dashboardUrl}/#companion`);
  return keepWindow(win);
}

app.whenReady().then(() => {
  app.setActivationPolicy('regular');
  createDashboardWindow();
  createCompanionWindow();
  app.focus({ steal: true });

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createDashboardWindow();
      createCompanionWindow();
    } else {
      BrowserWindow.getAllWindows().forEach((win) => revealWindow(win, { focus: true }));
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
