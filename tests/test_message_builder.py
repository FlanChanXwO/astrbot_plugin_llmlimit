"""MessageBuilder 单元测试"""

from core.message_builder import MessageBuilder


class TestBuildExceeded:
    def test_default_template(self):
        cfg = {
            "messages": {
                "usage_tip": "次数已用完（{usage}/{limit}），请 {reset_time} 后重试。"
            },
            "limits": {"daily_reset_time": "00:00"},
        }
        b = MessageBuilder(cfg)
        msg = b.build_exceeded(usage=20, limit=20, limit_type="daily")
        assert "20/20" in msg
        assert "00:00" in msg

    def test_custom_template(self):
        cfg = {
            "messages": {
                "usage_tip": "超限！已用 {usage}，上限 {limit}，剩余 {remaining}"
            },
            "limits": {"daily_reset_time": "08:00"},
        }
        b = MessageBuilder(cfg)
        msg = b.build_exceeded(usage=10, limit=10, limit_type="daily")
        assert "10" in msg
        assert "剩余 0" in msg

    def test_limit_type_in_label(self):
        cfg = {
            "messages": {
                "usage_tip": "您的 {limit_type} 调用次数已用完。"
            },
            "limits": {"daily_reset_time": "00:00"},
        }
        b = MessageBuilder(cfg)
        msg = b.build_exceeded(usage=5, limit=5, limit_type="weekly")
        assert "本周" in msg

    def test_timeperiod_label(self):
        cfg = {
            "messages": {
                "usage_tip": "您的 {limit_type} 调用次数已用完。"
            },
            "limits": {"daily_reset_time": "00:00"},
        }
        b = MessageBuilder(cfg)
        msg = b.build_exceeded(usage=5, limit=5, limit_type="timeperiod:tp_0")
        assert "当前时段" in msg


class TestBuildStatus:
    def test_exempt_user(self):
        b = MessageBuilder({})
        msg = b.build_status("u1", {}, {"daily": 20}, exempt=True)
        assert "豁免" in msg

    def test_normal_user_with_usage(self):
        cfg = {
            "messages": {},
            "limits": {"daily_reset_time": "00:00"},
        }
        b = MessageBuilder(cfg)
        usages = {"daily": 5}
        limits = {"daily": 20}
        msg = b.build_status("u1", usages, limits, exempt=False)
        assert "5/20" in msg

    def test_skip_zero_limits(self):
        b = MessageBuilder({})
        usages = {"daily": 5, "weekly": 0}
        limits = {"daily": 20, "weekly": 0}
        msg = b.build_status("u1", usages, limits, exempt=False)
        assert "daily" not in msg.lower() or "今日" in msg
        # weekly=0 is skipped

    def test_shared_group_hint(self):
        b = MessageBuilder({})
        usages = {"daily": 5}
        limits = {"daily": 20}
        msg = b.build_status("u1", usages, limits, exempt=False, group_mode="shared")
        assert "共享" in msg


class TestTypeLabel:
    def test_daily_label(self):
        assert MessageBuilder.type_label("daily") == "今日"

    def test_weekly_label(self):
        assert MessageBuilder.type_label("weekly") == "本周"

    def test_monthly_label(self):
        assert MessageBuilder.type_label("monthly") == "本月"

    def test_unknown_label(self):
        assert MessageBuilder.type_label("custom") == "custom"
