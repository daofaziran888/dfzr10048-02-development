"""时间轴标注写入领域服务：在媒体时间轴上打点标注章节与关键事件，产出标注点数据集供媒体索引构建与检索消费。"""
from __future__ import annotations

from typing import Any

from app.services.alignment_trial import alignment_trial_service
from app.services.base import BaseModuleService


class TimelineMarkService(BaseModuleService):
    MODULE = "timeline_mark"
    ENTITY = "标注点"
    OPERATION_TERM = "写入"
    LIST_FIELDS = [
        "标注点编号", "关联媒体源", "标注毫秒", "标注类别", "标注文本", "批注原文",
        "区间起始毫秒", "区间结束毫秒", "建议偏移毫秒", "标注人标识", "关联分段数", "创建时间",
    ]
    REQUIRED_FIELDS = ["标注点编号", "关联媒体源", "标注毫秒"]
    STATUS_ORDER = ["已打点", "待复核", "已复核", "已作废"]
    ACTION_RULES = {
        "试算影响范围": "待复核",
        "提交复核": "待复核",
        "完成复核": "已复核",
        "作废标注点": "已作废",
    }
    NEGATIVE_ACTIONS = ["作废标注点"]

    def run_action(self, entry_id: int, action: str) -> tuple[dict[str, Any] | None, str]:
        if action == "试算影响范围":
            entry = self.get_entry(entry_id)
            if entry is None:
                return None, f"{self.ENTITY} {entry_id} 不存在或已归档"
            preview = alignment_trial_service.preview()
            affected = len(preview.get("rows", []))
            entry["最近试算编号"] = preview.get("trial_id")
            entry["最近试算影响行数"] = affected
            entry["试算入口"] = "/alignment-trial"
            return entry, f"试算视图已生成：按原片时间排列 {affected} 行受影响字幕"
        return super().run_action(entry_id, action)
