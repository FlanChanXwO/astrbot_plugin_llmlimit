/**
 * 主题切换 / Theme management
 */
var _mode = null;

function initTheme() {
  var saved = localStorage.getItem('llmlimit-theme');
  if (saved) {
    _mode = saved;
  } else {
    _mode = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  _applyTheme();
  return _mode;
}

function toggleTheme() {
  _mode = _mode === 'dark' ? 'light' : 'dark';
  localStorage.setItem('llmlimit-theme', _mode);
  _applyTheme();
  return _mode;
}

function _applyTheme() {
  document.documentElement.setAttribute('data-theme', _mode);
}

window.initThemeNative = initTheme;
window.toggleThemeNative = toggleTheme;
