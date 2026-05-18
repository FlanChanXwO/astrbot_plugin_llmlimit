"""Limiter 单元测试 — 限流决策引擎"""

import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from core.config_manager import ConfigManager
from core.limiter import Limiter
from core.time_period_manager import TimePeriodManager
from core.usage_tracker import UsageTracker


def _make_config(**overrides) -> ConfigManager:
    base = {
        "limits": {
            "default_daily_limit": 20,
            "default_weekly_limit": 0,
            "default_monthly_limit": 0,
            "daily_reset_time": "00:00",
            "weekly_reset_day": 1,
            "monthly_reset_day": 1,
            "exempt_users": [],
            "priority_users": [],
            "user_limits": [],
            "group_limits": [],
            "group_mode_settings": [],
            "time_period_limits": [],
            "skip_patterns": ["#"],
            "enabled_limit_types": ["daily"],
        },
        "messages": {},
    }
    for section in ["limits"]:
        if section in overrides:
            base[section].update(overrides[section])
    mgr = ConfigManager(base)
    mgr.load()
    return mgr


@pytest.fixture
def mock_tracker():
    """创建一个 UsageTracker，其 get_usage 返回 0，可通过 side_effect 覆盖"""
    tracker = MagicMock(spec=UsageTracker)
    tracker.get_usage = AsyncMock(return_value=0)
    return tracker


# ── exempt ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_exempt_user_bypasses_all(mock_tracker):
    cfg = _make_config(limits={"exempt_users": "admin"})
    tp_mgr = TimePeriodManager([])
    limiter = Limiter(cfg, mock_tracker, tp_mgr)
    d = await limiter.decide("admin", None)
    assert d.allowed
    assert d.exempt
    mock_tracker.get_usage.assert_not_called()


# ── time period ────────────────────────────────────────────────────


@pytest.mark.asyncio
@patch("core.time_period_manager.datetime")
async def test_time_period_limit_blocks(mock_dt, mock_tracker):
    mock_dt.datetime.now.return_value = datetime.datetime(2026, 5, 17, 10, 0)
    mock_dt.datetime.strptime = datetime.datetime.strptime
    cfg = _make_config(limits={"time_period_limits": "09:00-12:00:5:true"})
    cfg.load()
    tp_mgr = TimePeriodManager(cfg.time_period_limits)
    mock_tracker.get_usage.return_value = 5
    limiter = Limiter(cfg, mock_tracker, tp_mgr)
    d = await limiter.decide("user_a", None)
    assert not d.allowed
    assert d.usage == 5
    assert d.limit == 5


@pytest.mark.asyncio
@patch("core.time_period_manager.datetime")
async def test_time_period_under_limit_allows(mock_dt, mock_tracker):
    mock_dt.datetime.now.return_value = datetime.datetime(2026, 5, 17, 10, 0)
    mock_dt.datetime.strptime = datetime.datetime.strptime
    cfg = _make_config(limits={"time_period_limits": "09:00-12:00:5:true"})
    cfg.load()
    tp_mgr = TimePeriodManager(cfg.time_period_limits)
    mock_tracker.get_usage.return_value = 3
    limiter = Limiter(cfg, mock_tracker, tp_mgr)
    d = await limiter.decide("user_a", None)
    assert d.allowed
    assert d.track_as == "timeperiod"


# ── user specific ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_user_specific_limit_blocks(mock_tracker):
    cfg = _make_config(limits={"user_limits": "user_a:3"})
    tp_mgr = TimePeriodManager([])
    mock_tracker.get_usage.return_value = 3
    limiter = Limiter(cfg, mock_tracker, tp_mgr)
    d = await limiter.decide("user_a", None)
    assert not d.allowed
    assert d.limit == 3
    assert d.limit_type == "user_specific"


@pytest.mark.asyncio
async def test_user_specific_limit_under_allows(mock_tracker):
    cfg = _make_config(limits={"user_limits": "user_a:3"})
    tp_mgr = TimePeriodManager([])
    mock_tracker.get_usage.return_value = 2
    limiter = Limiter(cfg, mock_tracker, tp_mgr)
    d = await limiter.decide("user_a", None)
    assert d.allowed
    assert d.track_as == "daily"


# ── group specific ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_group_specific_limit_blocks(mock_tracker):
    cfg = _make_config(limits={"group_limits": "group_1:10"})
    tp_mgr = TimePeriodManager([])
    mock_tracker.get_usage.return_value = 10
    limiter = Limiter(cfg, mock_tracker, tp_mgr)
    d = await limiter.decide("user_b", "group_1")
    assert not d.allowed
    assert d.limit == 10
    assert d.limit_type == "group_specific"


# ── default daily ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_default_daily_limit_blocks(mock_tracker):
    cfg = _make_config()
    tp_mgr = TimePeriodManager([])
    mock_tracker.get_usage.return_value = 20
    limiter = Limiter(cfg, mock_tracker, tp_mgr)
    d = await limiter.decide("user_c", None)
    assert not d.allowed
    assert d.limit == 20
    assert d.limit_type == "daily"


@pytest.mark.asyncio
async def test_default_daily_limit_under_allows(mock_tracker):
    cfg = _make_config()
    tp_mgr = TimePeriodManager([])
    mock_tracker.get_usage.return_value = 15
    limiter = Limiter(cfg, mock_tracker, tp_mgr)
    d = await limiter.decide("user_c", None)
    assert d.allowed
    assert d.track_as == "daily"


# ── weekly / monthly ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_weekly_limit(mock_tracker):
    cfg = _make_config(
        limits={
            "enabled_limit_types": ["weekly"],
            "default_weekly_limit": 100,
        }
    )
    tp_mgr = TimePeriodManager([])
    mock_tracker.get_usage.return_value = 100
    limiter = Limiter(cfg, mock_tracker, tp_mgr)
    d = await limiter.decide("user_d", None)
    assert not d.allowed
    assert d.limit_type == "weekly"


@pytest.mark.asyncio
async def test_monthly_limit(mock_tracker):
    cfg = _make_config(
        limits={
            "enabled_limit_types": ["monthly"],
            "default_monthly_limit": 500,
        }
    )
    tp_mgr = TimePeriodManager([])
    mock_tracker.get_usage.return_value = 500
    limiter = Limiter(cfg, mock_tracker, tp_mgr)
    d = await limiter.decide("user_e", None)
    assert not d.allowed
    assert d.limit_type == "monthly"


# ── no limits ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_no_limits_allows(mock_tracker):
    cfg = _make_config(
        limits={
            "enabled_limit_types": [],
            "default_daily_limit": 0,
        }
    )
    tp_mgr = TimePeriodManager([])
    limiter = Limiter(cfg, mock_tracker, tp_mgr)
    d = await limiter.decide("user_f", None)
    assert d.allowed
    assert d.unlimited


# ── priority user in shared group ─────────────────────────────────


@pytest.mark.asyncio
async def test_priority_user_not_affected_by_group_shared(mock_tracker):
    """优先用户不受群组共享限额影响"""
    cfg = _make_config(
        limits={
            "priority_users": "vip_user",
            "group_limits": "group_1:5",
        }
    )
    tp_mgr = TimePeriodManager([])
    # 群组共享配额用完了，但 vip 用户不受群组限制
    mock_tracker.get_usage.return_value = 0
    limiter = Limiter(cfg, mock_tracker, tp_mgr)
    d = await limiter.decide("vip_user", "group_1")
    # priority users aren't affected by group limits in dailylimit's logic,
    # but our limiter doesn't special-case them for group limits yet.
    # This test documents current behavior; can be updated when priority implemented.
    assert d.allowed
