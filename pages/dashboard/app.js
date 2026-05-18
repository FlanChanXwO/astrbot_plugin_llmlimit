const api = window.ApiModule;

console.log('[llmlimit] app.js loaded');

// ── State ────────────────────────────────────────────────────────────

const state = {
  activeTab: 'users',
  userLimits: [],
  groupLimits: [],
  timePeriodLimits: [],
  historyItems: [],
  historyPage: 1,
  historyPageSize: 50,
  historyTotal: 0,
  historySelected: new Set(),
  exemptUsers: [],
  priorityUsers: [],
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
  tabHistory: $('#tabHistory'),
  tabExempt: $('#tabExempt'),
  tabPriority: $('#tabPriority'),
  historyList: $('#historyList'),
  btnRefreshHistory: $('#btnRefreshHistory'),
  btnDeleteAllHistory: $('#btnDeleteAllHistory'),
  cbSelectAll: $('#cbSelectAll'),
  btnDeleteSelected: $('#btnDeleteSelected'),
  selPageSize: $('#selPageSize'),
  historyPagination: $('#historyPagination'),
  historyToolbar: $('#historyToolbar'),
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
  btnAddUser: $('#btnAddUser'),
  btnAddGroup: $('#btnAddGroup'),
  btnAddPeriod: $('#btnAddPeriod'),
  btnAddExempt: $('#btnAddExempt'),
  btnAddPriority: $('#btnAddPriority'),
  exemptList: $('#exemptList'),
  priorityList: $('#priorityList'),
  exemptForm: $('#exemptForm'),
  priorityForm: $('#priorityForm'),
  inputExemptUserId: $('#inputExemptUserId'),
  inputPriorityUserId: $('#inputPriorityUserId'),
};

// ── Lifecycle ────────────────────────────────────────────────────────

async function ready() {
  try { initTheme(); } catch (e) { console.warn('[llmlimit] initTheme failed:', e); }
  bindEvents();
  document.body.classList.add('js-loaded');

  // 等待 AstrBotPluginPage 桥接注入（服务器动态注入为最后一个 <script>）
  for (var retries = 0; retries < 50 && !window.AstrBotPluginPage; retries++) {
    await new Promise(function (r) { setTimeout(r, 100); });
  }

  if (!window.AstrBotPluginPage) {
    console.warn('[llmlimit] AstrBotPluginPage bridge not available after waiting');
    return;
  }

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
    const [users, groups, timePeriods, exemptUsers, priorityUsers] = await Promise.all([
      api.getUserLimits(),
      api.getGroupLimits(),
      api.getTimePeriodLimits(),
      api.getExemptUsers(),
      api.getPriorityUsers(),
    ]);
    state.userLimits = users || [];
    state.groupLimits = groups || [];
    state.timePeriodLimits = timePeriods || [];
    state.exemptUsers = exemptUsers || [];
    state.priorityUsers = priorityUsers || [];
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
  renderExemptList();
  renderPriorityList();
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

function renderExemptList() {
  const list = state.exemptUsers;
  if (list.length === 0) {
    dom.exemptList.innerHTML = '<div class="empty-state"><p>暂无豁免用户，点击「添加用户」开始配置。</p></div>';
    return;
  }
  dom.exemptList.innerHTML = list.map((userId) => `
    <div class="item-row">
      <div class="item-info">
        <div class="item-name">
          ${escHtml(userId)}
          <span class="item-badge badge-success">豁免</span>
        </div>
        <div class="item-meta">用户ID: ${escHtml(userId)}</div>
      </div>
      <div class="item-actions">
        <button class="btn btn-sm btn-danger-outline" data-action="delete-exempt" data-user-id="${escHtml(userId)}">删除</button>
      </div>
    </div>
  `).join('');
}

function renderPriorityList() {
  const list = state.priorityUsers;
  if (list.length === 0) {
    dom.priorityList.innerHTML = '<div class="empty-state"><p>暂无优先用户，点击「添加用户」开始配置。</p></div>';
    return;
  }
  dom.priorityList.innerHTML = list.map((userId) => `
    <div class="item-row">
      <div class="item-info">
        <div class="item-name">
          ${escHtml(userId)}
          <span class="item-badge badge-primary">优先</span>
        </div>
        <div class="item-meta">用户ID: ${escHtml(userId)}</div>
      </div>
      <div class="item-actions">
        <button class="btn btn-sm btn-danger-outline" data-action="delete-priority" data-user-id="${escHtml(userId)}">删除</button>
      </div>
    </div>
  `).join('');
}

async function loadHistory() {
  state.historySelected = new Set();
  try {
    var data = await api.getCallHistory(state.historyPage, state.historyPageSize);
    state.historyItems = (data && data.items) ? data.items : [];
    state.historyTotal = (data && data.total) ? data.total : 0;
  } catch (err) {
    state.historyItems = [];
    state.historyTotal = 0;
  }
  renderHistoryList();
  renderHistoryPagination();
}

function renderHistoryList() {
  var list = state.historyItems;
  if (list.length === 0) {
    dom.historyToolbar.style.display = 'none';
    dom.historyList.innerHTML = '<div class="empty-state"><p>暂无调用记录。</p></div>';
    return;
  }
  dom.historyToolbar.style.display = '';
  var hasSelected = state.historySelected.size > 0;
  dom.btnDeleteSelected.disabled = !hasSelected;
  dom.cbSelectAll.checked = list.length > 0 && list.every(function (e) { return state.historySelected.has(e.ts); });
  var rows = list.map(function (e) {
    var d = new Date(e.ts * 1000);
    var time = d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    var date = d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' });
    var checked = state.historySelected.has(e.ts) ? ' checked' : '';
    var resultBadge = e.allowed
      ? '<span class="item-badge badge-success">放行</span>'
      : '<span class="item-badge badge-warning">拦截</span>';
    var typeLabel = e.limit_type || 'daily';
    var usageInfo = e.limit > 0 ? (e.usage + '/' + e.limit) : '-';
    return '<tr>' +
      '<td><label class="checkbox-inline"><input type="checkbox" class="cb-row" data-ts="' + e.ts + '"' + checked + '/></label></td>' +
      '<td>' + escHtml(date + ' ' + time) + '</td>' +
      '<td title="' + escHtml(e.user_id) + '">' + escHtml(e.user_id.substring(0, 12)) + '</td>' +
      '<td>' + escHtml(e.group_id ? e.group_id.substring(0, 12) : '-') + '</td>' +
      '<td>' + resultBadge + '</td>' +
      '<td>' + escHtml(typeLabel) + '</td>' +
      '<td>' + escHtml(usageInfo) + '</td>' +
      '<td class="msg-preview" title="' + escHtml(e.msg_preview) + '">' + escHtml(e.msg_preview.substring(0, 30)) + '</td>' +
      '</tr>';
  });
  dom.historyList.innerHTML = '<table class="history-table"><thead><tr>' +
    '<th style="width:32px"></th><th>时间</th><th>用户</th><th>群</th><th>结果</th><th>类型</th><th>用量</th><th>消息</th>' +
    '</tr></thead><tbody>' + rows.join('') + '</tbody></table>';
}

function renderHistoryPagination() {
  var total = state.historyTotal;
  var page = state.historyPage;
  var pageSize = state.historyPageSize;
  if (total <= 0) {
    dom.historyPagination.innerHTML = '';
    return;
  }
  var totalPages = Math.ceil(total / pageSize);
  var html = '<span class="pagination-info">第 ' + page + '/' + totalPages + ' 页，共 ' + total + ' 条</span>';
  html += '<button class="btn btn-sm btn-secondary" ' + (page <= 1 ? 'disabled' : '') + ' data-page="' + (page - 1) + '">上一页</button>';
  html += '<button class="btn btn-sm btn-secondary" ' + (page >= totalPages ? 'disabled' : '') + ' data-page="' + (page + 1) + '">下一页</button>';
  dom.historyPagination.innerHTML = html;
}

function changePage(newPage) {
  if (newPage < 1) return;
  var totalPages = Math.ceil(state.historyTotal / state.historyPageSize);
  if (newPage > totalPages) return;
  state.historyPage = newPage;
  loadHistory();
}

function changePageSize(newSize) {
  state.historyPageSize = newSize;
  state.historyPage = 1;
  loadHistory();
}

function toggleSelectAll() {
  var allTs = state.historyItems.map(function (e) { return e.ts; });
  if (dom.cbSelectAll.checked) {
    allTs.forEach(function (ts) { state.historySelected.add(ts); });
  } else {
    allTs.forEach(function (ts) { state.historySelected.delete(ts); });
  }
  renderHistoryList();
}

function toggleSelectRow(ts, checked) {
  if (checked) {
    state.historySelected.add(ts);
  } else {
    state.historySelected.delete(ts);
  }
  dom.btnDeleteSelected.disabled = state.historySelected.size === 0;
  dom.cbSelectAll.checked = state.historyItems.length > 0 && state.historyItems.every(function (e) { return state.historySelected.has(e.ts); });
}

async function deleteSelectedHistory() {
  if (state.historySelected.size === 0) return;
  var ok = await confirmDialog('确认删除', '确定要删除选中的 ' + state.historySelected.size + ' 条记录吗？此操作不可撤销。');
  if (!ok) return;
  try {
    var tsList = Array.from(state.historySelected);
    var r = await api.deleteCallHistory(tsList);
    showToast('已删除 ' + (r && r.removed ? r.removed : tsList.length) + ' 条记录');
    state.historySelected = new Set();
    loadHistory();
  } catch (err) {
    showToast('删除失败: ' + err.message, 'error');
  }
}

async function deleteAllHistory() {
  var ok = await confirmDialog('清空全部', '确定要清空所有调用历史记录吗？此操作不可撤销。');
  if (!ok) return;
  try {
    var r = await api.deleteAllCallHistory();
    showToast('已清空 ' + (r && r.removed ? r.removed : '全部') + ' 条记录');
    state.historyPage = 1;
    state.historySelected = new Set();
    loadHistory();
  } catch (err) {
    showToast('清空失败: ' + err.message, 'error');
  }
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
  dom.tabHistory.hidden = tab !== 'history';
  dom.tabExempt.hidden = tab !== 'exempt';
  dom.tabPriority.hidden = tab !== 'priority';
  if (tab === 'history') {
    loadHistory();
  }
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

function openExemptPanel() {
  state.editingUserIndex = -1;
  state.editingGroupIndex = -1;
  state.editingPeriodIndex = -1;
  dom.inputExemptUserId.value = '';
  dom.panelTitle.textContent = '添加豁免用户';
  showPanel('exemptForm');
}

function openPriorityPanel() {
  state.editingUserIndex = -1;
  state.editingGroupIndex = -1;
  state.editingPeriodIndex = -1;
  dom.inputPriorityUserId.value = '';
  dom.panelTitle.textContent = '添加优先用户';
  showPanel('priorityForm');
}

function showPanel(formId) {
  dom.userForm.hidden = formId !== 'userForm';
  dom.groupForm.hidden = formId !== 'groupForm';
  dom.periodForm.hidden = formId !== 'periodForm';
  dom.exemptForm.hidden = formId !== 'exemptForm';
  dom.priorityForm.hidden = formId !== 'priorityForm';
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

// ── CRUD: exempt users ────────────────────────────────────────────────

async function saveExemptUser(e) {
  e.preventDefault();
  const userId = dom.inputExemptUserId.value.trim();
  if (!userId) { showToast('用户ID不能为空', 'error'); return; }
  try {
    await api.createExemptUser(userId);
    showToast('豁免用户已添加');
    closePanel();
    await loadAll();
  } catch (err) {
    showToast('添加失败: ' + err.message, 'error');
  }
}

async function deleteExemptUser(userId) {
  const ok = await confirmDialog('确认删除', `确定要将用户 ${userId} 从豁免名单中移除吗？`);
  if (!ok) return;
  try {
    await api.deleteExemptUser(userId);
    showToast('豁免用户已删除');
    await loadAll();
  } catch (err) {
    showToast('删除失败: ' + err.message, 'error');
  }
}

// ── CRUD: priority users ──────────────────────────────────────────────

async function savePriorityUser(e) {
  e.preventDefault();
  const userId = dom.inputPriorityUserId.value.trim();
  if (!userId) { showToast('用户ID不能为空', 'error'); return; }
  try {
    await api.createPriorityUser(userId);
    showToast('优先用户已添加');
    closePanel();
    await loadAll();
  } catch (err) {
    showToast('添加失败: ' + err.message, 'error');
  }
}

async function deletePriorityUser(userId) {
  const ok = await confirmDialog('确认删除', `确定要将用户 ${userId} 从优先名单中移除吗？`);
  if (!ok) return;
  try {
    await api.deletePriorityUser(userId);
    showToast('优先用户已删除');
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

  // Panel
  safely(dom.panelClose, 'click', closePanel, 'panelClose');
  safely(dom.panelOverlay, 'click', closePanel, 'panelOverlay');

  // Add buttons
  safely(dom.btnAddUser, 'click', () => openUserPanel(-1), 'btnAddUser');
  safely(dom.btnAddGroup, 'click', () => openGroupPanel(-1), 'btnAddGroup');
  safely(dom.btnAddPeriod, 'click', () => openPeriodPanel(-1), 'btnAddPeriod');
  safely(dom.btnAddExempt, 'click', openExemptPanel, 'btnAddExempt');
  safely(dom.btnAddPriority, 'click', openPriorityPanel, 'btnAddPriority');

  // Form submissions
  safely(dom.userForm, 'submit', saveUser, 'userForm');
  safely(dom.groupForm, 'submit', saveGroup, 'groupForm');
  safely(dom.periodForm, 'submit', savePeriod, 'periodForm');
  safely(dom.exemptForm, 'submit', saveExemptUser, 'exemptForm');
  safely(dom.priorityForm, 'submit', savePriorityUser, 'priorityForm');

  // Form cancel buttons
  safely(document.querySelector('#userFormCancel'), 'click', closePanel, 'userFormCancel');
  safely(document.querySelector('#groupFormCancel'), 'click', closePanel, 'groupFormCancel');
  safely(document.querySelector('#periodFormCancel'), 'click', closePanel, 'periodFormCancel');
  safely(document.querySelector('#exemptFormCancel'), 'click', closePanel, 'exemptFormCancel');
  safely(document.querySelector('#priorityFormCancel'), 'click', closePanel, 'priorityFormCancel');

  // Period enabled toggle label
  safely(dom.inputPeriodEnabled, 'change', updatePeriodToggleLabel, 'inputPeriodEnabled');

  // Confirm dialog
  safely(dom.confirmOk, 'click', () => closeConfirm(true), 'confirmOk');
  safely(dom.confirmCancel, 'click', () => closeConfirm(false), 'confirmCancel');

  // Refresh history
  safely(dom.btnRefreshHistory, 'click', loadHistory, 'btnRefreshHistory');

  // Delete all history
  safely(dom.btnDeleteAllHistory, 'click', deleteAllHistory, 'btnDeleteAllHistory');

  // Select all history
  safely(dom.cbSelectAll, 'change', toggleSelectAll, 'cbSelectAll');

  // Delete selected history
  safely(dom.btnDeleteSelected, 'click', deleteSelectedHistory, 'btnDeleteSelected');

  // Page size selector
  safely(dom.selPageSize, 'change', function () { changePageSize(parseInt(dom.selPageSize.value, 10)); }, 'selPageSize');

  // History pagination
  safely(dom.historyPagination, 'click', function (e) {
    var btn = e.target.closest('[data-page]');
    if (btn) changePage(parseInt(btn.dataset.page, 10));
  }, 'historyPagination');

  // History table row checkboxes
  safely(dom.historyList, 'click', function (e) {
    var cb = e.target.closest('.cb-row');
    if (cb) {
      var ts = parseFloat(cb.dataset.ts);
      toggleSelectRow(ts, cb.checked);
    }
  }, 'historyListCheckboxes');

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

  safely(dom.exemptList, 'click', (e) => {
    const btn = e.target.closest('[data-action]');
    if (!btn) return;
    if (btn.dataset.action === 'delete-exempt') deleteExemptUser(btn.dataset.userId);
  }, 'exemptList');

  safely(dom.priorityList, 'click', (e) => {
    const btn = e.target.closest('[data-action]');
    if (!btn) return;
    if (btn.dataset.action === 'delete-priority') deletePriorityUser(btn.dataset.userId);
  }, 'priorityList');

  console.log('[llmlimit] bindEvents() done — ' + bindOkCount + '/' + bindTotalCount + ' bindings OK');
}

// ── Bootstrap ────────────────────────────────────────────────────────

ready();
