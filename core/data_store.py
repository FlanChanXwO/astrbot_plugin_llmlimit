from __future__ import annotations

"""
独立持久化存储模块

提供独立于 AstrBotConfig 的 JSON 文件持久化，
防止 AstrBot 配置完整性检查清除 Web UI 管理的数据。
"""

import json
import os
import tempfile


class PluginDataStore:
    """独立于 AstrBotConfig 的持久化存储。

    数据目录由调用方通过 StarTools.get_data_dir() 获取，
    文件名为 plugin_data.json，不受 AstrBot check_config_integrity() 影响。
    """

    def __init__(self, data_dir: str):
        self._file = os.path.join(data_dir, "plugin_data.json")

    # ── public API ──────────────────────────────────────────────

    def load(self) -> dict:
        """读取全部数据，文件不存在时返回空 dict。"""
        if not os.path.exists(self._file):
            return {}
        try:
            with open(self._file, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return {}

    def save(self, section: str, data):
        """保存单个 section——原子写入。

        读出现有全部数据，更新指定 section，
        先写临时文件再 os.replace 确保写入不中断。
        """
        # 确保目录存在
        os.makedirs(os.path.dirname(self._file), exist_ok=True)

        all_data = self.load()
        all_data[section] = data

        fd, tmp_path = tempfile.mkstemp(
            dir=os.path.dirname(self._file),
            suffix=".tmp",
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(all_data, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, self._file)
        except Exception:
            # 写入失败时清理临时文件
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise
