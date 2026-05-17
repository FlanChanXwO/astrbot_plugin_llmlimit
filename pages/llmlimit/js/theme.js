/**
 * 主题切换 / Theme management
 */

console.log('[llmlimit] theme.js loaded');

var _mode = null;

function initTheme() {
  var saved = null;
  try { saved = localStorage.getItem('llmlimit-theme'); } catch (e) { /* sandboxed iframe */ }
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
  try { localStorage.setItem('llmlimit-theme', _mode); } catch (e) { /* sandboxed iframe */ }
  _applyTheme();
  return _mode;
}

function _applyTheme() {
  document.documentElement.setAttribute('data-theme', _mode);
}

window.initThemeNative = initTheme;
window.toggleThemeNative = toggleTheme;
