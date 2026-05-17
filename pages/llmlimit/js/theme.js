/**
 * 主题切换 / Theme management
 */
let _mode = null;

export function initTheme() {
  const saved = localStorage.getItem('llmlimit-theme');
  if (saved) {
    _mode = saved;
  } else {
    _mode = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  _applyTheme();
  return _mode;
}

export function toggleTheme() {
  _mode = _mode === 'dark' ? 'light' : 'dark';
  localStorage.setItem('llmlimit-theme', _mode);
  _applyTheme();
  return _mode;
}

function _applyTheme() {
  document.documentElement.setAttribute('data-theme', _mode);
}
