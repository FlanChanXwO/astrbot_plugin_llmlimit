from __future__ import annotations

import json
import time
from typing import Any

HISTORY_KEY = "history:recent"


class CallHistoryTracker:
    """记录并查询逐次 LLM 调用历史（支持分页、批量删除、按时间清理）。"""

    def __init__(self, plugin: Any):
        self._plugin = plugin

    # ── internal helpers ────────────────────────────────────────

    async def _load_all(self) -> list[dict]:
        raw = await self._plugin.get_kv_data(HISTORY_KEY, "[]")
        try:
            return json.loads(raw) if raw else []
        except (json.JSONDecodeError, TypeError):
            return []

    async def _save(self, events: list[dict]) -> None:
        await self._plugin.put_kv_data(
            HISTORY_KEY, json.dumps(events, ensure_ascii=False)
        )

    async def _load_and_trim(self) -> list[dict]:
        """加载并截断到 max_history_events"""
        events = await self._load_all()
        max_count = self._plugin.config_mgr.max_history_events
        if len(events) > max_count:
            events = events[:max_count]
            await self._save(events)
        return events

    # ── queries ─────────────────────────────────────────────────

    async def get_total_count(self) -> int:
        events = await self._load_all()
        return len(events)

    async def get_paginated(self, page: int, page_size: int) -> dict:
        events = await self._load_and_trim()
        total = len(events)
        start = (page - 1) * page_size
        return {
            "items": events[start : start + page_size],
            "total": total,
            "page": page,
            "pageSize": page_size,
        }

    async def get_recent(self, n: int | None = None) -> list[dict]:
        if n is None:
            n = self._plugin.config_mgr.max_history_events
        events = await self._load_all()
        return events[:n]

    # ── mutations ───────────────────────────────────────────────

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
        events = await self._load_all()
        events.insert(0, event)
        # 数量截断
        max_count = self._plugin.config_mgr.max_history_events
        if len(events) > max_count:
            events = events[:max_count]
        # 按时间清理
        retention = self._plugin.config_mgr.history_retention_days
        if retention > 0:
            events = self._trim_old(events, retention)
        await self._save(events)

    async def delete_by_timestamps(self, ts_list: list[float]) -> int:
        ts_set = set(ts_list)
        events = await self._load_all()
        before = len(events)
        events = [e for e in events if e["ts"] not in ts_set]
        removed = before - len(events)
        await self._save(events)
        return removed

    async def delete_all(self) -> int:
        events = await self._load_all()
        count = len(events)
        await self._save([])
        return count

    async def cleanup_old(self, days: int) -> int:
        if days <= 0:
            return 0
        events = await self._load_all()
        before = len(events)
        events = self._trim_old(events, days)
        removed = before - len(events)
        await self._save(events)
        return removed

    # ── pure helpers ────────────────────────────────────────────

    @staticmethod
    def _trim_old(events: list[dict], days: int) -> list[dict]:
        cutoff = time.time() - days * 86400
        return [e for e in events if e["ts"] >= cutoff]
