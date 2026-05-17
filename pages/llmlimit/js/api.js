/**
 * Web API 桥接模块 — LLMLimit 插件
 */

const bridge = typeof window !== 'undefined' ? window.AstrBotPluginPage : null;

export async function ready() {
  if (!bridge) throw new Error('AstrBotPluginPage bridge not available');
  return await bridge.ready();
}

// ── helpers ────────────────────────────────────────────────────────

function handle(resp) {
  if (!resp) return [];
  if (Array.isArray(resp)) return resp;
  if (resp.data !== undefined) return resp.data;
  return resp;
}

function apiError(err) {
  throw new Error(err?.message || err || '未知错误');
}

// ── user limits ────────────────────────────────────────────────────

export async function getUserLimits() {
  try {
    return handle(await bridge.apiGet('user-limits'));
  } catch (err) { apiError(err); }
}

export async function createUserLimit(item) {
  try {
    const r = await bridge.apiPost('user-limits/create', item);
    if (r === false || r === null || r === undefined || (r && r.success === false)) {
      throw new Error(r?.error || '添加失败');
    }
    return r;
  } catch (err) { apiError(err); }
}

export async function updateUserLimit(index, item) {
  try {
    const r = await bridge.apiPost('user-limits/update', { index, ...item });
    if (r === false || r === null || r === undefined || (r && r.success === false)) {
      throw new Error(r?.error || '更新失败');
    }
    return r;
  } catch (err) { apiError(err); }
}

export async function deleteUserLimit(index) {
  try {
    const r = await bridge.apiPost('user-limits/delete', { index });
    if (r === false || r === null || r === undefined || (r && r.success === false)) {
      throw new Error(r?.error || '删除失败');
    }
    return r;
  } catch (err) { apiError(err); }
}

// ── group limits ───────────────────────────────────────────────────

export async function getGroupLimits() {
  try {
    return handle(await bridge.apiGet('group-limits'));
  } catch (err) { apiError(err); }
}

export async function createGroupLimit(item) {
  try {
    const r = await bridge.apiPost('group-limits/create', item);
    if (r === false || r === null || r === undefined || (r && r.success === false)) {
      throw new Error(r?.error || '添加失败');
    }
    return r;
  } catch (err) { apiError(err); }
}

export async function updateGroupLimit(index, item) {
  try {
    const r = await bridge.apiPost('group-limits/update', { index, ...item });
    if (r === false || r === null || r === undefined || (r && r.success === false)) {
      throw new Error(r?.error || '更新失败');
    }
    return r;
  } catch (err) { apiError(err); }
}

export async function deleteGroupLimit(index) {
  try {
    const r = await bridge.apiPost('group-limits/delete', { index });
    if (r === false || r === null || r === undefined || (r && r.success === false)) {
      throw new Error(r?.error || '删除失败');
    }
    return r;
  } catch (err) { apiError(err); }
}

// ── time period limits ─────────────────────────────────────────────

export async function getTimePeriodLimits() {
  try {
    return handle(await bridge.apiGet('time-period-limits'));
  } catch (err) { apiError(err); }
}

export async function createTimePeriod(item) {
  try {
    const r = await bridge.apiPost('time-period-limits/create', item);
    if (r === false || r === null || r === undefined || (r && r.success === false)) {
      throw new Error(r?.error || '添加失败');
    }
    return r;
  } catch (err) { apiError(err); }
}

export async function updateTimePeriod(index, item) {
  try {
    const r = await bridge.apiPost('time-period-limits/update', { index, ...item });
    if (r === false || r === null || r === undefined || (r && r.success === false)) {
      throw new Error(r?.error || '更新失败');
    }
    return r;
  } catch (err) { apiError(err); }
}

export async function deleteTimePeriod(index) {
  try {
    const r = await bridge.apiPost('time-period-limits/delete', { index });
    if (r === false || r === null || r === undefined || (r && r.success === false)) {
      throw new Error(r?.error || '删除失败');
    }
    return r;
  } catch (err) { apiError(err); }
}
