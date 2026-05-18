"""
配置管理模块

负责加载、解析和验证插件配置。
"""

from __future__ import annotations

import datetime


class ConfigManager:
    """配置管理类 — 从 AstrBotConfig 加载并缓存所有限制配置"""

    def __init__(self, config: dict, data_store=None):
        self.config = config
        self._data_store = data_store
        self.group_limits: dict[str, int] = {}
        self.user_limits: dict[str, int] = {}
        self.group_modes: dict[str, str] = {}
        self.time_period_limits: list[dict] = []
        self.skip_patterns: list[str] = []
        self.exempt_users: set[str] = set()
        self.priority_users: set[str] = set()

    def load(self):
        """加载所有配置项"""
        limits = self.config.get("limits", {})

        if self._data_store:
            data = self._data_store.load()
            self._load_or_migrate_set(data, limits, "exempt_users", self.exempt_users)
            self._load_or_migrate_set(
                data, limits, "priority_users", self.priority_users
            )
            self._load_or_migrate_kv(data, limits, "user_limits", self.user_limits)
            self._load_or_migrate_kv(data, limits, "group_limits", self.group_limits)
            self._load_or_migrate_kv(
                data, limits, "group_mode_settings", self.group_modes
            )
            self._load_or_migrate_time_period(data, limits)
            try:
                from astrbot.api import logger as _log
            except ImportError:
                import logging

                _log = logging.getLogger(__name__)
            _log.info(
                "ConfigManager 从 data_store 加载: exempt=%d, priority=%d, "
                "user_limits=%d, group_limits=%d, group_modes=%d, time_periods=%d",
                len(self.exempt_users),
                len(self.priority_users),
                len(self.user_limits),
                len(self.group_limits),
                len(self.group_modes),
                len(self.time_period_limits),
            )
        else:
            self._parse_text_list(
                limits.get("exempt_users", ""), into_set=self.exempt_users
            )
            self._parse_text_list(
                limits.get("priority_users", ""), into_set=self.priority_users
            )
            self._parse_kv_lines(limits.get("user_limits", ""), self.user_limits)
            self._parse_kv_lines(limits.get("group_limits", ""), self.group_limits)
            self._parse_kv_lines(
                limits.get("group_mode_settings", ""), self.group_modes
            )
            self._parse_time_period_limits(limits.get("time_period_limits", ""))

        self.skip_patterns = limits.get("skip_patterns", ["#", "*"])
        self._validate_reset_time(limits)

    # ── defaults ──────────────────────────────────────────────

    @property
    def default_daily_limit(self) -> int:
        return self.config.get("limits", {}).get("default_daily_limit", 20)

    @property
    def default_weekly_limit(self) -> int:
        return self.config.get("limits", {}).get("default_weekly_limit", 0)

    @property
    def default_monthly_limit(self) -> int:
        return self.config.get("limits", {}).get("default_monthly_limit", 0)

    @property
    def enabled_limit_types(self) -> list[str]:
        return self.config.get("limits", {}).get("enabled_limit_types", ["daily"])

    @property
    def show_remaining_count(self) -> bool:
        return self.config.get("messages", {}).get("show_remaining_count", True)

    @property
    def usage_tip(self) -> str:
        return self.config.get("messages", {}).get(
            "usage_tip",
            "您的 LLM 调用次数已用完（{usage}/{limit}）。请在 {reset_time} 后重试。",
        )

    def get_reset_time(self) -> str:
        return self.config.get("limits", {}).get("daily_reset_time", "00:00")

    def get_weekly_reset_day(self) -> int:
        return self.config.get("limits", {}).get("weekly_reset_day", 1)

    def get_monthly_reset_day(self) -> int:
        return self.config.get("limits", {}).get("monthly_reset_day", 1)

    # ── history ────────────────────────────────────────────────

    @property
    def history_retention_days(self) -> int:
        """历史记录保留天数，0=不自动清理"""
        return int(self.config.get("history", {}).get("retention_days", 30))

    @property
    def max_history_events(self) -> int:
        """最大历史事件数"""
        return int(self.config.get("history", {}).get("max_events", 200))

    # ── helpers ───────────────────────────────────────────────

    def is_exempt(self, user_id: str) -> bool:
        return user_id in self.exempt_users

    def is_priority(self, user_id: str) -> bool:
        return user_id in self.priority_users

    def get_group_mode(self, group_id: str) -> str:
        return self.group_modes.get(str(group_id), "shared")

    def get_user_limit(self, user_id: str) -> int | None:
        return self.user_limits.get(str(user_id))

    def get_group_limit(self, group_id: str) -> int | None:
        return self.group_limits.get(str(group_id))

    # ── parsers ───────────────────────────────────────────────

    @staticmethod
    def _parse_text_list(value, into_set: set):
        """将字符串/列表解析为 set"""
        if isinstance(value, list):
            for item in value:
                into_set.add(str(item).strip())
        elif isinstance(value, str):
            for line in value.strip().split("\n"):
                line = line.strip()
                if line:
                    into_set.add(line)

    @staticmethod
    def _parse_kv_lines(value, target: dict):
        """解析 key:value 行文本"""
        if isinstance(value, list):
            lines = [str(x).strip() for x in value if str(x).strip()]
        elif isinstance(value, str):
            lines = [item.strip() for item in value.strip().split("\n") if item.strip()]
        else:
            return
        for line in lines:
            if ":" in line:
                k, v = line.split(":", 1)
                k, v = k.strip(), v.strip()
                try:
                    target[k] = int(v)
                except ValueError:
                    target[k] = v

    def _parse_time_period_limits(self, value):
        """解析时间段限制 — 格式：HH:MM-HH:MM:次数[:enabled_flag]"""
        if isinstance(value, list):
            lines = [str(x).strip() for x in value if str(x).strip()]
        elif isinstance(value, str):
            lines = [item.strip() for item in value.strip().split("\n") if item.strip()]
        else:
            return

        for line in lines:
            try:
                # Split from right: HH:MM-HH:MM:NUM[:enabled]
                parts = line.rsplit(":", maxsplit=2)
                if len(parts) < 2:
                    continue
                time_range = parts[0]
                limit = int(parts[1])
                enabled = True
                if len(parts) >= 3:
                    enabled = parts[2].strip().lower() in ("true", "1", "yes", "y")
                if not enabled:
                    continue
                start_str, end_str = time_range.split("-", 1)
                datetime.datetime.strptime(start_str.strip(), "%H:%M")
                datetime.datetime.strptime(end_str.strip(), "%H:%M")
                self.time_period_limits.append(
                    {
                        "start_time": start_str.strip(),
                        "end_time": end_str.strip(),
                        "limit": limit,
                    }
                )
            except (ValueError, IndexError):
                continue

    def _validate_reset_time(self, limits: dict):
        reset = limits.get("daily_reset_time", "00:00")
        try:
            h, m = map(int, reset.split(":"))
            if not (0 <= h <= 23 and 0 <= m <= 59):
                raise ValueError
        except (ValueError, AttributeError):
            limits["daily_reset_time"] = "00:00"

    # ── migration helpers ───────────────────────────────────────

    def _load_or_migrate_kv(self, data: dict, limits: dict, key: str, target: dict):
        """从 data_store 加载 kv，或从 AstrBotConfig 迁移旧数据。"""
        if key in data and data[key]:
            # data_store 中有数据，直接使用
            target.update(data[key])
        elif limits.get(key):
            # 从 AstrBotConfig 迁移旧数据
            self._parse_kv_lines(limits.get(key, ""), target)
            if target:
                self._data_store.save(key, target)

    def _load_or_migrate_set(self, data: dict, limits: dict, key: str, target: set):
        """从 data_store 加载 set，或从 AstrBotConfig 迁移旧数据。"""
        if key in data and data[key]:
            # data_store 中以 list 形式存储
            for item in data[key]:
                target.add(str(item).strip())
        elif limits.get(key):
            # 从 AstrBotConfig 迁移旧数据
            self._parse_text_list(limits.get(key, ""), into_set=target)
            if target:
                self._data_store.save(key, sorted(target))

    def _load_or_migrate_time_period(self, data: dict, limits: dict):
        """从 data_store 加载时间段，或从 AstrBotConfig 迁移旧数据。"""
        key = "time_period_limits"
        if key in data and data[key]:
            # data_store 中以 list[dict] 形式存储
            for p in data[key]:
                if isinstance(p, dict) and p.get("enabled", True):
                    self.time_period_limits.append(
                        {
                            "start_time": p["start_time"],
                            "end_time": p["end_time"],
                            "limit": p["limit"],
                        }
                    )
        elif limits.get(key):
            # 从 AstrBotConfig 迁移旧数据
            self._parse_time_period_limits(limits.get(key, ""))
            if self.time_period_limits:
                self._data_store.save(key, self.time_period_limits)
