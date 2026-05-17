# Changelog

## [1.0.0] - 2026-05-17

### Added

- **多维度限流引擎**：支持日限（daily）、周限（weekly）、月限（monthly）以及自定义时间段限制四种维度，可在配置中灵活启用/禁用
- **时间段限制**：支持任意时间段内限次（如 09:00-12:00 最多 5 次），自动解析 `HH:MM-HH:MM:次数[:enabled]` 格式，支持跨天时段（如 22:00-06:00）
- **群组配额模式**：`shared` 模式下群成员共享同一配额，`individual` 模式下每位成员独立计算，支持按群组单独配置
- **用户/群组特定限制**：可为指定用户或指定群组设置独立限额，优先级高于默认限额
- **豁免用户（Exempt Users）**：指定用户完全不受任何限流规则约束
- **优先用户（Priority Users）**：不受群组共享限制影响，仍受个人限额约束
- **跳过模式（Skip Patterns）**：配置前缀（如 `#`、`*`）后，匹配消息不参与限流统计
- **Web UI 管理面板**：`/api/plugin/page/content/astrbot_plugin_llmlimit/llmlimit/` 提供可视化管理页面，支持用户限制、群组限制、时间段限制的增删改查
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
