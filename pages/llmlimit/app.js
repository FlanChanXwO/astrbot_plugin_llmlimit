import * as api from './api.js';

let toastTimer = null;

// ── lifecycle ──────────────────────────────────────────────────────

function ready() {
  return api.ready().then(() => {
    loadAll();
  });
}

// ── data loading ───────────────────────────────────────────────────

async function loadAll() {
  try {
    const [users, groups, timePeriods] = await Promise.all([
      api.getUserLimits(),
      api.getGroupLimits(),
      api.getTimePeriodLimits(),
    ]);
    store.userLimits = users || [];
    store.groupLimits = groups || [];
    store.timePeriodLimits = timePeriods || [];
  } catch (err) {
    showToast('加载失败: ' + err.message, 'error');
  }
}

// ── CRUD helpers ───────────────────────────────────────────────────

function showToast(message, type = 'success') {
  store.toast = { show: true, message, type };
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    store.toast.show = false;
  }, 3000);
}

function confirmDialog(title, message) {
  return new Promise((resolve) => {
    store.dialog = { show: true, title, message, okText: '确定', okClass: 'btn-danger', resolve };
  });
}

// ── reactive store ─────────────────────────────────────────────────

const store = PetiteVue.reactive({
  // tabs
  activeTab: 'users',

  // data
  userLimits: [],
  groupLimits: [],
  timePeriodLimits: [],

  // user limit form
  userForm: { userId: '', limit: '' },
  editingUserIndex: -1,

  // group limit form
  groupForm: { groupId: '', limit: '' },
  editingGroupIndex: -1,

  // time period form
  periodForm: { start: '09:00', end: '12:00', limit: '5', enabled: true },
  editingPeriodIndex: -1,

  // panel
  panelVisible: false,
  panelExpanded: false,

  // dialog
  dialog: { show: false, title: '', message: '', okText: '确定', okClass: 'btn-danger', resolve: null },

  // toast
  toast: { show: false, message: '', type: 'success' },

  // ── user limit actions ──
  openUserPanel(index = -1) {
    this.editingUserIndex = index;
    if (index >= 0) {
      this.userForm = {
        userId: this.userLimits[index].userId || '',
        limit: this.userLimits[index].limit || '',
      };
    } else {
      this.userForm = { userId: '', limit: '' };
    }
    this.panelVisible = true;
    this.panelExpanded = false;
  },

  async saveUser() {
    const { userId, limit } = this.userForm;
    if (!userId.trim()) {
      showToast('用户ID不能为空', 'error');
      return;
    }
    const lim = parseInt(limit, 10);
    if (isNaN(lim) || lim <= 0) {
      showToast('请输入有效的次数（正整数）', 'error');
      return;
    }

    try {
      if (this.editingUserIndex >= 0) {
        await api.updateUserLimit(this.editingUserIndex, { userId: userId.trim(), limit: lim });
        showToast('用户限制已更新');
      } else {
        await api.createUserLimit({ userId: userId.trim(), limit: lim });
        showToast('用户限制已添加');
      }
      this.panelVisible = false;
      await loadAll();
    } catch (err) {
      showToast('保存失败: ' + err.message, 'error');
    }
  },

  async removeUser(index) {
    const item = this.userLimits[index];
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
  },

  // ── group limit actions ──
  openGroupPanel(index = -1) {
    this.editingGroupIndex = index;
    if (index >= 0) {
      this.groupForm = {
        groupId: this.groupLimits[index].groupId || '',
        limit: this.groupLimits[index].limit || '',
      };
    } else {
      this.groupForm = { groupId: '', limit: '' };
    }
    this.panelVisible = true;
    this.panelExpanded = false;
  },

  async saveGroup() {
    const { groupId, limit } = this.groupForm;
    if (!groupId.trim()) {
      showToast('群ID不能为空', 'error');
      return;
    }
    const lim = parseInt(limit, 10);
    if (isNaN(lim) || lim <= 0) {
      showToast('请输入有效的次数（正整数）', 'error');
      return;
    }

    try {
      if (this.editingGroupIndex >= 0) {
        await api.updateGroupLimit(this.editingGroupIndex, { groupId: groupId.trim(), limit: lim });
        showToast('群组限制已更新');
      } else {
        await api.createGroupLimit({ groupId: groupId.trim(), limit: lim });
        showToast('群组限制已添加');
      }
      this.panelVisible = false;
      await loadAll();
    } catch (err) {
      showToast('保存失败: ' + err.message, 'error');
    }
  },

  async removeGroup(index) {
    const item = this.groupLimits[index];
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
  },

  // ── time period actions ──
  openPeriodPanel(index = -1) {
    this.editingPeriodIndex = index;
    if (index >= 0) {
      const p = this.timePeriodLimits[index];
      this.periodForm = { start: p.startTime, end: p.endTime, limit: String(p.limit), enabled: p.enabled };
    } else {
      this.periodForm = { start: '09:00', end: '12:00', limit: '5', enabled: true };
    }
    this.panelVisible = true;
    this.panelExpanded = false;
  },

  async savePeriod() {
    const { start, end, limit, enabled } = this.periodForm;
    const lim = parseInt(limit, 10);
    if (isNaN(lim) || lim <= 0) {
      showToast('请输入有效的次数（正整数）', 'error');
      return;
    }

    try {
      if (this.editingPeriodIndex >= 0) {
        await api.updateTimePeriod(this.editingPeriodIndex, { startTime: start, endTime: end, limit: lim, enabled });
        showToast('时间段已更新');
      } else {
        await api.createTimePeriod({ startTime: start, endTime: end, limit: lim, enabled });
        showToast('时间段已添加');
      }
      this.panelVisible = false;
      await loadAll();
    } catch (err) {
      showToast('保存失败: ' + err.message, 'error');
    }
  },

  async removePeriod(index) {
    const item = this.timePeriodLimits[index];
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
  },

  // ── panel ──
  closePanel() {
    this.panelVisible = false;
    this.editingUserIndex = -1;
    this.editingGroupIndex = -1;
    this.editingPeriodIndex = -1;
  },

  toggleExpand() {
    this.panelExpanded = !this.panelExpanded;
  },

  async confirmDialogOk() {
    if (this.dialog.resolve) {
      this.dialog.resolve(true);
    }
    this.dialog.show = false;
  },

  confirmDialogCancel() {
    if (this.dialog.resolve) {
      this.dialog.resolve(false);
    }
    this.dialog.show = false;
  },
});

PetiteVue.start(store, document.body);
