# astrbot_plugin_llmlimit

精准控制 LLM 的调用频率与使用额度，支持日/周/月/自定义时间段的多维度限流策略。

防止 Bot 被刷、控制 API 成本、合理分配资源。

## 特性

- **多维度限流**：支持日限、周限、月限、自定义时间段限制
- **灵活配额**：支持群组共享配额 / 独立配额两种模式
- **精准控制**：可针对特定用户、特定群组设置独立限额
- **豁免/优先**：支持豁免用户（无限制）和优先用户（不参与群组共享限制）
- **无需 Redis**：使用 AstrBot 内置 KV 存储，零外部依赖
- **冷却机制**：防止短时间内重复发送"已达上限"消息

## 安装

将插件目录放入 AstrBot 的 `data/plugins/` 目录：

```
data/plugins/astrbot_plugin_llmlimit/
```

## 配置

在 AstrBot 插件配置界面中配置，或在 `_conf_schema.json` 中查看完整配置项。

### 主要配置项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `default_daily_limit` | 默认每日限次 | 20 |
| `default_weekly_limit` | 默认每周限次 (0=不启用) | 0 |
| `default_monthly_limit` | 默认每月限次 (0=不启用) | 0 |
| `daily_reset_time` | 每日重置时间 (HH:MM) | 00:00 |
| `weekly_reset_day` | 每周重置日 (1=周一) | 1 |
| `monthly_reset_day` | 每月重置日 (1-28) | 1 |
| `exempt_users` | 豁免用户 ID（一行一个） | — |
| `priority_users` | 优先用户 ID（一行一个） | — |
| `user_limits` | 用户特定限制（格式：`用户ID:次数`） | — |
| `group_limits` | 群组特定限制（格式：`群ID:次数`） | — |
| `group_mode_settings` | 群组模式（格式：`群ID:shared` 或 `群ID:individual`） | shared |
| `time_period_limits` | 时间段限制（格式：`HH:MM-HH:MM:次数[:enabled]`） | — |
| `skip_patterns` | 忽略的消息前缀 | `#`, `*` |
| `enabled_limit_types` | 启用的限制维度 | `["daily"]` |

### 限制优先级

1. 豁免用户 → 无限制
2. 时间段限制 → 特定时段限次
3. 用户特定限制 → 指定用户单独限次
4. 群组特定限制 → 指定群组单独限次
5. 默认限制 → 日/周/月

## 命令

### 用户命令

| 命令 | 说明 |
|------|------|
| `/limit_status` | 查看当前 LLM 调用使用状态 |

### 管理员命令 (需要 ADMIN 权限)

| 命令 | 说明 |
|------|------|
| `/limit_admin list` | 列出所有自定义限制 |
| `/limit_admin set_user <用户ID> <次数>` | 设置用户特定限制 |
| `/limit_admin set_group <群ID> <次数>` | 设置群组特定限制 |
| `/limit_admin set_mode <群ID> <shared\|individual>` | 设置群组配额模式 |
| `/limit_admin remove_user <用户ID>` | 移除用户特定限制 |
| `/limit_admin remove_group <群ID>` | 移除群组特定限制 |

## 架构

```
astrbot_plugin_llmlimit/
├── main.py              # 插件入口、Hook 注册、命令处理
├── metadata.yaml        # 插件元数据
├── _conf_schema.json    # 配置 Schema
├── requirements.txt     # 依赖声明
└── core/
    ├── __init__.py
    ├── config_manager.py    # 配置加载与解析
    ├── limiter.py           # 限流决策引擎
    ├── usage_tracker.py     # 用量追踪 (AstrBot KV Store)
    ├── time_period_manager.py # 时间段管理
    └── message_builder.py   # 消息构建
```

## License

AGPL v3
