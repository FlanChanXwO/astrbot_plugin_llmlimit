# CLAUDE.md — astrbot_plugin_llmlimit

AstrBot plugin for multi-dimensional LLM call rate limiting.

## Project overview

- **Language**: Python 3.12
- **Framework**: AstrBot v4.24.x plugin system
- **Architecture**: DDD-layered `core/` module
- **Zero external dependencies**: storage via AstrBot KV Store only (no Redis)

## Directory structure

```
main.py                    # Plugin entry, hooks, commands, REST API handlers
metadata.yaml              # Plugin metadata (name, version, author, repo)
_conf_schema.json           # AstrBot config UI schema
core/
  config_manager.py        # Config loading, parsing, validation
  usage_tracker.py         # Usage counting + KV storage read/write
  time_period_manager.py   # Time period matching logic
  limiter.py               # 5-tier priority rate-limit decision engine
  message_builder.py       # Message template rendering
  utils/
    logger.py              # LLMLimitLogger — [llmlimit]-prefixed logging
pages/
  llmlimit/
    index.html             # Web UI (vanilla JS, no framework)
    app.js                 # State management + DOM rendering + CRUD logic
    js/
      api.js               # Bridge to window.AstrBotPluginPage (REST calls)
      theme.js             # Light/dark toggle with localStorage persistence
    css/                   # 7 CSS files: base, components, forms, panels,
                           #   notifications, responsive, dark-theme
tests/                     # 57 pytest + pytest-asyncio unit tests
```

## Key conventions

### Rate limit decision chain (5-tier priority)

1. **Exempt users** — skip all limits
2. **Priority users** — skip shared group limits, still personal
3. **Time period limits** — override other limits during configured periods
4. **Per-user / Per-group limits** — specific overrides
5. **Default limits** — daily/weekly/monthly fallback

### Config field types (AstrBot v4.24.5)

All key-value lists use `type: "list"` (not `type: "text"` or `type: "object"`). Supported config types: `int/float/bool/string/text/list/file/object/template_list`.

### KV Store key format

```
usage:{period_type}:{period_key}:{scope}
```

Period keys are date-based (daily: `YYYY-MM-DD`, weekly: `YYYY-Www`, monthly: `YYYY-MM`). Reading with a new period key = stateless reset (no background tasks needed).

### Web UI

- Pages auto-discovered by AstrBot from `pages/<page_name>/index.html` subdirectories
- No `register_web_page()` API exists in AstrBot v4.x
- `window.AstrBotPluginPage` bridge injected by server as last `<script>` before `</body>`
- All APIs registered via `context.register_web_api(route, handler, methods, desc)` — **4 positional args required, including `desc`**
- All JS uses plain `<script>` tags (no modules, no frameworks)

### Testing

- `pytest + pytest-asyncio`, 57 tests
- Mock patterns: `MagicMock` / `AsyncMock`, config built with `_build_config()`
- Test files: `test_config_manager.py`, `test_limiter.py`, `test_message_builder.py`, `test_time_period_manager.py`, `test_usage_tracker.py`

## Code rules

- Python 3.9 compat: use `from __future__ import annotations` for `X | None` syntax
- Logger formatting: `logger.info("msg %s", arg)` — `%` placeholders, not `{}`
- `@filter.command_group` decorator: non-async, no params (Dashboard compatibility)
- Plugin version bump: update `main.py` `@register(...)` decorator, `metadata.yaml`, and `CHANGELOG.md`
- Releases: automatic via `release-from-changelog.yml` GitHub Actions workflow on CHANGELOG.md push to master

### Ruff

- **每次修改 Python 文件后必须运行** `ruff check .` 确保 0 errors
- **提交前运行** `ruff check . --fix` 自动修复可修复的问题
- Target version: Python 3.12，默认规则集
- 已确认的误报豁免（6 × E402，`ruff --fix` 已自动修复 UP037 和 F401）：
  - `core/config_manager.py:9: E402` ← `from __future__ import annotations` 在模块 docstring 前，符合 Python 规范
  - `core/limiter.py:9-11: E402` ← 同上
  - `core/time_period_manager.py:9: E402` ← 同上
  - `core/usage_tracker.py:9: E402` ← 同上
