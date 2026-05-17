"""ConfigManager 单元测试"""

from core.config_manager import ConfigManager


class TestConfigDefaults:
    def test_default_daily_limit(self, default_config):
        mgr = ConfigManager(default_config)
        mgr.load()
        assert mgr.default_daily_limit == 20

    def test_default_weekly_limit_zero(self, default_config):
        mgr = ConfigManager(default_config)
        mgr.load()
        assert mgr.default_weekly_limit == 0

    def test_enabled_limit_types(self, default_config):
        mgr = ConfigManager(default_config)
        mgr.load()
        assert mgr.enabled_limit_types == ["daily"]

    def test_is_exempt_empty(self, default_config):
        mgr = ConfigManager(default_config)
        mgr.load()
        assert not mgr.is_exempt("anyone")

    def test_get_group_mode_default(self, default_config):
        mgr = ConfigManager(default_config)
        mgr.load()
        assert mgr.get_group_mode("unknown_group") == "shared"


class TestParseUserLimits:
    def test_parse_string_format(self):
        config = {
            "limits": {
                "default_daily_limit": 20,
                "user_limits": "user_a:5\nuser_b:10",
                "exempt_users": [],
                "priority_users": [],
                "group_limits": "",
                "group_mode_settings": "",
                "time_period_limits": "",
                "skip_patterns": ["#"],
                "enabled_limit_types": ["daily"],
                "daily_reset_time": "00:00",
            }
        }
        mgr = ConfigManager(config)
        mgr.load()
        assert mgr.get_user_limit("user_a") == 5
        assert mgr.get_user_limit("user_b") == 10
        assert mgr.get_user_limit("user_c") is None

    def test_parse_list_format(self):
        config = {
            "limits": {
                "default_daily_limit": 20,
                "user_limits": ["user_a:5", "user_b:10"],
                "exempt_users": [],
                "priority_users": [],
                "group_limits": "",
                "group_mode_settings": "",
                "time_period_limits": "",
                "skip_patterns": ["#"],
                "enabled_limit_types": ["daily"],
                "daily_reset_time": "00:00",
            }
        }
        mgr = ConfigManager(config)
        mgr.load()
        assert mgr.user_limits == {"user_a": 5, "user_b": 10}


class TestParseTimePeriodLimits:
    def test_parse_basic(self):
        config = self._make_config("09:00-12:00:5:true")
        mgr = ConfigManager(config)
        mgr.load()
        assert len(mgr.time_period_limits) == 1
        tp = mgr.time_period_limits[0]
        assert tp["start_time"] == "09:00"
        assert tp["end_time"] == "12:00"
        assert tp["limit"] == 5

    def test_parse_disabled_period(self):
        config = self._make_config("09:00-12:00:5:false")
        mgr = ConfigManager(config)
        mgr.load()
        assert len(mgr.time_period_limits) == 0

    def test_parse_multiple(self):
        config = self._make_config("09:00-12:00:3\ntrue\n14:00-18:00:10:true")
        # 注意：格式是 HH:MM-HH:MM:次数[:enabled]
        # 第二行的 "true" 会被跳过（不在正确格式内），第三行正确解析
        config["limits"]["time_period_limits"] = "09:00-12:00:3:true\n14:00-18:00:10:true"
        mgr = ConfigManager(config)
        mgr.load()
        assert len(mgr.time_period_limits) == 2

    def test_parse_invalid_time_skipped(self):
        config = self._make_config("25:00-12:00:5:true")
        mgr = ConfigManager(config)
        mgr.load()
        assert len(mgr.time_period_limits) == 0

    @staticmethod
    def _make_config(time_period_str: str) -> dict:
        return {
            "limits": {
                "default_daily_limit": 20,
                "time_period_limits": time_period_str,
                "exempt_users": [],
                "priority_users": [],
                "user_limits": "",
                "group_limits": "",
                "group_mode_settings": "",
                "skip_patterns": ["#"],
                "enabled_limit_types": ["daily"],
                "daily_reset_time": "00:00",
            }
        }


class TestParseExemptAndPriority:
    def test_parse_exempt_users(self):
        config = {
            "limits": {
                "default_daily_limit": 20,
                "exempt_users": "admin_1\nsuperuser",
                "priority_users": "",
                "user_limits": "",
                "group_limits": "",
                "group_mode_settings": "",
                "time_period_limits": "",
                "skip_patterns": [],
                "enabled_limit_types": ["daily"],
                "daily_reset_time": "00:00",
            }
        }
        mgr = ConfigManager(config)
        mgr.load()
        assert mgr.is_exempt("admin_1")
        assert mgr.is_exempt("superuser")
        assert not mgr.is_exempt("normal_user")

    def test_parse_priority_users(self):
        config = {
            "limits": {
                "default_daily_limit": 20,
                "exempt_users": "",
                "priority_users": "vip_1\nvip_2",
                "user_limits": "",
                "group_limits": "",
                "group_mode_settings": "",
                "time_period_limits": "",
                "skip_patterns": [],
                "enabled_limit_types": ["daily"],
                "daily_reset_time": "00:00",
            }
        }
        mgr = ConfigManager(config)
        mgr.load()
        assert mgr.is_priority("vip_1")
        assert mgr.is_priority("vip_2")
        assert not mgr.is_priority("normal_user")


class TestGroupMode:
    def test_get_group_mode(self):
        config = {
            "limits": {
                "default_daily_limit": 20,
                "group_mode_settings": "group_1:individual\ngroup_2:shared",
                "exempt_users": [],
                "priority_users": [],
                "user_limits": "",
                "group_limits": "",
                "time_period_limits": "",
                "skip_patterns": [],
                "enabled_limit_types": ["daily"],
                "daily_reset_time": "00:00",
            }
        }
        mgr = ConfigManager(config)
        mgr.load()
        assert mgr.get_group_mode("group_1") == "individual"
        assert mgr.get_group_mode("group_2") == "shared"
        assert mgr.get_group_mode("unknown") == "shared"  # default


class TestValidateResetTime:
    def test_invalid_reset_time_falls_back_to_default(self, default_config):
        default_config["limits"]["daily_reset_time"] = "25:00"
        mgr = ConfigManager(default_config)
        mgr.load()
        assert mgr.get_reset_time() == "00:00"

    def test_valid_reset_time_preserved(self, default_config):
        default_config["limits"]["daily_reset_time"] = "06:30"
        mgr = ConfigManager(default_config)
        mgr.load()
        assert mgr.get_reset_time() == "06:30"
