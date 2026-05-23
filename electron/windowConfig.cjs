const backgroundColor = '#f4f7f6';

function buildDashboardWindowOptions() {
  return {
    width: 1280,
    height: 860,
    minWidth: 980,
    minHeight: 720,
    title: 'ADHD OpenClaw Pet',
    backgroundColor,
    show: false,
    webPreferences: {
      contextIsolation: true
    }
  };
}

function buildCompanionWindowOptions(position) {
  return {
    width: 420,
    height: 360,
    x: position.x,
    y: position.y,
    title: 'Companion',
    frame: false,
    transparent: false,
    alwaysOnTop: true,
    resizable: true,
    backgroundColor,
    show: false,
    webPreferences: {
      contextIsolation: true
    }
  };
}

function revealWindow(win, options = {}) {
  if (typeof win.isMinimized === 'function' && win.isMinimized()) {
    win.restore();
  }
  win.show();
  if (typeof win.moveTop === 'function') {
    win.moveTop();
  }
  if (options.focus && typeof win.focus === 'function') {
    win.focus();
  }
}

module.exports = {
  buildDashboardWindowOptions,
  buildCompanionWindowOptions,
  revealWindow
};
