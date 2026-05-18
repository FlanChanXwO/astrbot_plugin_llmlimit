/**
 * Web API 桥接模块 — LLMLimit 插件
 */

console.log('[llmlimit] api.js loaded');

function getBridge() {
  return window.AstrBotPluginPage || null;
}

function handle(resp) {
  if (!resp) return [];
  if (Array.isArray(resp)) return resp;
  if (resp.data !== undefined) return resp.data;
  return resp;
}

function apiError(err) {
  throw new Error(err?.message || err || '未知错误');
}

var ApiModule = {
  async ready() {
    var bridge = getBridge();
    if (!bridge) return;               // bridge not yet loaded — caller handles gracefully
    return await bridge.ready();
  },

  // user limits
  async getUserLimits() {
    var bridge = getBridge();
    if (!bridge) return [];
    try { return handle(await bridge.apiGet('user-limits')); }
    catch (err) { apiError(err); }
  },
  async createUserLimit(item) {
    var bridge = getBridge();
    if (!bridge) throw new Error('API bridge not available');
    try {
      var r = await bridge.apiPost('user-limits/create', item);
      if (r === false || r === null || r === undefined || (r && r.success === false)) {
        throw new Error(r?.error || '添加失败');
      }
      return r;
    } catch (err) { apiError(err); }
  },
  async updateUserLimit(index, item) {
    var bridge = getBridge();
    if (!bridge) throw new Error('API bridge not available');
    try {
      var r = await bridge.apiPost('user-limits/update', { index, ...item });
      if (r === false || r === null || r === undefined || (r && r.success === false)) {
        throw new Error(r?.error || '更新失败');
      }
      return r;
    } catch (err) { apiError(err); }
  },
  async deleteUserLimit(index) {
    var bridge = getBridge();
    if (!bridge) throw new Error('API bridge not available');
    try {
      var r = await bridge.apiPost('user-limits/delete', { index });
      if (r === false || r === null || r === undefined || (r && r.success === false)) {
        throw new Error(r?.error || '删除失败');
      }
      return r;
    } catch (err) { apiError(err); }
  },

  // group limits
  async getGroupLimits() {
    var bridge = getBridge();
    if (!bridge) return [];
    try { return handle(await bridge.apiGet('group-limits')); }
    catch (err) { apiError(err); }
  },
  async createGroupLimit(item) {
    var bridge = getBridge();
    if (!bridge) throw new Error('API bridge not available');
    try {
      var r = await bridge.apiPost('group-limits/create', item);
      if (r === false || r === null || r === undefined || (r && r.success === false)) {
        throw new Error(r?.error || '添加失败');
      }
      return r;
    } catch (err) { apiError(err); }
  },
  async updateGroupLimit(index, item) {
    var bridge = getBridge();
    if (!bridge) throw new Error('API bridge not available');
    try {
      var r = await bridge.apiPost('group-limits/update', { index, ...item });
      if (r === false || r === null || r === undefined || (r && r.success === false)) {
        throw new Error(r?.error || '更新失败');
      }
      return r;
    } catch (err) { apiError(err); }
  },
  async deleteGroupLimit(index) {
    var bridge = getBridge();
    if (!bridge) throw new Error('API bridge not available');
    try {
      var r = await bridge.apiPost('group-limits/delete', { index });
      if (r === false || r === null || r === undefined || (r && r.success === false)) {
        throw new Error(r?.error || '删除失败');
      }
      return r;
    } catch (err) { apiError(err); }
  },

  // time period limits
  async getTimePeriodLimits() {
    var bridge = getBridge();
    if (!bridge) return [];
    try { return handle(await bridge.apiGet('time-period-limits')); }
    catch (err) { apiError(err); }
  },
  async createTimePeriod(item) {
    var bridge = getBridge();
    if (!bridge) throw new Error('API bridge not available');
    try {
      var r = await bridge.apiPost('time-period-limits/create', item);
      if (r === false || r === null || r === undefined || (r && r.success === false)) {
        throw new Error(r?.error || '添加失败');
      }
      return r;
    } catch (err) { apiError(err); }
  },
  async updateTimePeriod(index, item) {
    var bridge = getBridge();
    if (!bridge) throw new Error('API bridge not available');
    try {
      var r = await bridge.apiPost('time-period-limits/update', { index, ...item });
      if (r === false || r === null || r === undefined || (r && r.success === false)) {
        throw new Error(r?.error || '更新失败');
      }
      return r;
    } catch (err) { apiError(err); }
  },
  async deleteTimePeriod(index) {
    var bridge = getBridge();
    if (!bridge) throw new Error('API bridge not available');
    try {
      var r = await bridge.apiPost('time-period-limits/delete', { index });
      if (r === false || r === null || r === undefined || (r && r.success === false)) {
        throw new Error(r?.error || '删除失败');
      }
      return r;
    } catch (err) { apiError(err); }
  },

  // call history
  async getCallHistory(page, pageSize) {
    var bridge = getBridge();
    if (!bridge) return { items: [], total: 0, page: 1, pageSize: 50 };
    page = page || 1;
    pageSize = pageSize || 50;
    try { return handle(await bridge.apiPost('call-history', { page: page, pageSize: pageSize })); }
    catch (err) { apiError(err); }
  },
  async deleteCallHistory(tsList) {
    var bridge = getBridge();
    if (!bridge) throw new Error('API bridge not available');
    try {
      var r = await bridge.apiPost('call-history/delete', { ts_list: tsList });
      if (r === false || r === null || r === undefined || (r && r.success === false)) {
        throw new Error(r?.error || '删除失败');
      }
      return r;
    } catch (err) { apiError(err); }
  },
  async deleteAllCallHistory() {
    var bridge = getBridge();
    if (!bridge) throw new Error('API bridge not available');
    try {
      var r = await bridge.apiPost('call-history/delete', { delete_all: true });
      if (r === false || r === null || r === undefined || (r && r.success === false)) {
        throw new Error(r?.error || '清空失败');
      }
      return r;
    } catch (err) { apiError(err); }
  },
  async cleanupCallHistory(days) {
    var bridge = getBridge();
    if (!bridge) throw new Error('API bridge not available');
    try {
      var r = await bridge.apiPost('call-history/cleanup', { days: days });
      if (r === false || r === null || r === undefined || (r && r.success === false)) {
        throw new Error(r?.error || '清理失败');
      }
      return r;
    } catch (err) { apiError(err); }
  },

  // exempt users
  async getExemptUsers() {
    var bridge = getBridge();
    if (!bridge) return [];
    try { return handle(await bridge.apiGet('exempt-users')); }
    catch (err) { apiError(err); }
  },
  async createExemptUser(userId) {
    var bridge = getBridge();
    if (!bridge) throw new Error('API bridge not available');
    try {
      var r = await bridge.apiPost('exempt-users/create', { userId });
      if (r === false || r === null || r === undefined || (r && r.success === false)) {
        throw new Error(r?.error || '添加失败');
      }
      return r;
    } catch (err) { apiError(err); }
  },
  async deleteExemptUser(userId) {
    var bridge = getBridge();
    if (!bridge) throw new Error('API bridge not available');
    try {
      var r = await bridge.apiPost('exempt-users/delete', { userId });
      if (r === false || r === null || r === undefined || (r && r.success === false)) {
        throw new Error(r?.error || '删除失败');
      }
      return r;
    } catch (err) { apiError(err); }
  },

  // priority users
  async getPriorityUsers() {
    var bridge = getBridge();
    if (!bridge) return [];
    try { return handle(await bridge.apiGet('priority-users')); }
    catch (err) { apiError(err); }
  },
  async createPriorityUser(userId) {
    var bridge = getBridge();
    if (!bridge) throw new Error('API bridge not available');
    try {
      var r = await bridge.apiPost('priority-users/create', { userId });
      if (r === false || r === null || r === undefined || (r && r.success === false)) {
        throw new Error(r?.error || '添加失败');
      }
      return r;
    } catch (err) { apiError(err); }
  },
  async deletePriorityUser(userId) {
    var bridge = getBridge();
    if (!bridge) throw new Error('API bridge not available');
    try {
      var r = await bridge.apiPost('priority-users/delete', { userId });
      if (r === false || r === null || r === undefined || (r && r.success === false)) {
        throw new Error(r?.error || '删除失败');
      }
      return r;
    } catch (err) { apiError(err); }
  },
};

window.ApiModule = ApiModule;
