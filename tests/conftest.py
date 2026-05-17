"""
测试配置和共享 fixtures。

Mock AstrBot 框架组件（Star, Context, KV store），
使单元测试不依赖完整 AstrBot 运行时。
"""

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_plugin():
    """模拟插件实例，提供 put_kv_data / get_kv_data 等 KV 存储方法。"""
    plugin = MagicMock()
    plugin.put_kv_data = AsyncMock()
    plugin.get_kv_data = AsyncMock(return_value=0)
    return plugin


@pytest.fixture
def default_config():
    """提供默认插件配置字典（模拟 AstrBotConfig）。"""
    return {
        "limits": {
            "default_daily_limit": 20,
            "default_weekly_limit": 0,
            "default_monthly_limit": 0,
            "daily_reset_time": "00:00",
            "weekly_reset_day": 1,
            "monthly_reset_day": 1,
            "exempt_users": [],
            "priority_users": [],
            "user_limits": "",
            "group_limits": "",
            "group_mode_settings": "",
            "time_period_limits": "",
            "skip_patterns": ["#", "*"],
            "enabled_limit_types": ["daily"],
        },
        "messages": {
            "show_remaining_count": True,
            "usage_tip": "您的 LLM 调用次数已用完（{usage}/{limit}）。请在 {reset_time} 后重试。",
        },
    }


@pytest.fixture
def mock_kv(mock_plugin):
    """返回可重置的 KV Mock 工具，支持预设/验证存储值。

    方法:
    - set(key, val): 预置 get 返回值
    - get_calls(): 返回所有 put 调用的 (key, value) 列表
    """

    class KVMock:
        def __init__(self, plugin):
            self.plugin = plugin
            self._store: dict[str, int] = {}

        def set(self, key: str, value: int):
            self._store[key] = value

        async def _get_impl(self, key, default):
            return self._store.get(key, default)

        async def _put_impl(self, key, value):
            self._store[key] = value

        def install(self):
            self.plugin.get_kv_data.side_effect = self._get_impl
            self.plugin.put_kv_data.side_effect = self._put_impl
            return self

        @property
        def store(self):
            return dict(self._store)

    return KVMock(mock_plugin).install()


@pytest.fixture
def mock_event():
    """模拟 AstrMessageEvent。"""
    event = MagicMock()
    event.get_sender_id = MagicMock(return_value="user_123")
    event.get_sender_name = MagicMock(return_value="TestUser")
    event.get_group_id = MagicMock(return_value="group_456")
    event.get_message_type = MagicMock(return_value="group_message")
    event.message_str = "hello"
    event.is_admin = MagicMock(return_value=True)
    event.plain_result = MagicMock(return_value="ok")
    event.set_result = MagicMock()
    event.stop_event = MagicMock()
    return event
