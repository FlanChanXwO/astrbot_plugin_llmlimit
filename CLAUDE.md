# CLAUDE.md — astrbot_plugin_llmlimit

AstrBot plugin for multi-dimensional LLM call rate limiting.

## Project overview

- **Language**: Python 3.12
- **Framework**: AstrBot v4.24.x plugin system
- **Architecture**: DDD-layered `core/` module
- **Zero external dependencies**: storage via AstrBot KV Store + independent JSON persistence

## Communication language

**Must communicate with the user in Chinese (中文).** All user-facing responses must be in Chinese.

## Skills

**Prefer using the `astrbot-dev-skill` when writing or modifying this plugin.** It provides AstrBot-specific API references, decorators, hook signatures, config schema rules, and platform adapter patterns — reducing guesswork and preventing signature mismatches.

If the skill is not available in the current session, ask the user whether they want to install it:

> 当前未加载 astrbot-dev-skill，建议安装以提升 AstrBot 插件开发效率。是否安装？
> - 项目本地安装：`npx skills add xunxiing/AstrBot-Skill`
> - 全局安装（所有项目可用）：`npx skills add -g xunxiing/AstrBot-Skill`
> - 或手动下载：https://github.com/xunxiing/AstrBot-Skill/tree/v4

## Directory structure

```
main.py                    # Plugin entry, hooks, commands, REST API handlers
metadata.yaml              # Plugin metadata (name, version, author, repo)
_conf_schema.json          # AstrBot config UI schema (scalar fields only)
CHANGELOG.md               # Release changelog
core/
  config_manager.py        # Config loading, parsing, validation, data_store integration
  data_store.py            # PluginDataStore — independent JSON persistence for Web UI data
  usage_tracker.py         # Usage counting + KV storage read/write
  time_period_manager.py   # Time period matching logic
  limiter.py               # 5-tier priority rate-limit decision engine
  message_builder.py       # Message template rendering
  call_history.py          # LLM call history tracking + pagination
  utils/
    logger.py              # LLMLimitLogger — [llmlimit]-prefixed logging
pages/
  dashboard/
    index.html             # Web UI (vanilla JS, no framework)
    app.js                 # State management + DOM rendering + CRUD logic
    js/
      api.js               # Bridge to window.AstrBotPluginPage (REST calls)
      theme.js             # Light/dark toggle with localStorage persistence
    css/                   # 7 CSS files: base, components, forms, panels,
                           #   notifications, responsive, dark-theme
tests/                     # 82 pytest + pytest-asyncio unit tests
```

## Key conventions

### Rate limit decision chain (5-tier priority)

1. **Exempt users** — skip all limits
2. **Priority users** — skip shared group limits, still personal
3. **Time period limits** — override other limits during configured periods
4. **Per-user / Per-group limits** — specific overrides
5. **Default limits** — daily/weekly/monthly fallback

### Independent persistence layer (v1.2.0+)

Web UI-managed data (6 categories: user_limits, group_limits, group_mode_settings, time_period_limits, exempt_users, priority_users) is stored in `plugin_data.json` via `PluginDataStore`, independent of `AstrBotConfig`. This prevents data loss from `check_config_integrity()` which strips keys not defined in `_conf_schema.json`.

- `PluginDataStore` is initialized with the path from `StarTools.get_data_dir(plugin_name="astrbot_plugin_llmlimit")`
- `ConfigManager.__init__` accepts optional `data_store` parameter; when present, `load()` reads from data_store with migration from AstrBotConfig as fallback
- All `_save_*()` methods in `main.py` write to `PluginDataStore`, not `self.config["limits"]`

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
- `app.js` polls for bridge availability (up to 5s) before calling `loadAll()` to avoid race condition
- All APIs registered via `context.register_web_api(route, handler, methods, desc)` — **4 positional args required, including `desc`**
- All JS uses plain `<script>` tags (no modules, no frameworks)

### Testing

- `pytest + pytest-asyncio`, 82 tests
- Mock patterns: `MagicMock` / `AsyncMock`, config built with `_build_config()`
- Test files: `test_call_history.py`, `test_config_manager.py`, `test_limiter.py`, `test_message_builder.py`, `test_time_period_manager.py`, `test_usage_tracker.py`
- `test_config_manager.py` includes `TestDataStore` class (10 tests) for `PluginDataStore` integration

## Code rules

- Python 3.9 compat: use `from __future__ import annotations` for `X | None` syntax
- Logger formatting: `logger.info("msg %s", arg)` — `%` placeholders, not `{}`
- `@filter.command_group` decorator: non-async, no params (Dashboard compatibility)
- Plugin version bump: update `main.py` `@register(...)` decorator, `metadata.yaml`, and `CHANGELOG.md`
- Releases: automatic via `release-from-changelog.yml` GitHub Actions workflow on CHANGELOG.md push to master

### Ruff

- **Must run** `ruff check .` **after every Python file modification** to ensure 0 errors
- **Run** `ruff check . --fix` **before committing** to auto-fix fixable issues
- Target version: Python 3.12, default rule set
- Confirmed false-positive suppressions (9 × E402, `ruff --fix` has auto-fixed UP037 and F401):
  - `core/config_manager.py:9: E402` ← `from __future__ import annotations` placed before module docstring, compliant with Python spec
  - `core/data_store.py:10-12: E402` ← same as above
  - `core/limiter.py:9-11: E402` ← same as above
  - `core/time_period_manager.py:9: E402` ← same as above
  - `core/usage_tracker.py:9: E402` ← same as above

## MCP tools

If you have MCP tools available, use them as follows. Tool names may vary between MCP servers — identify them by their capabilities rather than exact names.

### IDE / code intelligence tools

Tools that provide IDE-level operations for project files belong to this category. Look for tool names like:
- `get_file_text_by_path` / `read_file` — reading files
- `find_files_by_name_keyword` / `search_file` / `find_files_by_glob` — locating files
- `search_in_files_by_text` / `search_in_files_by_regex` — searching code
- `get_symbol_info` — inspecting symbols
- `get_file_problems` — running inspections (lint/type errors)
- `build_project` — triggering builds

**When available, prefer these over raw Bash `grep` / `find` / `cat` for exploring and editing Python files.** They provide richer context and catch issues early.

### Browser / UI testing tools (Playwright-like)

Tools that control a real browser for UI testing. Look for: `browser_navigate`, `browser_snapshot`, `browser_click`, `browser_take_screenshot`, `browser_console_messages`.

**Only use these for UI-related tasks** — testing `pages/dashboard/` rendering, verifying button interactions, debugging layout/CSS issues. Navigate to `http://localhost:6185` to access the AstrBot dashboard, then go to the plugin page at `/api/plugin/page/content/astrbot_plugin_llmlimit/dashboard/`.

**Do NOT use browser tools for code search, file reading, or non-UI debugging.**

### LSP / code navigation tools

Tools that provide language server protocol features: completions, hover info, go-to-definition, cross-references. Use for understanding code structure and symbol relationships.

## Maintenance

**This file must be updated when significant code changes occur.** Including but not limited to:

- Directory structure changes (add/delete/move/rename files or modules)
- Core logic changes (rate-limit decision chain, KV storage format, API route rules)
- New/removed external dependencies
- Test framework or mock pattern changes
- Build/deployment process changes

Commit this file after updates to ensure accurate code context in future AI sessions.
