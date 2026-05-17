"""TimePeriodManager 单元测试"""

import datetime
from unittest.mock import patch

from core.time_period_manager import TimePeriodManager


def _time(h, m):
    return datetime.time(h, m)


class TestNoPeriods:
    def test_no_periods_returns_none(self):
        mgr = TimePeriodManager([])
        assert mgr.get_current_limit() is None

    def test_no_periods_index_returns_none(self):
        mgr = TimePeriodManager([])
        assert mgr.get_active_period_index() is None


class TestInPeriod:
    @patch("core.time_period_manager.datetime")
    def test_inside_period(self, mock_dt):
        mock_dt.datetime.now.return_value = datetime.datetime(2026, 5, 17, 10, 30)
        mock_dt.datetime.strptime = datetime.datetime.strptime
        periods = [{"start_time": "09:00", "end_time": "12:00", "limit": 5}]
        mgr = TimePeriodManager(periods)
        assert mgr.get_current_limit() == 5
        assert mgr.get_active_period_index() == 0

    @patch("core.time_period_manager.datetime")
    def test_outside_period(self, mock_dt):
        mock_dt.datetime.now.return_value = datetime.datetime(2026, 5, 17, 14, 0)
        mock_dt.datetime.strptime = datetime.datetime.strptime
        periods = [{"start_time": "09:00", "end_time": "12:00", "limit": 5}]
        mgr = TimePeriodManager(periods)
        assert mgr.get_current_limit() is None

    @patch("core.time_period_manager.datetime")
    def test_cross_midnight_inside(self, mock_dt):
        """跨天时间段 22:00-06:00，当前 02:00"""
        mock_dt.datetime.now.return_value = datetime.datetime(2026, 5, 17, 2, 0)
        mock_dt.datetime.strptime = datetime.datetime.strptime
        periods = [{"start_time": "22:00", "end_time": "06:00", "limit": 3}]
        mgr = TimePeriodManager(periods)
        assert mgr.get_current_limit() == 3

    @patch("core.time_period_manager.datetime")
    def test_cross_midnight_inside_evening(self, mock_dt):
        """跨天时间段 22:00-06:00，当前 23:30"""
        mock_dt.datetime.now.return_value = datetime.datetime(2026, 5, 17, 23, 30)
        mock_dt.datetime.strptime = datetime.datetime.strptime
        periods = [{"start_time": "22:00", "end_time": "06:00", "limit": 3}]
        mgr = TimePeriodManager(periods)
        assert mgr.get_current_limit() == 3

    @patch("core.time_period_manager.datetime")
    def test_cross_midnight_outside(self, mock_dt):
        """跨天时间段 22:00-06:00，当前 12:00 — 不在时段内"""
        mock_dt.datetime.now.return_value = datetime.datetime(2026, 5, 17, 12, 0)
        mock_dt.datetime.strptime = datetime.datetime.strptime
        periods = [{"start_time": "22:00", "end_time": "06:00", "limit": 3}]
        mgr = TimePeriodManager(periods)
        assert mgr.get_current_limit() is None

    @patch("core.time_period_manager.datetime")
    def test_multiple_periods_picks_first(self, mock_dt):
        """多个时段重叠时返回第一个匹配的"""
        mock_dt.datetime.now.return_value = datetime.datetime(2026, 5, 17, 10, 30)
        mock_dt.datetime.strptime = datetime.datetime.strptime
        periods = [
            {"start_time": "09:00", "end_time": "12:00", "limit": 5},
            {"start_time": "10:00", "end_time": "14:00", "limit": 8},
        ]
        mgr = TimePeriodManager(periods)
        assert mgr.get_current_limit() == 5  # 第一个匹配
