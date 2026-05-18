"""
测试 CallHistoryTracker — 调用历史记录与查询。
"""

import time

import pytest

from core.call_history import CallHistoryTracker


@pytest.fixture
def tracker(mock_kv):
    """返回一个使用内存 KV Mock 的 CallHistoryTracker。"""
    return CallHistoryTracker(mock_kv.plugin)


async def _record(t: CallHistoryTracker, **kwargs):
    defaults = {
        "user_id": "user_1",
        "group_id": None,
        "allowed": True,
        "limit_type": "daily",
        "usage": 3,
        "limit": 20,
        "msg_preview": "hello",
    }
    defaults.update(kwargs)
    await t.record(**defaults)


class TestRecordSingle:
    @pytest.mark.asyncio
    async def test_record_single_event(self, tracker):
        await _record(tracker)
        events = await tracker.get_recent()
        assert len(events) == 1
        assert events[0]["user_id"] == "user_1"
        assert events[0]["allowed"] is True
        assert events[0]["limit_type"] == "daily"

    @pytest.mark.asyncio
    async def test_record_allowed_false(self, tracker):
        await _record(tracker, allowed=False, limit_type="daily")
        events = await tracker.get_recent()
        assert events[0]["allowed"] is False

    @pytest.mark.asyncio
    async def test_record_with_group_id(self, tracker):
        await _record(tracker, group_id="group_99")
        events = await tracker.get_recent()
        assert events[0]["group_id"] == "group_99"

    @pytest.mark.asyncio
    async def test_record_group_id_none_becomes_empty(self, tracker):
        await _record(tracker, group_id=None)
        events = await tracker.get_recent()
        assert events[0]["group_id"] == ""

    @pytest.mark.asyncio
    async def test_record_preserves_usage_and_limit(self, tracker):
        await _record(tracker, usage=5, limit=10)
        events = await tracker.get_recent()
        assert events[0]["usage"] == 5
        assert events[0]["limit"] == 10

    @pytest.mark.asyncio
    async def test_record_stores_timestamp(self, tracker):
        before = time.time()
        await _record(tracker)
        after = time.time()
        ts = (await tracker.get_recent())[0]["ts"]
        assert before <= ts <= after

    @pytest.mark.asyncio
    async def test_record_msg_preview(self, tracker):
        await _record(tracker, msg_preview="这是一条测试消息" * 5)
        events = await tracker.get_recent()
        assert len(events[0]["msg_preview"]) > 0


class TestGetRecent:
    @pytest.mark.asyncio
    async def test_empty_returns_empty_list(self, tracker):
        events = await tracker.get_recent()
        assert events == []

    @pytest.mark.asyncio
    async def test_events_in_reverse_chronological_order(self, tracker):
        await _record(tracker, user_id="user_A")
        await _record(tracker, user_id="user_B")
        events = await tracker.get_recent()
        assert events[0]["user_id"] == "user_B"
        assert events[1]["user_id"] == "user_A"

    @pytest.mark.asyncio
    async def test_get_recent_limits_n(self, tracker):
        for i in range(10):
            await _record(tracker, user_id=f"user_{i}")
        events = await tracker.get_recent(n=3)
        assert len(events) == 3
        # 最新的在前面
        assert events[0]["user_id"] == "user_9"
        assert events[2]["user_id"] == "user_7"


class TestTrim:
    @pytest.mark.asyncio
    async def test_record_trims_to_max(self, tracker):
        # 临时减小 max 以避免创建 200+ 条记录
        tracker._plugin.config_mgr.max_history_events = 5
        for i in range(10):
            await _record(tracker, user_id=f"user_{i}")
        events = await tracker.get_recent()
        assert len(events) == 5
        # 保留最新的 5 条
        assert events[0]["user_id"] == "user_9"
        assert events[4]["user_id"] == "user_5"

    @pytest.mark.asyncio
    async def test_exact_max(self, tracker):
        tracker._plugin.config_mgr.max_history_events = 3
        await _record(tracker, user_id="a")
        await _record(tracker, user_id="b")
        await _record(tracker, user_id="c")
        events = await tracker.get_recent()
        assert len(events) == 3


class TestCorruptData:
    @pytest.mark.asyncio
    async def test_non_json_data_returns_empty(self, mock_plugin):
        """KV 中存储的不是有效的 JSON 时 get_recent 返回 []。"""
        mock_plugin.get_kv_data.return_value = "not-valid-json"
        t = CallHistoryTracker(mock_plugin)
        events = await t.get_recent()
        assert events == []

    @pytest.mark.asyncio
    async def test_non_string_data_handled(self, mock_plugin):
        """KV 中存储的是非字符串类型时返回 []。"""
        mock_plugin.get_kv_data.return_value = 12345
        t = CallHistoryTracker(mock_plugin)
        events = await t.get_recent()
        assert events == []

    @pytest.mark.asyncio
    async def test_record_handles_corrupt_existing(self, mock_kv):
        """record() 在已有数据损坏时视为空列表并正常写入。"""
        # 在 KV 中预置损坏的数据（KVMock 按 key 保存）
        mock_kv.set("history:recent", "garbage{{{")
        t = CallHistoryTracker(mock_kv.plugin)
        await _record(t, user_id="recovered")
        # get_recent 应该忽略损坏数据，仅返回新事件
        events = await t.get_recent()
        assert len(events) == 1
        assert events[0]["user_id"] == "recovered"
