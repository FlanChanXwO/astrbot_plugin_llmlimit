# LLMLimit 插件（astrbot_plugin_llmlimit）

<div align="center">

<img src="https://raw.githubusercontent.com/FlanChanXwO/astrbot_plugin_llmlimit/master/logo.png" width="400" alt="llmlimit 插件"/>

<br/>

<img src="https://count.getloli.com/@astrbot_plugin_llmlimit?name=astrbot_plugin_llmlimit&theme=rule34&padding=7&offset=0&align=top&scale=1&pixelated=1&darkmode=auto" alt="Moe Counter">

**精准控制 LLM 的调用频率与使用额度，支持日/周/月/自定义时间段的多维度限流策略。**

防止 Bot 被刷、控制 API 成本、合理分配资源。

[![License: AGPL](https://img.shields.io/badge/License-AGPL-blue.svg)](LICENSE)
![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue)
![AstrBot](https://img.shields.io/badge/AstrBot-%E2%89%A54.24.0-green)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey)

</div>

本插件完全开源免费，欢迎 Issue 和 PR。

---

## ✨ 功能特性

- ⚡ **多维度限流** — 日限、周限、月限、自定义时间段限制，可按需启用/禁用
- 👥 **灵活配额** — 群组共享配额（shared）/ 独立配额（individual）两种模式
- 🎯 **精准控制** — 针对特定用户、特定群组设置独立限额，覆盖默认值
- 🛡️ **豁免/优先** — 豁免用户完全不受限，优先用户跳过群组共享限制
- 🔧 **Web UI 管理面板** — 可视化配置用户限制/群组限制/时间段/豁免名单/优先用户/调用历史
- 📊 **调用历史追踪** — 记录每次 LLM 调用详情（放行/拦截、用量、消息预览），支持分页浏览和批量清理
- 🧊 **冷却机制** — 超额消息 300 秒冷却，避免短时间重复刷屏
- 💾 **独立持久化** — Web UI 管理数据独立于 AstrBotConfig 存储，插件重载不丢失
- 🚫 **零外部依赖** — 基于 AstrBot 内置 KV 存储 + JSON 文件持久化，无需 Redis

---

## 📦 安装

### 方式一：通过 AstrBot 插件市场安装（推荐）

在 AstrBot 管理面板中搜索 `astrbot_plugin_llmlimit` 并安装。

### 方式二：手动安装

1. 克隆本仓库到 AstrBot 的插件目录：
   ```bash
   cd AstrBot/data/plugins
   git clone https://github.com/FlanChanXwO/astrbot_plugin_llmlimit.git
   ```
2. 重启 AstrBot 或重载插件

---

## 🛠️ 配置项

在 AstrBot 管理面板中配置以下选项：

### 基础限制设置

| 配置项 | 类型 | 说明 | 默认值 |
|--------|------|------|--------|
| `default_daily_limit` | 整数 | 默认每日限制次数（0=不限制） | `20` |
| `default_weekly_limit` | 整数 | 默认每周限制次数（0=不启用） | `0` |
| `default_monthly_limit` | 整数 | 默认每月限制次数（0=不启用） | `0` |
| `daily_reset_time` | 字符串 | 每日重置时间（HH:MM） | `00:00` |
| `weekly_reset_day` | 整数 | 每周重置日（1=周一，7=周日） | `1` |
| `monthly_reset_day` | 整数 | 每月重置日（1-28，超出取月末） | `1` |
| `enabled_limit_types` | 列表 | 启用的限制维度（可选 `daily`/`weekly`/`monthly`/`timeperiod`） | `["daily"]` |
| `skip_patterns` | 列表 | 以此前缀开头的消息跳过限流检查且不计入次数 | `["#", "*"]` |

### 历史记录设置

| 配置项 | 类型 | 说明 | 默认值 |
|--------|------|------|--------|
| `max_events` | 整数 | 调用历史最大保留条数（50-10000） | `200` |
| `retention_days` | 整数 | 调用历史保留天数（0=不自动清理） | `30` |

### 消息设置

| 配置项 | 类型 | 说明 | 默认值 |
|--------|------|------|--------|
| `show_remaining_count` | 布尔 | 到达限制时是否向用户显示剩余次数 | `true` |
| `usage_tip` | 文本 | 使用提示模板（支持 `{usage}`/`{limit}`/`{remaining}`/`{limit_type}`/`{reset_time}` 占位符） | 见配置面板 |

> **注意**：Web UI 管理的 6 类数据（用户限制、群组限制、群组模式、时间段限制、豁免用户、优先用户）通过独立持久化层存储，不在上述配置表中。请通过 Web UI 面板或管理命令进行管理。

---

## 📝 使用方法

### 用户命令

发送以下指令查看当前使用状态：

```
/limit_status
```

输出示例：当前各维度的已用次数、总额度、剩余次数（含进度条）。

### 管理员命令 (需要 ADMIN 权限)

#### 限额管理

| 命令 | 说明 |
|------|------|
| `/limit_admin list` | 列出所有自定义限制（用户/群组/群组模式/时间段） |
| `/limit_admin set_user <用户ID> <次数>` | 设置用户特定限制 |
| `/limit_admin set_group <群ID> <次数>` | 设置群组特定限制 |
| `/limit_admin set_mode <群ID> <shared\|individual>` | 设置群组配额模式 |
| `/limit_admin remove_user <用户ID>` | 移除用户特定限制 |
| `/limit_admin remove_group <群ID>` | 移除群组特定限制 |
| `/limit_admin clear <用户ID>` | 重置用户当前周期额度 |

#### 使用示例

```
/limit_admin set_user 123456789 100
/limit_admin set_group 987654321 50
/limit_admin set_mode 987654321 shared
/limit_admin remove_user 123456789
/limit_admin list
```

---

## 🔗 限制优先级（5 级）

1. **豁免用户** — 完全跳过所有限制，不计数
2. **优先用户** — 跳过群组共享配额限制，仍受个人限制
3. **自定义时间段限制** — 特定时段内限次，覆盖其他限制
4. **用户/群组特定限制** — 指定对象独立限额
5. **默认限制** — 日限 / 周限 / 月限兜底

任一启用维度超额即拦截。

---

## 🧩 架构

```
astrbot_plugin_llmlimit/
├── main.py                  # 插件入口、Hook 注册、命令处理、REST API
├── metadata.yaml            # 插件元数据
├── _conf_schema.json        # 配置 Schema（标量字段）
├── CHANGELOG.md             # 版本更新日志
├── core/
│   ├── config_manager.py    # 配置加载、解析、验证、data_store 集成
│   ├── data_store.py        # PluginDataStore — Web UI 数据独立 JSON 持久化
│   ├── limiter.py           # 五级优先级限流决策引擎
│   ├── usage_tracker.py     # 用量追踪（AstrBot KV Store）
│   ├── time_period_manager.py  # 时间段匹配逻辑
│   ├── message_builder.py   # 消息模板渲染
│   ├── call_history.py      # LLM 调用历史记录与分页
│   └── utils/
│       └── logger.py        # [llmlimit] 前缀日志输出
├── pages/
│   └── dashboard/           # Web UI 管理面板（原生 JS，零框架）
│       ├── index.html
│       ├── app.js
│       ├── js/api.js
│       ├── js/theme.js
│       └── css/             # 7 个 CSS 文件
└── tests/                   # 82 个单元测试（pytest + pytest-asyncio）
```

---

## 📋 Web UI 面板

插件提供完整的管理面板，访问路径：`/api/plugin/page/content/astrbot_plugin_llmlimit/dashboard/`

六个 Tab 页签：

| 页签 | 功能 |
|------|------|
| 用户限制 | 增删改查用户特定限额 |
| 群组限制 | 增删改查群组特定限额 |
| 时间段限制 | 增删改查自定义时间段限制，支持启用/停用 |
| 调用历史 | 分页浏览调用记录，支持全选批量删除、清空全部 |
| 豁免名单 | 添加/移除豁免用户 |
| 优先用户 | 添加/移除优先用户 |

---

## 🔄 限流流程

```
消息到达
  → 检查 skip_patterns（匹配则放行不计数）
  → 检查豁免用户（匹配则放行不计数）
  → 检查各启用维度用量（daily/weekly/monthly/timeperiod）
  → 任一维度超额 → 记录拦截 → 发送冷却提示
  → 全部未超额 → 记录放行 → 增量计数 → 剩余量提醒（1/3/5 次时）
```

---

## 📄 开源协议

本项目基于 [AGPL](LICENSE) 协议开源。
