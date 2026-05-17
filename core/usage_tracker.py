"""
用量追踪模块

通过 AstrBot 内置 KV Store 读写使用次数，不依赖 Redis。
"""

import datetime


class UsageTracker:
    """用量追踪"""

    def __init__(self, plugin):
        self.plugin = plugin

    # ── public ──────────────────────────────────────────────────

    async def get_usage(
        self,
        user_id: str,
        group_id: str | None = None,
        *,
        period_type: str = "daily",
        group_mode: str = "shared",
    ) -> int:
        key = self._build_key(user_id, group_id, period_type, group_mode)
        val = await self.plugin.get_kv_data(key, 0)
        return int(val) if val is not None else 0

    async def increment_usage(
        self,
        user_id: str,
        group_id: str | None = None,
        *,
        period_type: str = "daily",
        group_mode: str = "shared",
    ) -> int:
        """递增计数并返回新值"""
        key = self._build_key(user_id, group_id, period_type, group_mode)
        current = await self.plugin.get_kv_data(key, 0)
        new_val = int(current) + 1 if current else 1
        await self.plugin.put_kv_data(key, new_val)
        return new_val

    async def get_usages_for_status(
        self,
        user_id: str,
        group_id: str | None,
        group_mode: str,
        enabled_types: list[str],
    ) -> dict:
        """批量读取各维度的当前用量，供 /limit_status 展示"""
        result = {}
        for pt in enabled_types:
            key = self._build_key(user_id, group_id, pt, group_mode)
            val = await self.plugin.get_kv_data(key, 0)
            result[pt] = int(val) if val else 0
        return result

    # ── key generation ──────────────────────────────────────────

    def _build_key(
        self,
        user_id: str,
        group_id: str | None,
        period_type: str,
        group_mode: str,
    ) -> str:
        period_key = self._period_key(period_type)
        scope = self._scope(user_id, group_id, group_mode)
        return f"usage:{period_type}:{period_key}:{scope}"

    def _scope(self, user_id: str, group_id: str | None, group_mode: str) -> str:
        if group_id:
            if group_mode == "shared":
                return f"group:{group_id}:shared"
            return f"group:{group_id}:user:{user_id}"
        return f"user:{user_id}"

    def _period_key(self, period_type: str) -> str:
        """生成当前时间对应的周期键"""
        now = datetime.datetime.now()
        if period_type == "daily":
            return self._daily_period_key(now)
        elif period_type == "weekly":
            return self._weekly_period_key(now)
        elif period_type == "monthly":
            return self._monthly_period_key(now)
        elif period_type == "timeperiod":
            return self._daily_period_key(now)  # time period 按日重置
        return self._daily_period_key(now)

    def _daily_period_key(self, now: datetime.datetime) -> str:
        reset_str = self.plugin.config.get("limits", {}).get(
            "daily_reset_time", "00:00"
        )
        h, m = map(int, reset_str.split(":"))
        reset_moment = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if now < reset_moment:
            now = now - datetime.timedelta(days=1)
        return now.strftime("%Y-%m-%d")

    def _weekly_period_key(self, now: datetime.datetime) -> str:
        reset_day = self.plugin.config.get("limits", {}).get("weekly_reset_day", 1)
        reset_str = self.plugin.config.get("limits", {}).get(
            "daily_reset_time", "00:00"
        )
        h, m = map(int, reset_str.split(":"))
        reset_moment = now.replace(hour=h, minute=m, second=0, microsecond=0)
        # ISO weekday: 1=Monday … 7=Sunday
        current_iso = now.isocalendar()
        current_weekday = current_iso[2]
        # 如果还没到本周的 reset 日/时间，用上一周
        if current_weekday < reset_day or (
            current_weekday == reset_day and now < reset_moment
        ):
            now = now - datetime.timedelta(days=7)
        iso = now.isocalendar()
        return f"{iso[0]}-W{iso[1]}"

    def _monthly_period_key(self, now: datetime.datetime) -> str:
        reset_day = self.plugin.config.get("limits", {}).get("monthly_reset_day", 1)
        reset_str = self.plugin.config.get("limits", {}).get(
            "daily_reset_time", "00:00"
        )
        h, m = map(int, reset_str.split(":"))
        reset_moment = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if now.day < reset_day or (now.day == reset_day and now < reset_moment):
            if now.month == 1:
                now = now.replace(year=now.year - 1, month=12)
            else:
                now = now.replace(month=now.month - 1)
        return now.strftime("%Y-%m")
