from __future__ import annotations

"""
时间段管理模块

负责时间段限制的解析、匹配和管理。
"""

import datetime


class TimePeriodManager:
    """时间段管理类 — 解析时间段配置并判断当前是否在某个时间段内"""

    def __init__(self, time_period_limits):
        self.time_period_limits = time_period_limits

    def get_current_limit(self) -> int | None:
        """返回当前时间所处的第一段时间段限制，不在任何时间段内返回 None"""
        now = datetime.datetime.now().time()
        for period in self.time_period_limits:
            if self._is_in_period(now, period["start_time"], period["end_time"]):
                return period["limit"]
        return None

    def get_active_period_index(self) -> int | None:
        """返回当前时间所处的第一段时间段的索引，不在任何时间段内返回 None"""
        now = datetime.datetime.now().time()
        for i, period in enumerate(self.time_period_limits):
            if self._is_in_period(now, period["start_time"], period["end_time"]):
                return i
        return None

    @staticmethod
    def _is_in_period(current: datetime.time, start_str: str, end_str: str) -> bool:
        """判断当前时间是否在 [start, end] 内（支持跨天，如 22:00-06:00）"""
        start = datetime.datetime.strptime(start_str, "%H:%M").time()
        end = datetime.datetime.strptime(end_str, "%H:%M").time()
        if start <= end:
            return start <= current <= end
        else:
            return current >= start or current <= end
