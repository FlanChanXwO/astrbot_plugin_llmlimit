# Changelog

## [1.2.0] - 2026-05-18

### Added

- **独立持久化层**：`core/data_store.py` PluginDataStore，Web UI 管理的 6 类数据（用户限制/群组限制/群组模式/时间段限制/豁免用户/优先用户）独立于 AstrBotConfig 存储为 `plugin_data.json`，不受 `check_config_integrity()` 影响
- **数据迁移机制**：`ConfigManager._load_or_migrate_*()` 首批从 AstrBotConfig 迁移旧数据到独立存储，后续优先从独立存储读取

### Changed

- **`_conf_schema.json`**：移除 6 个 `type: "text"` 的 Web UI 管理字段，仅保留标量配置项
- **`main.py`**：通过 `StarTools.get_data_dir(plugin_name="astrbot_plugin_llmlimit")` 获取数据目录，6 个 `_save_*()` 方法改为写入 PluginDataStore
- **页面目录**：`pages/llmlimit/` → `pages/dashboard/` 重命名

### Fixed

- **插件重载后 Web UI 数据丢失**：PluginDataStore 独立持久化，数据不再被 AstrBotConfig 完整性检查清除
- **Web UI 页面加载时不显示已有数据**：`app.js` ready() 轮询等待 `window.AstrBotPluginPage` 桥接注入后再调用 `loadAll()`

### Testing

- 新增 `TestDataStore` 测试类 10 个用例
- 测试总计 82 passed（+10）

---

## [1.1.0] - 2026-05-17

### Added

- **Web UI 管理面板**：`pages/llmlimit/` 提供可视化配置页面，访问路径 `/api/plugin/page/content/astrbot_plugin_llmlimit/llmlimit/`
  - 三个 Tab 页签：用户限制 / 群组限制 / 时间段限制
  - 增删改查弹窗表单，含确认对话框防误删
  - Toast 通知 + 空状态提示
  - 浅色/深色主题切换，偏好记忆到 `localStorage`
  - 响应式布局适配移动端
- **Logger 包装器**：`core/utils/logger.py` 提供 `LLMLimitLogger`，统一以 `[llmlimit]` 前缀输出日志，基于 rsshub `PrefixedLogger` 模式，支持 `debug/info/warning/error/fatal`
- **REST API 端点**（供 Web UI 调用）：
  - `GET /llmlimit/user-limits` / `POST /llmlimit/user-limits/create` / `update` / `delete`
  - `GET /llmlimit/group-limits` / `POST /llmlimit/group-limits/create` / `update` / `delete`
  - `GET /llmlimit/time-period-limits` / `POST /llmlimit/time-period-limits/create` / `update` / `delete`
- **`.gitignore` 修复**：例外规则 `!pages/llmlimit/lib/` 确保 `petite-vue.iife.js` 前端库正常纳入版本管理

### Changed

- **页面目录结构**：从平铺的 `pages/` 改为 `pages/llmlimit/` 子目录，符合 AstrBot `_discover_plugin_pages()` 自动发现机制
- **`main.py`**：移除无效的 `register_web_page()` 调用（AstrBot v4.x 无此 API，页面由自动发现机制提供）
- **Web UI 从 PetiteVue 迁移至原生 JS**：移除 `petite-vue.iife.js` 依赖
  - `app.js`：使用原生 DOM API（`querySelector`、事件委托、`innerHTML` 模板拼接）实现状态管理和渲染
  - `api.js`：去除 `export` 关键字，改为 `window.ApiModule` 全局暴露
  - `theme.js`：去除 `export` 关键字，改为 `window.initThemeNative` / `window.toggleThemeNative` 全局暴露
  - 所有脚本以 `<script>` 非 module 方式加载，零外部框架依赖

### Fixed

- **按钮无法交互**：`api.js` 在模块加载时一次性捕获 `window.AstrBotPluginPage`，当 bridge SDK 脚本（由服务器在 `</body>` 前注入）尚未执行时 `bridge` 始终为 `null`，导致 `api.ready()` 在 `await` 前同步抛出异常，`ready()` 流程提前中断，`bindEvents()` 从未被调用。修复：`getBridge()` 动态读取 `window.AstrBotPluginPage`（每次调用都检查），`api.ready()` 在 bridge 不存在时静默返回，`ready()` 将 `initTheme()` + `bindEvents()` 移出 `try` 块确保始终执行
- **`confirm-dialog-overlay` 初始可见**：缺少 `opacity: 0; pointer-events: none` 默认样式，导致确认弹窗在未调用 `confirmDialog()` 时就覆盖全屏，拦截所有按钮点击

---

## [1.0.0] - 2026-05-17

### Added

- **多维度限流引擎**：支持日限（daily）、周限（weekly）、月限（monthly）以及自定义时间段限制四种维度，可在配置中灵活启用/禁用
- **时间段限制**：支持任意时间段内限次（如 09:00-12:00 最多 5 次），自动解析 `HH:MM-HH:MM:次数[:enabled]` 格式，支持跨天时段（如 22:00-06:00）
- **群组配额模式**：`shared` 模式下群成员共享同一配额，`individual` 模式下每位成员独立计算，支持按群组单独配置
- **用户/群组特定限制**：可为指定用户或指定群组设置独立限额，优先级高于默认限额
- **豁免用户（Exempt Users）**：指定用户完全不受任何限流规则约束
- **优先用户（Priority Users）**：不受群组共享限制影响，仍受个人限额约束
- **跳过模式（Skip Patterns）**：配置前缀（如 `#`、`*`）后，匹配消息不参与限流统计
- **管理命令**：`/limit_admin set_user/set_group/set_mode/remove_user/remove_group/list` — 管理员可实时调整限制规则
- **用户状态查询**：`/limit_status` — 展示当前各维度用量进度条（含百分比和可视化进度条）
- **冷却机制**：超额提醒消息 300 秒防刷，避免短时间内重复发送限流通知
- **AstrBot KV Store 存储**：完全基于 AstrBot 内置 KV 存储，零外部依赖，无需 Redis
- **插件配置 Schema**：`_conf_schema.json` 提供完整可视化配置界面

### Architecture

- **DDD 分层架构**：`core/` 模块职责清晰分离
  - `config_manager.py` — 配置加载、解析、验证
  - `usage_tracker.py` — 用量计数与 KV 存储读写
  - `time_period_manager.py` — 时间段匹配逻辑
  - `limiter.py` — 五级优先级限流决策引擎
  - `message_builder.py` — 消息模板渲染（支持自定义模板变量）
- **主入口精简**：`main.py` 仅 273 行，专注于插件注册、Hook 绑定与命令分发

### Testing

- **单元测试覆盖**：57 个测试用例，使用 pytest + pytest-asyncio
  - `test_config_manager.py` — 配置解析、默认值、豁免/优先用户、时间段解析
  - `test_time_period_manager.py` — 正常时段、跨天时段、多时段重叠等边界情况
  - `test_usage_tracker.py` — 周期 Key 生成、Key 格式、增量计数、批量读取
  - `test_limiter.py` — 五级优先级决策链、放行/拦截场景全覆盖
  - `test_message_builder.py` — 超额消息、状态消息、类型标签
- **代码规范**：通过 ruff 检查（0 errors），Python 3.12 目标版本

### Added — v1.0.0-rc1

- 初始开发阶段基础框架搭建
