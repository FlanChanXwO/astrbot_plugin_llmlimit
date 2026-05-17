"""
消息构建模块

负责生成限制相关提示消息，支持模板变量替换。
"""


class MessageBuilder:
    """消息构建器 — 将决策结果渲染为用户可见的提示文本"""

    def __init__(self, config: dict):
        self.config = config

    def build_exceeded(
        self,
        usage: int,
        limit: int,
        limit_type: str = "daily",
    ) -> str:
        tip = self.config.get("messages", {}).get(
            "usage_tip",
            "您的 LLM 调用次数已用完（{usage}/{limit}）。请在 {reset_time} 后重试。",
        )
        remaining = max(0, limit - usage)
        return (
            tip.replace("{usage}", str(usage))
            .replace("{limit}", str(limit))
            .replace("{remaining}", str(remaining))
            .replace("{limit_type}", self.type_label(limit_type))
            .replace("{reset_time}", self._reset_time_for(limit_type))
        )

    def build_status(
        self,
        user_id: str,
        usages: dict[str, int],
        limits: dict[str, int],
        exempt: bool,
        group_mode: str = "individual",
    ) -> str:
        if exempt:
            return "您是豁免用户，不受 LLM 调用限制。"

        lines = ["📊 **LLM 调用状态**"]
        for pt, usage in usages.items():
            limit = limits.get(pt, 0)
            if limit <= 0:
                continue
            pct = (usage / limit * 100) if limit > 0 else 0
            bar = self._bar(usage, limit)
            lines.append(
                f"• {self.type_label(pt)}: {usage}/{limit} {bar} ({pct:.0f}%)"
            )
        if group_mode == "shared" and "daily" in usages:
            lines.append("[!] 当前群组使用共享配额，所有成员共用限额。")
        return "\n".join(lines)

    # ── helpers ──────────────────────────────────────────────

    @staticmethod
    def type_label(limit_type: str) -> str:
        labels = {
            "daily": "今日",
            "weekly": "本周",
            "monthly": "本月",
            "user_specific": "个人限制",
            "group_specific": "群组限制",
        }
        if limit_type.startswith("timeperiod"):
            return "当前时段"
        return labels.get(limit_type, limit_type)

    def _reset_time_for(self, limit_type: str) -> str:
        if limit_type == "daily":
            return self.config.get("limits", {}).get("daily_reset_time", "00:00")
        elif limit_type == "weekly":
            day_map = {1: "周一", 7: "周日"}
            day = self.config.get("limits", {}).get("weekly_reset_day", 1)
            return day_map.get(day, f"周{day}")
        elif limit_type == "monthly":
            day = self.config.get("limits", {}).get("monthly_reset_day", 1)
            return f"每月{day}日"
        return "下次重置"

    @staticmethod
    def _bar(usage: int, limit: int, width: int = 8) -> str:
        if limit <= 0:
            return ""
        filled = min(width, int(width * usage / limit))
        return "█" * filled + "░" * (width - filled)
