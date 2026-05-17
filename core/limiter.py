from __future__ import annotations

"""
核心限制逻辑模块

负责编排多维度速率限制决策：决定一个 LLM 请求是否应该被允许。
"""

from .config_manager import ConfigManager
from .time_period_manager import TimePeriodManager
from .usage_tracker import UsageTracker


class Limiter:
    """核心限制引擎 — 纯策略编排，不持有存储逻辑"""

    def __init__(
        self,
        config_mgr: ConfigManager,
        tracker: UsageTracker,
        time_period_mgr: TimePeriodManager,
    ):
        self.config = config_mgr
        self.tracker = tracker
        self.time_period = time_period_mgr

    # ── decision ───────────────────────────────────────────────

    async def decide(
        self,
        user_id: str,
        group_id: str | None = None,
    ) -> LimiterDecision:
        """
        对一次 LLM 请求执行完整的限制决策。

        返回 LimiterDecision，其中 allowed 表示是否放行，
        detail 包含用于消息展示的详细信息。
        """
        # 1. 豁免用户
        if self.config.is_exempt(user_id):
            return LimiterDecision(allowed=True, exempt=True)

        group_mode = self.config.get_group_mode(group_id) if group_id else "individual"
        enabled = self.config.enabled_limit_types

        # 2. 时间段限制 (最高优先级限制)
        tp_limit = self.time_period.get_current_limit()
        tp_index = self.time_period.get_active_period_index()
        if tp_limit is not None:
            usage = await self.tracker.get_usage(
                user_id,
                group_id,
                period_type="timeperiod",
                group_mode=group_mode if group_id else "individual",
            )
            tp_key = f"timeperiod:tp_{tp_index}"
            if usage >= tp_limit:
                return LimiterDecision(
                    allowed=False,
                    usage=usage,
                    limit=tp_limit,
                    limit_type=tp_key,
                    group_mode=group_mode,
                )
            # 时间段内：只记 timeperiod，不记 daily/weekly/monthly
            return LimiterDecision(
                allowed=True,
                usage=usage,
                limit=tp_limit,
                limit_type=tp_key,
                group_mode=group_mode,
                track_as="timeperiod",
            )

        # 3. 用户特定限制
        user_limit = self.config.get_user_limit(user_id)
        if user_limit is not None:
            usage = await self.tracker.get_usage(
                user_id,
                group_id=None,
                period_type="daily",
                group_mode="individual",
            )
            if usage >= user_limit:
                return LimiterDecision(
                    allowed=False,
                    usage=usage,
                    limit=user_limit,
                    limit_type="user_specific",
                )
            return LimiterDecision(
                allowed=True,
                usage=usage,
                limit=user_limit,
                limit_type="user_specific",
                track_as="daily",
            )

        # 4. 群组特定限制
        if group_id:
            group_limit = self.config.get_group_limit(group_id)
            if group_limit is not None:
                usage = await self.tracker.get_usage(
                    user_id,
                    group_id,
                    period_type="daily",
                    group_mode=group_mode,
                )
                if usage >= group_limit:
                    return LimiterDecision(
                        allowed=False,
                        usage=usage,
                        limit=group_limit,
                        limit_type="group_specific",
                        group_mode=group_mode,
                    )
                return LimiterDecision(
                    allowed=True,
                    usage=usage,
                    limit=group_limit,
                    limit_type="group_specific",
                    group_mode=group_mode,
                    track_as="daily",
                )

        # 5. 默认限制 — 按优先级 daily > weekly > monthly
        for pt in enabled:
            if pt == "timeperiod":
                continue
            limit = self._default_limit_for(pt)
            if limit <= 0:
                continue
            usage = await self.tracker.get_usage(
                user_id,
                group_id,
                period_type=pt,
                group_mode=group_mode,
            )
            if usage >= limit:
                return LimiterDecision(
                    allowed=False,
                    usage=usage,
                    limit=limit,
                    limit_type=pt,
                    group_mode=group_mode,
                )
            return LimiterDecision(
                allowed=True,
                usage=usage,
                limit=limit,
                limit_type=pt,
                group_mode=group_mode,
                track_as=pt,
            )

        # 没有任何限制配置 → 放行
        return LimiterDecision(allowed=True, unlimited=True)

    # ── helpers ─────────────────────────────────────────────────

    def _default_limit_for(self, period_type: str) -> int:
        if period_type == "daily":
            return self.config.default_daily_limit
        elif period_type == "weekly":
            return self.config.default_weekly_limit
        elif period_type == "monthly":
            return self.config.default_monthly_limit
        return 0


# ── decision DTO ──────────────────────────────────────────────────


class LimiterDecision:
    """一次限制决策的结果"""

    def __init__(
        self,
        allowed: bool,
        usage: int = 0,
        limit: int = 0,
        limit_type: str = "",
        group_mode: str = "individual",
        exempt: bool = False,
        unlimited: bool = False,
        track_as: str | None = None,
    ):
        self.allowed = allowed
        self.usage = usage
        self.limit = limit
        self.limit_type = limit_type
        self.group_mode = group_mode
        self.exempt = exempt
        self.unlimited = unlimited
        self.track_as = track_as  # 用什么 period_type 来记录本次使用
