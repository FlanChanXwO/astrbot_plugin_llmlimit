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
                "group_limits": [],
                "group_mode_settings": [],
                "time_period_limits": [],
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
                "group_limits": [],
                "group_mode_settings": [],
                "time_period_limits": [],
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
        config["limits"]["time_period_limits"] = (
            "09:00-12:00:3:true\n14:00-18:00:10:true"
        )
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
                "user_limits": [],
                "group_limits": [],
                "group_mode_settings": [],
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
                "priority_users": [],
                "user_limits": [],
                "group_limits": [],
                "group_mode_settings": [],
                "time_period_limits": [],
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
                "exempt_users": [],
                "priority_users": "vip_1\nvip_2",
                "user_limits": [],
                "group_limits": [],
                "group_mode_settings": [],
                "time_period_limits": [],
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
                "user_limits": [],
                "group_limits": [],
                "time_period_limits": [],
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


class TestDataStore:
    """测试独立持久化层 — PluginDataStore 读写与迁移。"""

    @staticmethod
    def _make_scalar_config() -> dict:
        """仅包含标量字段的 config（无 Web UI 管理字段）。"""
        return {
            "limits": {
                "default_daily_limit": 20,
                "default_weekly_limit": 0,
                "default_monthly_limit": 0,
                "daily_reset_time": "00:00",
                "weekly_reset_day": 1,
                "monthly_reset_day": 1,
                "skip_patterns": ["#", "*"],
                "enabled_limit_types": ["daily"],
            }
        }

    def test_load_from_data_store_user_limits(self, data_store):
        data_store.save("user_limits", {"u1": 10, "u2": 20})
        config = self._make_scalar_config()
        mgr = ConfigManager(config, data_store=data_store)
        mgr.load()
        assert mgr.get_user_limit("u1") == 10
        assert mgr.get_user_limit("u2") == 20
        assert mgr.get_user_limit("u3") is None

    def test_load_from_data_store_exempt_users(self, data_store):
        data_store.save("exempt_users", ["admin_1", "superuser"])
        config = self._make_scalar_config()
        mgr = ConfigManager(config, data_store=data_store)
        mgr.load()
        assert mgr.is_exempt("admin_1")
        assert mgr.is_exempt("superuser")
        assert not mgr.is_exempt("normal")

    def test_load_from_data_store_priority_users(self, data_store):
        data_store.save("priority_users", ["vip_1", "vip_2"])
        config = self._make_scalar_config()
        mgr = ConfigManager(config, data_store=data_store)
        mgr.load()
        assert mgr.is_priority("vip_1")
        assert mgr.is_priority("vip_2")

    def test_load_from_data_store_group_limits(self, data_store):
        data_store.save("group_limits", {"g1": 30, "g2": 50})
        config = self._make_scalar_config()
        mgr = ConfigManager(config, data_store=data_store)
        mgr.load()
        assert mgr.get_group_limit("g1") == 30
        assert mgr.get_group_limit("g2") == 50

    def test_load_from_data_store_group_modes(self, data_store):
        data_store.save("group_mode_settings", {"g1": "individual", "g2": "shared"})
        config = self._make_scalar_config()
        mgr = ConfigManager(config, data_store=data_store)
        mgr.load()
        assert mgr.get_group_mode("g1") == "individual"
        assert mgr.get_group_mode("g2") == "shared"

    def test_load_from_data_store_time_periods(self, data_store):
        data_store.save(
            "time_period_limits",
            [
                {
                    "start_time": "09:00",
                    "end_time": "12:00",
                    "limit": 5,
                    "enabled": True,
                },
                {
                    "start_time": "14:00",
                    "end_time": "18:00",
                    "limit": 10,
                    "enabled": True,
                },
            ],
        )
        config = self._make_scalar_config()
        mgr = ConfigManager(config, data_store=data_store)
        mgr.load()
        assert len(mgr.time_period_limits) == 2
        assert mgr.time_period_limits[0]["start_time"] == "09:00"
        assert mgr.time_period_limits[1]["limit"] == 10

    def test_disabled_time_period_skipped(self, data_store):
        data_store.save(
            "time_period_limits",
            [
                {
                    "start_time": "09:00",
                    "end_time": "12:00",
                    "limit": 5,
                    "enabled": False,
                },
                {
                    "start_time": "14:00",
                    "end_time": "18:00",
                    "limit": 10,
                    "enabled": True,
                },
            ],
        )
        config = self._make_scalar_config()
        mgr = ConfigManager(config, data_store=data_store)
        mgr.load()
        assert len(mgr.time_period_limits) == 1
        assert mgr.time_period_limits[0]["limit"] == 10

    def test_empty_data_store(self, data_store):
        """data_store 为空时，容器应为空。"""
        config = self._make_scalar_config()
        mgr = ConfigManager(config, data_store=data_store)
        mgr.load()
        assert len(mgr.user_limits) == 0
        assert len(mgr.exempt_users) == 0
        assert len(mgr.time_period_limits) == 0

    def test_migrate_from_astrobot_config(self, data_store):
        """首次加载时应从 AstrBotConfig 迁移旧数据到 data_store。"""
        config = self._make_scalar_config()
        config["limits"]["user_limits"] = "migrated_u:99"
        config["limits"]["exempt_users"] = "migrated_exempt"
        config["limits"]["time_period_limits"] = "09:00-12:00:7:true"

        mgr = ConfigManager(config, data_store=data_store)
        mgr.load()

        # 数据应加载到内存
        assert mgr.get_user_limit("migrated_u") == 99
        assert mgr.is_exempt("migrated_exempt")
        assert len(mgr.time_period_limits) == 1

        # 再次 load（从 data_store 而非 AstrBotConfig）
        mgr2 = ConfigManager(self._make_scalar_config(), data_store=data_store)
        mgr2.load()
        assert mgr2.get_user_limit("migrated_u") == 99
        assert mgr2.is_exempt("migrated_exempt")
        assert len(mgr2.time_period_limits) == 1

    def test_no_data_store_fallback(self, default_config):
        """不传 data_store 时应从 config dict 读取（向后兼容）。"""
        mgr = ConfigManager(default_config)
        mgr.load()
        assert mgr.default_daily_limit == 20
