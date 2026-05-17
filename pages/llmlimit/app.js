const api = window.ApiModule;

console.log('[llmlimit] app.js loaded');

// ── State ────────────────────────────────────────────────────────────

const state = {
  activeTab: 'users',
  userLimits: [],
  groupLimits: [],
  timePeriodLimits: [],
  editingUserIndex: -1,
  editingGroupIndex: -1,
  editingPeriodIndex: -1,
  panelVisible: false,
  toastTimer: null,
  confirmResolve: null,
};

// ── DOM refs ─────────────────────────────────────────────────────────

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const dom = {
  tabBar: $('#tabBar'),
  tabUsers: $('#tabUsers'),
  tabGroups: $('#tabGroups'),
  tabPeriods: $('#tabPeriods'),
  userList: $('#userList'),
  groupList: $('#groupList'),
  periodList: $('#periodList'),
  panelOverlay: $('#panelOverlay'),
  editPanel: $('#editPanel'),
  panelTitle: $('#panelTitle'),
  panelClose: $('#panelClose'),
  userForm: $('#userForm'),
  groupForm: $('#groupForm'),
  periodForm: $('#periodForm'),
  inputUserId: $('#inputUserId'),
  inputUserLimit: $('#inputUserLimit'),
  inputGroupId: $('#inputGroupId'),
  inputGroupLimit: $('#inputGroupLimit'),
  inputPeriodStart: $('#inputPeriodStart'),
  inputPeriodEnd: $('#inputPeriodEnd'),
  inputPeriodLimit: $('#inputPeriodLimit'),
  inputPeriodEnabled: $('#inputPeriodEnabled'),
  periodToggleLabel: $('#periodToggleLabel'),
  toast: $('#toast'),
  confirmOverlay: $('#confirmOverlay'),
  confirmTitle: $('#confirmTitle'),
  confirmMsg: $('#confirmMsg'),
  confirmOk: $('#confirmOk'),
  confirmCancel: $('#confirmCancel'),
  themeToggle: $('#themeToggle'),
  btnAddUser: $('#btnAddUser'),
  btnAddGroup: $('#btnAddGroup'),
  btnAddPeriod: $('#btnAddPeriod'),
};

// ── Lifecycle ────────────────────────────────────────────────────────

async function ready() {
  // Theme + event bindings must work even if the API bridge is not yet available
  // Theme init must not block event bindings (sandboxed iframe: no localStorage)
  try { initTheme(); } catch (e) { console.warn('[llmlimit] initTheme failed:', e); }
  bindEvents();
  document.body.classList.add('js-loaded');

  // Data loading requires the AstrBotPluginPage bridge; handle gracefully
  try {
    await api.ready();
    await loadAll();
  } catch (err) {
    console.warn('[llmlimit] API bridge not ready, data loading skipped:', err.message);
  }
}

// ── Data loading ─────────────────────────────────────────────────────

async function loadAll() {
  try {
    const [users, groups, timePeriods] = await Promise.all([
      api.getUserLimits(),
      api.getGroupLimits(),
      api.getTimePeriodLimits(),
    ]);
    state.userLimits = users || [];
    state.groupLimits = groups || [];
    state.timePeriodLimits = timePeriods || [];
    renderLists();
  } catch (err) {
    showToast('加载失败: ' + err.message, 'error');
  }
}

// ── Render ───────────────────────────────────────────────────────────

function renderLists() {
  renderUserList();
  renderGroupList();
  renderPeriodList();
}

function renderUserList() {
  const list = state.userLimits;
  if (list.length === 0) {
    dom.userList.innerHTML = '<div class="empty-state"><p>暂无用户特定限制，点击「添加用户」开始配置。</p></div>';
    return;
  }
  dom.userList.innerHTML = list.map((item, i) => `
    <div class="item-row">
      <div class="item-info">
        <div class="item-name">
          ${escHtml(item.userId)}
          <span class="item-badge badge-primary">${escHtml(item.limit)} 次/日</span>
        </div>
        <div class="item-meta">用户ID: ${escHtml(item.userId)}</div>
      </div>
      <div class="item-actions">
        <button class="btn btn-sm btn-secondary" data-action="edit-user" data-index="${i}">编辑</button>
        <button class="btn btn-sm btn-danger-outline" data-action="delete-user" data-index="${i}">删除</button>
      </div>
    </div>
  `).join('');
}

function renderGroupList() {
  const list = state.groupLimits;
  if (list.length === 0) {
    dom.groupList.innerHTML = '<div class="empty-state"><p>暂无群组特定限制，点击「添加群组」开始配置。</p></div>';
    return;
  }
  dom.groupList.innerHTML = list.map((item, i) => `
    <div class="item-row">
      <div class="item-info">
        <div class="item-name">
          ${escHtml(item.groupId)}
          <span class="item-badge badge-success">${escHtml(item.limit)} 次/日</span>
        </div>
        <div class="item-meta">群ID: ${escHtml(item.groupId)}</div>
      </div>
      <div class="item-actions">
        <button class="btn btn-sm btn-secondary" data-action="edit-group" data-index="${i}">编辑</button>
        <button class="btn btn-sm btn-danger-outline" data-action="delete-group" data-index="${i}">删除</button>
      </div>
    </div>
  `).join('');
}

function renderPeriodList() {
  const list = state.timePeriodLimits;
  if (list.length === 0) {
    dom.periodList.innerHTML = '<div class="empty-state"><p>暂无时间段限制，点击「添加时段」开始配置。</p></div>';
    return;
  }
  dom.periodList.innerHTML = list.map((item, i) => `
    <div class="item-row">
      <div class="item-info">
        <div class="item-name">
          ${escHtml(item.startTime)} – ${escHtml(item.endTime)}
          <span class="item-badge ${item.enabled ? 'badge-primary' : 'badge-warning'}">${escHtml(item.limit)} 次</span>
          ${item.enabled ? '' : '<span class="item-badge badge-warning">已停用</span>'}
        </div>
        <div class="item-meta">
          时段 ${escHtml(item.startTime)}–${escHtml(item.endTime)}，上限 ${escHtml(item.limit)} 次
          ${item.enabled ? '' : '（已禁用）'}
        </div>
      </div>
      <div class="item-actions">
        <button class="btn btn-sm btn-secondary" data-action="edit-period" data-index="${i}">编辑</button>
        <button class="btn btn-sm btn-danger-outline" data-action="delete-period" data-index="${i}">删除</button>
      </div>
    </div>
  `).join('');
}

// ── Tab switching ────────────────────────────────────────────────────

function switchTab(tab) {
  state.activeTab = tab;
  $$('.tab-btn').forEach((btn) => {
    btn.classList.toggle('active', btn.dataset.tab === tab);
  });
  dom.tabUsers.hidden = tab !== 'users';
  dom.tabGroups.hidden = tab !== 'groups';
  dom.tabPeriods.hidden = tab !== 'periods';
}

// ── Panel ────────────────────────────────────────────────────────────

function openUserPanel(index) {
  state.editingUserIndex = index;
  state.editingGroupIndex = -1;
  state.editingPeriodIndex = -1;
  if (index >= 0) {
    const item = state.userLimits[index];
    dom.inputUserId.value = item.userId || '';
    dom.inputUserLimit.value = item.limit || '';
    dom.panelTitle.textContent = '编辑用户限制';
    $('#userFormSubmit').textContent = '更新';
  } else {
    dom.inputUserId.value = '';
    dom.inputUserLimit.value = '';
    dom.panelTitle.textContent = '添加用户限制';
    $('#userFormSubmit').textContent = '添加';
  }
  showPanel('userForm');
}

function openGroupPanel(index) {
  state.editingGroupIndex = index;
  state.editingUserIndex = -1;
  state.editingPeriodIndex = -1;
  if (index >= 0) {
    const item = state.groupLimits[index];
    dom.inputGroupId.value = item.groupId || '';
    dom.inputGroupLimit.value = item.limit || '';
    dom.panelTitle.textContent = '编辑群组限制';
    $('#groupFormSubmit').textContent = '更新';
  } else {
    dom.inputGroupId.value = '';
    dom.inputGroupLimit.value = '';
    dom.panelTitle.textContent = '添加群组限制';
    $('#groupFormSubmit').textContent = '添加';
  }
  showPanel('groupForm');
}

function openPeriodPanel(index) {
  state.editingPeriodIndex = index;
  state.editingUserIndex = -1;
  state.editingGroupIndex = -1;
  if (index >= 0) {
    const p = state.timePeriodLimits[index];
    dom.inputPeriodStart.value = p.startTime;
    dom.inputPeriodEnd.value = p.endTime;
    dom.inputPeriodLimit.value = p.limit;
    dom.inputPeriodEnabled.checked = p.enabled;
    updatePeriodToggleLabel();
    dom.panelTitle.textContent = '编辑时间段';
    $('#periodFormSubmit').textContent = '更新';
  } else {
    dom.inputPeriodStart.value = '09:00';
    dom.inputPeriodEnd.value = '12:00';
    dom.inputPeriodLimit.value = '5';
    dom.inputPeriodEnabled.checked = true;
    updatePeriodToggleLabel();
    dom.panelTitle.textContent = '添加时间段';
    $('#periodFormSubmit').textContent = '添加';
  }
  showPanel('periodForm');
}

function showPanel(formId) {
  dom.userForm.hidden = formId !== 'userForm';
  dom.groupForm.hidden = formId !== 'groupForm';
  dom.periodForm.hidden = formId !== 'periodForm';
  dom.editPanel.classList.add('panel-visible');
  dom.panelOverlay.classList.add('visible');
  state.panelVisible = true;
}

function closePanel() {
  dom.editPanel.classList.remove('panel-visible');
  dom.panelOverlay.classList.remove('visible');
  state.panelVisible = false;
  state.editingUserIndex = -1;
  state.editingGroupIndex = -1;
  state.editingPeriodIndex = -1;
}

// ── CRUD: users ──────────────────────────────────────────────────────

async function saveUser(e) {
  e.preventDefault();
  const userId = dom.inputUserId.value.trim();
  const limit = parseInt(dom.inputUserLimit.value, 10);
  if (!userId) { showToast('用户ID不能为空', 'error'); return; }
  if (isNaN(limit) || limit <= 0) { showToast('请输入有效的次数（正整数）', 'error'); return; }
  try {
    if (state.editingUserIndex >= 0) {
      await api.updateUserLimit(state.editingUserIndex, { userId, limit });
      showToast('用户限制已更新');
    } else {
      await api.createUserLimit({ userId, limit });
      showToast('用户限制已添加');
    }
    closePanel();
    await loadAll();
  } catch (err) {
    showToast('保存失败: ' + err.message, 'error');
  }
}

async function deleteUser(index) {
  const item = state.userLimits[index];
  if (!item) return;
  const ok = await confirmDialog('确认删除', `确定要删除用户 ${item.userId} 的限制吗？`);
  if (!ok) return;
  try {
    await api.deleteUserLimit(index);
    showToast('用户限制已删除');
    await loadAll();
  } catch (err) {
    showToast('删除失败: ' + err.message, 'error');
  }
}

// ── CRUD: groups ─────────────────────────────────────────────────────

async function saveGroup(e) {
  e.preventDefault();
  const groupId = dom.inputGroupId.value.trim();
  const limit = parseInt(dom.inputGroupLimit.value, 10);
  if (!groupId) { showToast('群ID不能为空', 'error'); return; }
  if (isNaN(limit) || limit <= 0) { showToast('请输入有效的次数（正整数）', 'error'); return; }
  try {
    if (state.editingGroupIndex >= 0) {
      await api.updateGroupLimit(state.editingGroupIndex, { groupId, limit });
      showToast('群组限制已更新');
    } else {
      await api.createGroupLimit({ groupId, limit });
      showToast('群组限制已添加');
    }
    closePanel();
    await loadAll();
  } catch (err) {
    showToast('保存失败: ' + err.message, 'error');
  }
}

async function deleteGroup(index) {
  const item = state.groupLimits[index];
  if (!item) return;
  const ok = await confirmDialog('确认删除', `确定要删除群 ${item.groupId} 的限制吗？`);
  if (!ok) return;
  try {
    await api.deleteGroupLimit(index);
    showToast('群组限制已删除');
    await loadAll();
  } catch (err) {
    showToast('删除失败: ' + err.message, 'error');
  }
}

// ── CRUD: time periods ───────────────────────────────────────────────

async function savePeriod(e) {
  e.preventDefault();
  const start = dom.inputPeriodStart.value;
  const end = dom.inputPeriodEnd.value;
  const limit = parseInt(dom.inputPeriodLimit.value, 10);
  const enabled = dom.inputPeriodEnabled.checked;
  if (!start || !end) { showToast('请填写开始时间和结束时间', 'error'); return; }
  if (isNaN(limit) || limit <= 0) { showToast('请输入有效的次数（正整数）', 'error'); return; }
  try {
    const body = { startTime: start, endTime: end, limit, enabled };
    if (state.editingPeriodIndex >= 0) {
      await api.updateTimePeriod(state.editingPeriodIndex, body);
      showToast('时间段已更新');
    } else {
      await api.createTimePeriod(body);
      showToast('时间段已添加');
    }
    closePanel();
    await loadAll();
  } catch (err) {
    showToast('保存失败: ' + err.message, 'error');
  }
}

async function deletePeriod(index) {
  const item = state.timePeriodLimits[index];
  if (!item) return;
  const label = `${item.startTime}-${item.endTime} (${item.limit}次)`;
  const ok = await confirmDialog('确认删除', `确定要删除时间段 ${label} 吗？`);
  if (!ok) return;
  try {
    await api.deleteTimePeriod(index);
    showToast('时间段已删除');
    await loadAll();
  } catch (err) {
    showToast('删除失败: ' + err.message, 'error');
  }
}

// ── Toast ────────────────────────────────────────────────────────────

function showToast(message, type) {
  type = type || 'success';
  dom.toast.textContent = message;
  dom.toast.className = 'toast ' + type + ' show';
  clearTimeout(state.toastTimer);
  state.toastTimer = setTimeout(() => {
    dom.toast.classList.remove('show');
  }, 3000);
}

// ── Confirm dialog ───────────────────────────────────────────────────

function confirmDialog(title, message) {
  return new Promise((resolve) => {
    dom.confirmTitle.textContent = title;
    dom.confirmMsg.textContent = message;
    dom.confirmOverlay.classList.add('visible');
    state.confirmResolve = resolve;
  });
}

function closeConfirm(res) {
  dom.confirmOverlay.classList.remove('visible');
  if (state.confirmResolve) {
    state.confirmResolve(res);
    state.confirmResolve = null;
  }
}

// ── Theme ────────────────────────────────────────────────────────────

function initTheme() {
  if (typeof initThemeNative === 'function') {
    initThemeNative();
  }
  updateThemeLabel();
}

function toggleTheme() {
  if (typeof toggleThemeNative === 'function') {
    toggleThemeNative();
  }
  updateThemeLabel();
}

function updateThemeLabel() {
  const dark = document.documentElement.getAttribute('data-theme') === 'dark';
  dom.themeToggle.textContent = dark ? '☀️ 浅色' : '🌙 深色';
}

// ── Helpers ──────────────────────────────────────────────────────────

function escHtml(str) {
  const div = document.createElement('span');
  div.textContent = str;
  return div.innerHTML;
}

function updatePeriodToggleLabel() {
  dom.periodToggleLabel.textContent = dom.inputPeriodEnabled.checked ? '启用' : '停用';
}

// ── Event binding ────────────────────────────────────────────────────

var bindOkCount = 0;
var bindTotalCount = 0;

function safely(el, event, handler, label) {
  bindTotalCount++;
  if (!el) {
    console.error('[llmlimit] bind failed: element is null for "' + label + '"');
    return;
  }
  try {
    el.addEventListener(event, handler);
    bindOkCount++;
  } catch (e) {
    console.error('[llmlimit] bind failed for "' + label + '":', e);
  }
}

function bindEvents() {
  // Tabs
  safely(dom.tabBar, 'click', (e) => {
    const btn = e.target.closest('[data-tab]');
    if (btn) switchTab(btn.dataset.tab);
  }, 'tabBar');

  // Theme
  safely(dom.themeToggle, 'click', toggleTheme, 'themeToggle');

  // Panel
  safely(dom.panelClose, 'click', closePanel, 'panelClose');
  safely(dom.panelOverlay, 'click', closePanel, 'panelOverlay');

  // Add buttons
  safely(dom.btnAddUser, 'click', () => openUserPanel(-1), 'btnAddUser');
  safely(dom.btnAddGroup, 'click', () => openGroupPanel(-1), 'btnAddGroup');
  safely(dom.btnAddPeriod, 'click', () => openPeriodPanel(-1), 'btnAddPeriod');

  // Form submissions
  safely(dom.userForm, 'submit', saveUser, 'userForm');
  safely(dom.groupForm, 'submit', saveGroup, 'groupForm');
  safely(dom.periodForm, 'submit', savePeriod, 'periodForm');

  // Form cancel buttons
  safely(document.querySelector('#userFormCancel'), 'click', closePanel, 'userFormCancel');
  safely(document.querySelector('#groupFormCancel'), 'click', closePanel, 'groupFormCancel');
  safely(document.querySelector('#periodFormCancel'), 'click', closePanel, 'periodFormCancel');

  // Period enabled toggle label
  safely(dom.inputPeriodEnabled, 'change', updatePeriodToggleLabel, 'inputPeriodEnabled');

  // Confirm dialog
  safely(dom.confirmOk, 'click', () => closeConfirm(true), 'confirmOk');
  safely(dom.confirmCancel, 'click', () => closeConfirm(false), 'confirmCancel');

  // List item delegation (edit / delete)
  safely(dom.userList, 'click', (e) => {
    const btn = e.target.closest('[data-action]');
    if (!btn) return;
    const idx = parseInt(btn.dataset.index, 10);
    if (btn.dataset.action === 'edit-user') openUserPanel(idx);
    else if (btn.dataset.action === 'delete-user') deleteUser(idx);
  }, 'userList');

  safely(dom.groupList, 'click', (e) => {
    const btn = e.target.closest('[data-action]');
    if (!btn) return;
    const idx = parseInt(btn.dataset.index, 10);
    if (btn.dataset.action === 'edit-group') openGroupPanel(idx);
    else if (btn.dataset.action === 'delete-group') deleteGroup(idx);
  }, 'groupList');

  safely(dom.periodList, 'click', (e) => {
    const btn = e.target.closest('[data-action]');
    if (!btn) return;
    const idx = parseInt(btn.dataset.index, 10);
    if (btn.dataset.action === 'edit-period') openPeriodPanel(idx);
    else if (btn.dataset.action === 'delete-period') deletePeriod(idx);
  }, 'periodList');

  console.log('[llmlimit] bindEvents() done — ' + bindOkCount + '/' + bindTotalCount + ' bindings OK');
}

// ── Bootstrap ────────────────────────────────────────────────────────

ready();
