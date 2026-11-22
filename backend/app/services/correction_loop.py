"""纠错回路回填领域服务：登记转写文本纠错并合入版本触发下游重算，产出纠错单数据集供字幕包重算与版本联动消费。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class CorrectionLoopService(BaseModuleService):
    MODULE = "correction_loop"
    ENTITY = "纠错单"
    OPERATION_TERM = "回填"
    LIST_FIELDS = ["纠错编号", "关联版本", "纠错范围毫秒", "原文本", "纠正文本", "纠错来源", "是否触发重算", "纠错时间"]
    REQUIRED_FIELDS = ["纠错编号", "关联版本", "纠错范围毫秒"]
    STATUS_ORDER = ["已登记", "处理中", "已合入", "已拒绝"]
    ACTION_RULES = {"启动处理": "处理中", "合入版本": "已合入", "拒绝纠错": "已拒绝"}
    NEGATIVE_ACTIONS = ["拒绝纠错"]

    def register_correction(
        self, correction_id: str, version_id: str, ms_range: str,
        original: str, corrected: str, source: str, trigger_recompute: bool,
    ) -> tuple[dict[str, Any] | None, str]:
        """登记纠错单。"""
        rows = store.rows(self.MODULE)
        entry = {
            "id": max((int(r.get("id", 0)) for r in rows), default=0) + 1,
            "纠错编号": correction_id, "关联版本": version_id,
            "纠错范围毫秒": ms_range, "原文本": original,
            "纠正文本": corrected, "纠错来源": source,
            "是否触发重算": "是" if trigger_recompute else "否",
            "纠错时间": "2026-11-01",
            "status": "已登记", "pending": True, "abnormal": False,
        }
        rows.append(entry)
        return entry, f"纠错单 {correction_id} 已登记"

    def check_triggers_recompute(self, version_id: str) -> list[dict[str, Any]]:
        """获取指定版本中触发重算的纠错单。"""
        rows = store.rows(self.MODULE)
        return [
            r for r in rows
            if r.get("关联版本") == version_id
            and r.get("是否触发重算") == "是"
            and r.get("status") == "已合入"
        ]

    def get_by_version(self, version_id: str) -> list[dict[str, Any]]:
        """获取指定版本的所有纠错单。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("关联版本") == version_id]

    def count_pending(self) -> int:
        """统计待处理的纠错单数量。"""
        rows = store.rows(self.MODULE)
        return sum(1 for r in rows if r.get("status") == "已登记")