import time

from quart import request

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, MessageEventResult, filter
from astrbot.api.platform import MessageType
from astrbot.api.provider import ProviderRequest
from astrbot.api.star import Context, Star, register
from astrbot.core.star.star_tools import StarTools

from .core import (
    CallHistoryTracker,
    ConfigManager,
    Limiter,
    LimiterDecision,
    MessageBuilder,
    TimePeriodManager,
    UsageTracker,
)
from .core.data_store import PluginDataStore


@register(
    "astrbot_plugin_llmlimit", "FlanChanXwO", "精准控制 LLM 调用频率与使用额度", "1.2.0"
)
class LLMLimitPlugin(Star):
    """LLM 调用限流插件"""

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        data_dir = str(StarTools.get_data_dir(plugin_name="astrbot_plugin_llmlimit"))
        self._data_store = PluginDataStore(data_dir)
        logger.info("PluginDataStore 路径: %s", self._data_store._file)

    async def initialize(self):
        """插件初始化"""
        self.config_mgr = ConfigManager(self.config, data_store=self._data_store)
        self.config_mgr.load()
        self.tracker = UsageTracker(self)
        self.time_period_mgr = TimePeriodManager(self.config_mgr.time_period_limits)
        self.limiter = Limiter(self.config_mgr, self.tracker, self.time_period_mgr)
        self.msg_builder = MessageBuilder(self.config)
        self.history = CallHistoryTracker(self)

        # 启动时清理过期历史记录
        retention = self.config_mgr.history_retention_days
        if retention > 0:
            cleaned = await self.history.cleanup_old(retention)
            if cleaned > 0:
                logger.info("启动清理：移除 %s 条过期历史记录", cleaned)

        # 冷却：防止短时间重复发送"次数已用完"
        self._blocked_cooldown: dict[str, float] = {}
        self._cooldown_seconds = 300

        logger.info(
            "LLMLimit 已加载 | 默认日限: %s | 豁免用户: %s | 时段限制: %s | 启用维度: %s",
            self.config_mgr.default_daily_limit,
            len(self.config_mgr.exempt_users),
            len(self.config_mgr.time_period_limits),
            self.config_mgr.enabled_limit_types,
        )

        # ── Web API ────────────────────────────────────────────
        self._init_web_apis()

    def _init_web_apis(self):
        ctx = self.context
        ctx.register_web_api(
            "/astrbot_plugin_llmlimit/user-limits",
            self._api_get_user_limits,
            ["GET"],
            "获取用户限制列表",
        )
        ctx.register_web_api(
            "/astrbot_plugin_llmlimit/user-limits/create",
            self._api_create_user_limit,
            ["POST"],
            "创建用户限制",
        )
        ctx.register_web_api(
            "/astrbot_plugin_llmlimit/user-limits/update",
            self._api_update_user_limit,
            ["POST"],
            "更新用户限制",
        )
        ctx.register_web_api(
            "/astrbot_plugin_llmlimit/user-limits/delete",
            self._api_delete_user_limit,
            ["POST"],
            "删除用户限制",
        )

        # ── Group limits API ──
        ctx.register_web_api(
            "/astrbot_plugin_llmlimit/group-limits",
            self._api_get_group_limits,
            ["GET"],
            "获取群组限制列表",
        )
        ctx.register_web_api(
            "/astrbot_plugin_llmlimit/group-limits/create",
            self._api_create_group_limit,
            ["POST"],
            "创建群组限制",
        )
        ctx.register_web_api(
            "/astrbot_plugin_llmlimit/group-limits/update",
            self._api_update_group_limit,
            ["POST"],
            "更新群组限制",
        )
        ctx.register_web_api(
            "/astrbot_plugin_llmlimit/group-limits/delete",
            self._api_delete_group_limit,
            ["POST"],
            "删除群组限制",
        )

        # ── Time period limits API ──
        ctx.register_web_api(
            "/astrbot_plugin_llmlimit/time-period-limits",
            self._api_get_time_period_limits,
            ["GET"],
            "获取时间段限制列表",
        )
        ctx.register_web_api(
            "/astrbot_plugin_llmlimit/time-period-limits/create",
            self._api_create_time_period,
            ["POST"],
            "创建时间段限制",
        )
        ctx.register_web_api(
            "/astrbot_plugin_llmlimit/time-period-limits/update",
            self._api_update_time_period,
            ["POST"],
            "更新时间段限制",
        )
        ctx.register_web_api(
            "/astrbot_plugin_llmlimit/time-period-limits/delete",
            self._api_delete_time_period,
            ["POST"],
            "删除时间段限制",
        )

        # ── Call history API ──
        ctx.register_web_api(
            "/astrbot_plugin_llmlimit/call-history",
            self._api_get_call_history,
            ["POST"],
            "获取分页调用历史",
        )
        ctx.register_web_api(
            "/astrbot_plugin_llmlimit/call-history/delete",
            self._api_delete_call_history,
            ["POST"],
            "批量删除调用历史",
        )
        ctx.register_web_api(
            "/astrbot_plugin_llmlimit/call-history/cleanup",
            self._api_cleanup_call_history,
            ["POST"],
            "手动清理过期调用历史",
        )

        # ── Exempt users API ──
        ctx.register_web_api(
            "/astrbot_plugin_llmlimit/exempt-users",
            self._api_get_exempt_users,
            ["GET"],
            "获取豁免用户列表",
        )
        ctx.register_web_api(
            "/astrbot_plugin_llmlimit/exempt-users/create",
            self._api_create_exempt_user,
            ["POST"],
            "添加豁免用户",
        )
        ctx.register_web_api(
            "/astrbot_plugin_llmlimit/exempt-users/delete",
            self._api_delete_exempt_user,
            ["POST"],
            "删除豁免用户",
        )

        # ── Priority users API ──
        ctx.register_web_api(
            "/astrbot_plugin_llmlimit/priority-users",
            self._api_get_priority_users,
            ["GET"],
            "获取优先用户列表",
        )
        ctx.register_web_api(
            "/astrbot_plugin_llmlimit/priority-users/create",
            self._api_create_priority_user,
            ["POST"],
            "添加优先用户",
        )
        ctx.register_web_api(
            "/astrbot_plugin_llmlimit/priority-users/delete",
            self._api_delete_priority_user,
            ["POST"],
            "删除优先用户",
        )

        logger.info("LLMLimit Web APIs registered at /astrbot_plugin_llmlimit/*")

    # ── LLM 请求拦截 ────────────────────────────────────────────

    @filter.on_llm_request()
    async def on_llm_request(self, event: AstrMessageEvent, req: ProviderRequest):
        """在 LLM 调用前拦截，执行限流检查"""
        user_id = event.get_sender_id()
        message_str = event.message_str.strip() if event.message_str else ""

        # 跳过以特定前缀开头的非 LLM 指令消息
        for pattern in self.config_mgr.skip_patterns:
            if message_str and message_str.startswith(pattern):
                return True

        group_id: str | None = None
        if event.get_message_type() == MessageType.GROUP_MESSAGE:
            group_id = event.get_group_id()

        decision = await self.limiter.decide(user_id, group_id)

        # 记录调用历史
        await self.history.record(
            user_id=user_id,
            group_id=group_id,
            allowed=decision.allowed,
            limit_type=decision.limit_type,
            usage=decision.usage,
            limit=decision.limit,
            msg_preview=message_str[:50] if message_str else "",
        )

        if not decision.allowed:
            self._send_exceeded_message(event, user_id, decision)
            event.stop_event()
            return False

        # 记录使用
        track_as = decision.track_as or "daily"
        await self.tracker.increment_usage(
            user_id,
            group_id,
            period_type=track_as,
            group_mode=decision.group_mode if group_id else "individual",
        )

        # 剩余量提醒
        remaining = decision.limit - decision.usage - 1  # -1 因为刚 +1
        if remaining in (1, 3, 5):
            self._send_reminder(event, user_id, remaining, decision.limit_type)

        return True

    # ── 用户命令 ─────────────────────────────────────────────────

    @filter.command("limit_status")
    async def cmd_limit_status(self, event: AstrMessageEvent):
        """查看当前 LLM 调用使用状态"""
        user_id = event.get_sender_id()
        group_id: str | None = None
        group_mode = "individual"
        if event.get_message_type() == MessageType.GROUP_MESSAGE:
            group_id = event.get_group_id()
            group_mode = self.config_mgr.get_group_mode(group_id)

        exempt = self.config_mgr.is_exempt(user_id)
        enabled = self.config_mgr.enabled_limit_types
        usages = await self.tracker.get_usages_for_status(
            user_id,
            group_id,
            group_mode,
            enabled,
        )
        limits: dict[str, int] = {}
        for pt in enabled:
            if pt == "timeperiod":
                tp_limit = self.time_period_mgr.get_current_limit()
                if tp_limit is not None:
                    limits[pt] = tp_limit
            elif pt == "daily":
                limits[pt] = self._effective_limit(user_id, group_id)
            elif pt == "weekly":
                limits[pt] = self.config_mgr.default_weekly_limit
            elif pt == "monthly":
                limits[pt] = self.config_mgr.default_monthly_limit

        msg = self.msg_builder.build_status(user_id, usages, limits, exempt, group_mode)
        yield event.plain_result(msg)

    # ── 管理命令 ─────────────────────────────────────────────────

    @filter.command_group("limit_admin")
    def cmd_limit_admin(self):
        """管理命令入口 (需要 ADMIN 权限) — 使用子命令管理限制"""
        pass

    def _check_admin(self, event: AstrMessageEvent) -> bool:
        if not event.is_admin():
            event.set_result(MessageEventResult().message("您没有权限执行管理命令。"))
            return False
        return True

    @cmd_limit_admin.command("set_user")
    async def admin_set_user(self, event: AstrMessageEvent, target_id: str, limit: int):
        """设置用户特定限制: /limit_admin set_user <用户ID> <次数>"""
        if not self._check_admin(event):
            return
        self.config_mgr.user_limits[target_id] = limit
        self._save_user_limits()
        yield event.plain_result(f"用户 {target_id} 的调用限制已设为 {limit} 次/日。")

    @cmd_limit_admin.command("set_group")
    async def admin_set_group(
        self, event: AstrMessageEvent, target_id: str, limit: int
    ):
        """设置群组特定限制: /limit_admin set_group <群ID> <次数>"""
        if not self._check_admin(event):
            return
        self.config_mgr.group_limits[target_id] = limit
        self._save_group_limits()
        yield event.plain_result(f"群组 {target_id} 的调用限制已设为 {limit} 次/日。")

    @cmd_limit_admin.command("set_mode")
    async def admin_set_mode(self, event: AstrMessageEvent, target_id: str, mode: str):
        """设置群组配额模式: /limit_admin set_mode <群ID> <shared|individual>"""
        if not self._check_admin(event):
            return
        if mode not in ("shared", "individual"):
            yield event.plain_result("模式只能是 shared 或 individual。")
            return
        self.config_mgr.group_modes[target_id] = mode
        self._save_group_modes()
        label = "共享配额" if mode == "shared" else "独立配额"
        yield event.plain_result(f"群组 {target_id} 已设为 {label} 模式。")

    @cmd_limit_admin.command("remove_user")
    async def admin_remove_user(self, event: AstrMessageEvent, target_id: str):
        """移除用户特定限制"""
        if not self._check_admin(event):
            return
        if target_id in self.config_mgr.user_limits:
            del self.config_mgr.user_limits[target_id]
            self._save_user_limits()
            yield event.plain_result(f"已移除用户 {target_id} 的特定限制。")
        else:
            yield event.plain_result(f"用户 {target_id} 没有设置特定限制。")

    @cmd_limit_admin.command("remove_group")
    async def admin_remove_group(self, event: AstrMessageEvent, target_id: str):
        """移除群组特定限制"""
        if not self._check_admin(event):
            return
        if target_id in self.config_mgr.group_limits:
            del self.config_mgr.group_limits[target_id]
            self._save_group_limits()
            yield event.plain_result(f"已移除群组 {target_id} 的特定限制。")
        else:
            yield event.plain_result(f"群组 {target_id} 没有设置特定限制。")

    @cmd_limit_admin.command("list")
    async def admin_list(self, event: AstrMessageEvent):
        """列出当前自定义限制"""
        if not self._check_admin(event):
            return
        lines = ["**自定义限制列表**"]
        if self.config_mgr.user_limits:
            lines.append("\n用户限制:")
            for uid, lim in self.config_mgr.user_limits.items():
                lines.append(f"  • {uid}: {lim} 次/日")
        if self.config_mgr.group_limits:
            lines.append("\n群组限制:")
            for gid, lim in self.config_mgr.group_limits.items():
                lines.append(f"  • {gid}: {lim} 次/日")
        if self.config_mgr.group_modes:
            lines.append("\n群组模式:")
            for gid, mode in self.config_mgr.group_modes.items():
                lines.append(f"  • {gid}: {mode}")
        if self.config_mgr.time_period_limits:
            lines.append("\n时间段限制:")
            for tp in self.config_mgr.time_period_limits:
                lines.append(
                    f"  • {tp['start_time']}-{tp['end_time']}: {tp['limit']} 次"
                )
        if len(lines) == 1:
            lines.append("暂无自定义限制。")
        yield event.plain_result("\n".join(lines))

    # ── 配置持久化 ───────────────────────────────────────────────

    def _save_user_limits(self):
        self._data_store.save("user_limits", self.config_mgr.user_limits)

    def _save_group_limits(self):
        self._data_store.save("group_limits", self.config_mgr.group_limits)

    def _save_group_modes(self):
        self._data_store.save("group_mode_settings", self.config_mgr.group_modes)

    def _save_exempt_users(self):
        self._data_store.save("exempt_users", sorted(self.config_mgr.exempt_users))

    def _save_priority_users(self):
        self._data_store.save("priority_users", sorted(self.config_mgr.priority_users))

    # ── 内部辅助 ─────────────────────────────────────────────────

    async def _api_get_call_history(self):
        """返回分页调用历史。"""
        body = await request.get_json()
        page = int(body.get("page", 1)) if body else 1
        page_size = int(body.get("pageSize", 50)) if body else 50
        return await self.history.get_paginated(page, page_size)

    def _reload_config_mgr(self):
        """重新加载 ConfigManager 以同步配置。"""
        self.config_mgr = ConfigManager(self.config, data_store=self._data_store)
        self.config_mgr.load()
        self.tracker = UsageTracker(self)
        self.time_period_mgr = TimePeriodManager(self.config_mgr.time_period_limits)
        self.limiter = Limiter(self.config_mgr, self.tracker, self.time_period_mgr)
        self.history = CallHistoryTracker(self)

    # ── Web API handlers ───────────────────────────────────────────

    # -- User limits --

    async def _api_get_user_limits(self) -> list:
        items = []
        for uid, lim in self.config_mgr.user_limits.items():
            items.append({"userId": str(uid), "limit": lim})
        return items

    async def _api_create_user_limit(self) -> dict:
        body = await request.get_json()
        uid = body.get("userId", "").strip()
        lim = body.get("limit", 0)
        if not uid or lim <= 0:
            return {"success": False, "error": "无效参数"}
        self.config_mgr.user_limits[uid] = lim
        self._save_user_limits()
        self._reload_config_mgr()
        return {"success": True}

    async def _api_update_user_limit(self) -> dict:
        body = await request.get_json()
        idx = body.get("index", -1)
        uid = body.get("userId", "").strip()
        lim = body.get("limit", 0)
        items = list(self.config_mgr.user_limits.items())
        if idx < 0 or idx >= len(items):
            return {"success": False, "error": "索引越界"}
        old_uid, _ = items[idx]
        if uid and uid != old_uid:
            del self.config_mgr.user_limits[old_uid]
        if uid and lim > 0:
            self.config_mgr.user_limits[uid] = lim
        self._save_user_limits()
        self._reload_config_mgr()
        return {"success": True}

    async def _api_delete_user_limit(self) -> dict:
        body = await request.get_json()
        idx = body.get("index", -1)
        items = list(self.config_mgr.user_limits.items())
        if idx < 0 or idx >= len(items):
            return {"success": False, "error": "索引越界"}
        uid, _ = items[idx]
        del self.config_mgr.user_limits[uid]
        self._save_user_limits()
        self._reload_config_mgr()
        return {"success": True}

    # -- Group limits --

    async def _api_get_group_limits(self) -> list:
        items = []
        for gid, lim in self.config_mgr.group_limits.items():
            items.append({"groupId": str(gid), "limit": lim})
        return items

    async def _api_create_group_limit(self) -> dict:
        body = await request.get_json()
        gid = body.get("groupId", "").strip()
        lim = body.get("limit", 0)
        if not gid or lim <= 0:
            return {"success": False, "error": "无效参数"}
        self.config_mgr.group_limits[gid] = lim
        self._save_group_limits()
        self._reload_config_mgr()
        return {"success": True}

    async def _api_update_group_limit(self) -> dict:
        body = await request.get_json()
        idx = body.get("index", -1)
        gid = body.get("groupId", "").strip()
        lim = body.get("limit", 0)
        items = list(self.config_mgr.group_limits.items())
        if idx < 0 or idx >= len(items):
            return {"success": False, "error": "索引越界"}
        old_gid, _ = items[idx]
        if gid and gid != old_gid:
            del self.config_mgr.group_limits[old_gid]
        if gid and lim > 0:
            self.config_mgr.group_limits[gid] = lim
        self._save_group_limits()
        self._reload_config_mgr()
        return {"success": True}

    async def _api_delete_group_limit(self) -> dict:
        body = await request.get_json()
        idx = body.get("index", -1)
        items = list(self.config_mgr.group_limits.items())
        if idx < 0 or idx >= len(items):
            return {"success": False, "error": "索引越界"}
        gid, _ = items[idx]
        del self.config_mgr.group_limits[gid]
        self._save_group_limits()
        self._reload_config_mgr()
        return {"success": True}

    # -- Time period limits --

    async def _api_get_time_period_limits(self) -> list:
        return [
            {
                "startTime": p["start_time"],
                "endTime": p["end_time"],
                "limit": p["limit"],
                "enabled": p.get("enabled", True),
            }
            for p in self.config_mgr.time_period_limits
        ]

    async def _api_create_time_period(self) -> dict:
        body = await request.get_json()
        start = body.get("startTime", "")
        end = body.get("endTime", "")
        lim = body.get("limit", 0)
        enabled = body.get("enabled", True)
        if not start or not end or lim <= 0:
            return {"success": False, "error": "无效参数"}
        self.config_mgr.time_period_limits.append(
            {"start_time": start, "end_time": end, "limit": lim, "enabled": enabled}
        )
        self._save_time_period_limits()
        self._reload_config_mgr()
        return {"success": True}

    async def _api_update_time_period(self) -> dict:
        body = await request.get_json()
        idx = body.get("index", -1)
        start = body.get("startTime", "")
        end = body.get("endTime", "")
        lim = body.get("limit", 0)
        enabled = body.get("enabled", True)
        if idx < 0 or idx >= len(self.config_mgr.time_period_limits):
            return {"success": False, "error": "索引越界"}
        self.config_mgr.time_period_limits[idx] = {
            "start_time": start,
            "end_time": end,
            "limit": lim,
            "enabled": enabled,
        }
        self._save_time_period_limits()
        self._reload_config_mgr()
        return {"success": True}

    async def _api_delete_time_period(self) -> dict:
        body = await request.get_json()
        idx = body.get("index", -1)
        if idx < 0 or idx >= len(self.config_mgr.time_period_limits):
            return {"success": False, "error": "索引越界"}
        self.config_mgr.time_period_limits.pop(idx)
        self._save_time_period_limits()
        self._reload_config_mgr()
        return {"success": True}

    def _save_time_period_limits(self):
        self._data_store.save("time_period_limits", self.config_mgr.time_period_limits)

    # -- Exempt users --

    async def _api_get_exempt_users(self) -> list:
        return sorted(self.config_mgr.exempt_users)

    async def _api_create_exempt_user(self) -> dict:
        body = await request.get_json()
        uid = body.get("userId", "").strip()
        if not uid:
            return {"success": False, "error": "用户ID不能为空"}
        self.config_mgr.exempt_users.add(uid)
        self._save_exempt_users()
        self._reload_config_mgr()
        return {"success": True}

    async def _api_delete_exempt_user(self) -> dict:
        body = await request.get_json()
        uid = body.get("userId", "").strip()
        if not uid:
            return {"success": False, "error": "用户ID不能为空"}
        if uid in self.config_mgr.exempt_users:
            self.config_mgr.exempt_users.discard(uid)
            self._save_exempt_users()
            self._reload_config_mgr()
            return {"success": True}
        return {"success": False, "error": "未找到该用户"}

    # -- Priority users --

    async def _api_get_priority_users(self) -> list:
        return sorted(self.config_mgr.priority_users)

    async def _api_create_priority_user(self) -> dict:
        body = await request.get_json()
        uid = body.get("userId", "").strip()
        if not uid:
            return {"success": False, "error": "用户ID不能为空"}
        self.config_mgr.priority_users.add(uid)
        self._save_priority_users()
        self._reload_config_mgr()
        return {"success": True}

    async def _api_delete_priority_user(self) -> dict:
        body = await request.get_json()
        uid = body.get("userId", "").strip()
        if not uid:
            return {"success": False, "error": "用户ID不能为空"}
        if uid in self.config_mgr.priority_users:
            self.config_mgr.priority_users.discard(uid)
            self._save_priority_users()
            self._reload_config_mgr()
            return {"success": True}
        return {"success": False, "error": "未找到该用户"}

    # ── Call history management ──

    async def _api_delete_call_history(self) -> dict:
        body = await request.get_json()
        ts_list = body.get("ts_list")
        if ts_list:
            removed = await self.history.delete_by_timestamps(ts_list)
            return {"success": True, "removed": removed}
        if body.get("delete_all"):
            removed = await self.history.delete_all()
            return {"success": True, "removed": removed}
        return {"success": False, "error": "请提供 ts_list 或 delete_all"}

    async def _api_cleanup_call_history(self) -> dict:
        body = await request.get_json()
        days = int(body.get("days", self.config_mgr.history_retention_days))
        removed = await self.history.cleanup_old(days)
        return {"success": True, "removed": removed}

    def _effective_limit(self, user_id: str, group_id: str | None) -> int:
        """计算用户生效的限制值（用于状态展示）"""
        tp = self.time_period_mgr.get_current_limit()
        if tp is not None:
            return tp
        user_lim = self.config_mgr.get_user_limit(user_id)
        if user_lim is not None:
            return user_lim
        if group_id:
            group_lim = self.config_mgr.get_group_limit(group_id)
            if group_lim is not None:
                return group_lim
        return self.config_mgr.default_daily_limit

    def _send_exceeded_message(
        self, event: AstrMessageEvent, user_id: str, decision: LimiterDecision
    ):
        """发送'已达上限'消息（带冷却）"""
        now = time.time()
        last = self._blocked_cooldown.get(user_id, 0)
        if now - last < self._cooldown_seconds:
            return
        self._blocked_cooldown[user_id] = now

        msg = self.msg_builder.build_exceeded(
            decision.usage,
            decision.limit,
            decision.limit_type,
        )
        event.set_result(MessageEventResult().message(msg))

    def _send_reminder(
        self, event: AstrMessageEvent, user_id: str, remaining: int, limit_type: str
    ):
        label = MessageBuilder.type_label(limit_type)
        event.set_result(
            MessageEventResult().message(f"[{label}] 剩余 LLM 调用次数: {remaining}")
        )

    async def terminate(self):
        """插件销毁"""
        logger.info("LLMLimit 已卸载")
