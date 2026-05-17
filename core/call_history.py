from __future__ import annotations

import json
import time
from typing import Any

HISTORY_KEY = "history:recent"
MAX_EVENTS = 200


class CallHistoryTracker:
    """记录并查询逐次 LLM 调用历史（最近 200 条）。"""

    def __init__(self, plugin: Any):
        self._plugin = plugin

    async def record(
        self,
        *,
        user_id: str,
        group_id: str | None = None,
        allowed: bool,
        limit_type: str = "",
        usage: int = 0,
        limit: int = 0,
        msg_preview: str = "",
    ) -> None:
        event = {
            "ts": time.time(),
            "user_id": user_id,
            "group_id": group_id or "",
            "allowed": allowed,
            "limit_type": limit_type,
            "usage": usage,
            "limit": limit,
            "msg_preview": msg_preview,
        }
        raw = await self._plugin.get_kv_data(HISTORY_KEY, "[]")
        try:
            events: list[dict] = json.loads(raw) if raw else []
        except (json.JSONDecodeError, TypeError):
            events = []
        events.insert(0, event)
        if len(events) > MAX_EVENTS:
            events = events[:MAX_EVENTS]
        await self._plugin.put_kv_data(HISTORY_KEY, json.dumps(events, ensure_ascii=False))

    async def get_recent(self, n: int = MAX_EVENTS) -> list[dict]:
        raw = await self._plugin.get_kv_data(HISTORY_KEY, "[]")
        try:
            events: list[dict] = json.loads(raw) if raw else []
        except (json.JSONDecodeError, TypeError):
            return []
        return events[:n]
