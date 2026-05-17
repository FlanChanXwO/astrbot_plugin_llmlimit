"""UsageTracker 单元测试 — 用量追踪 & Key 生成"""

import datetime
from unittest.mock import patch

import pytest
from core.usage_tracker import UsageTracker


@pytest.fixture
def plugin_with_config(default_config, mock_kv, mock_plugin):
    """创建一个带有 config 和 mock KV 的 plugin"""
    mock_plugin.config = default_config
    return mock_plugin


class TestPeriodKeys:
    @patch("core.usage_tracker.datetime")
    def test_daily_period_key_default_reset(self, mock_dt, mock_plugin):
        """默认 reset_time=00:00，2026-05-17 15:00 → key 含 2026-05-17"""
        mock_dt.datetime.now.return_value = datetime.datetime(2026, 5, 17, 15, 0)
        mock_dt.timedelta = datetime.timedelta
        mock_plugin.config = {"limits": {"daily_reset_time": "00:00"}}
        tracker = UsageTracker(mock_plugin)
        key = tracker._build_key("u1", None, "daily", "individual")
        assert "2026-05-17" in key
        assert key.startswith("usage:daily:")

    @patch("core.usage_tracker.datetime")
    def test_daily_period_key_before_reset(self, mock_dt, mock_plugin):
        """reset_time=06:00，当前 2026-05-17 04:00 → 仍属前一天 2026-05-16"""
        mock_dt.datetime.now.return_value = datetime.datetime(2026, 5, 17, 4, 0)
        mock_dt.timedelta = datetime.timedelta
        mock_plugin.config = {"limits": {"daily_reset_time": "06:00"}}
        tracker = UsageTracker(mock_plugin)
        key = tracker._build_key("u1", None, "daily", "individual")
        assert "2026-05-16" in key

    @patch("core.usage_tracker.datetime")
    def test_weekly_period_key(self, mock_dt, mock_plugin):
        """2026-05-17 是一个周日(iso weekday=7)，reset_day=1(周一)，在reset之前"""
        mock_dt.datetime.now.return_value = datetime.datetime(2026, 5, 17, 15, 0)
        mock_dt.timedelta = datetime.timedelta
        mock_plugin.config = {
            "limits": {
                "weekly_reset_day": 1,
                "daily_reset_time": "00:00",
            }
        }
        tracker = UsageTracker(mock_plugin)
        key = tracker._build_key("u1", None, "weekly", "individual")
        # May 17 is Sunday, reset day is Monday → still in this week
        iso = datetime.date(2026, 5, 17).isocalendar()
        assert key.startswith("usage:weekly:")
        assert f"{iso[0]}-W{iso[1]}" in key

    @patch("core.usage_tracker.datetime")
    def test_monthly_period_key(self, mock_dt, mock_plugin):
        mock_dt.datetime.now.return_value = datetime.datetime(2026, 5, 17, 15, 0)
        mock_dt.timedelta = datetime.timedelta
        mock_plugin.config = {
            "limits": {
                "monthly_reset_day": 1,
                "daily_reset_time": "00:00",
            }
        }
        tracker = UsageTracker(mock_plugin)
        key = tracker._build_key("u1", None, "monthly", "individual")
        assert "2026-05" in key
        assert key.startswith("usage:monthly:")


class TestKeyFormat:
    @patch("core.usage_tracker.datetime")
    def test_private_chat_key(self, mock_dt, mock_plugin):
        mock_dt.datetime.now.return_value = datetime.datetime(2026, 5, 17, 15, 0)
        mock_dt.timedelta = datetime.timedelta
        mock_plugin.config = {"limits": {"daily_reset_time": "00:00"}}
        tracker = UsageTracker(mock_plugin)
        key = tracker._build_key("user_123", None, "daily", "individual")
        assert key == "usage:daily:2026-05-17:user:user_123"

    @patch("core.usage_tracker.datetime")
    def test_group_shared_key(self, mock_dt, mock_plugin):
        mock_dt.datetime.now.return_value = datetime.datetime(2026, 5, 17, 15, 0)
        mock_dt.timedelta = datetime.timedelta
        mock_plugin.config = {"limits": {"daily_reset_time": "00:00"}}
        tracker = UsageTracker(mock_plugin)
        key = tracker._build_key("user_123", "group_456", "daily", "shared")
        assert key == "usage:daily:2026-05-17:group:group_456:shared"

    @patch("core.usage_tracker.datetime")
    def test_group_individual_key(self, mock_dt, mock_plugin):
        mock_dt.datetime.now.return_value = datetime.datetime(2026, 5, 17, 15, 0)
        mock_dt.timedelta = datetime.timedelta
        mock_plugin.config = {"limits": {"daily_reset_time": "00:00"}}
        tracker = UsageTracker(mock_plugin)
        key = tracker._build_key("user_123", "group_456", "daily", "individual")
        assert key == "usage:daily:2026-05-17:group:group_456:user:user_123"


class TestIncrementUsage:
    @pytest.mark.asyncio
    @patch("core.usage_tracker.datetime")
    async def test_increment_from_zero(self, mock_dt, mock_kv, plugin_with_config):
        mock_dt.datetime.now.return_value = datetime.datetime(2026, 5, 17, 15, 0)
        mock_dt.timedelta = datetime.timedelta
        tracker = UsageTracker(plugin_with_config)
        new_val = await tracker.increment_usage("u1", None, period_type="daily")
        assert new_val == 1
        assert mock_kv.store.get("usage:daily:2026-05-17:user:u1") == 1

    @pytest.mark.asyncio
    @patch("core.usage_tracker.datetime")
    async def test_get_usage_returns_int(self, mock_dt, mock_kv, plugin_with_config):
        mock_dt.datetime.now.return_value = datetime.datetime(2026, 5, 17, 15, 0)
        mock_dt.timedelta = datetime.timedelta
        mock_kv.set("usage:daily:2026-05-17:user:u1", 5)
        tracker = UsageTracker(plugin_with_config)
        usage = await tracker.get_usage("u1", None, period_type="daily")
        assert usage == 5
        assert isinstance(usage, int)
