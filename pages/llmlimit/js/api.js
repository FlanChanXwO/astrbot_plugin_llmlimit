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
};

window.ApiModule = ApiModule;
