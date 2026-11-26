"""字幕对齐关联领域服务：把语音段与字幕行按时间轴对齐并记录偏移，产出对齐结果数据集供字幕包生成与纠错回路消费。"""
from __future__ import annotations

from typing import Any

from app.services.alignment_trial import MEDIA_ID, alignment_trial_service
from app.services.base import BaseModuleService
from app.store import store


class SubtitleAlignService(BaseModuleService):
    MODULE = "subtitle_align"
    ENTITY = "对齐结果"
    OPERATION_TERM = "关联"
    LIST_FIELDS = ["对齐编号", "关联分段", "字幕行号", "对齐起始毫秒", "对齐结束毫秒", "偏移毫秒", "对齐方式", "对齐行数"]
    REQUIRED_FIELDS = ["对齐编号", "关联分段", "字幕行号"]
    STATUS_ORDER = ["待对齐", "对齐中", "已对齐", "待再审", "偏移超限"]
    ACTION_RULES = {"启动对齐": "对齐中", "确认对齐": "已对齐", "完成再审": "已对齐", "登记超限": "偏移超限"}
    NEGATIVE_ACTIONS = []

    def run_action(self, entry_id: int, action: str) -> tuple[dict[str, Any] | None, str]:
        """字幕行确认对齐时，让试算领域服务计算实际采纳值和并发来源。"""
        entry = store.find(self.MODULE, entry_id)
        if entry is None:
            return None, f"{self.ENTITY} {entry_id} 不存在或已归档"

        is_trial_line = (
            entry.get("关联媒体源") == MEDIA_ID
            or entry.get("媒体标识") == MEDIA_ID
            or entry.get("line_number") is not None
        )
        if action == "完成再审" and is_trial_line:
            result = alignment_trial_service.complete_review(entry_id, "字幕对齐页")
            return result.get("entry") or entry, result.get("message", "再审已完成")

        if action == "确认对齐" and is_trial_line:
            result = alignment_trial_service.confirm({
                "entry_id": entry_id,
                "reviewer": "字幕对齐页",
            })
            if result.get("ok") and result.get("results"):
                item = result["results"][0]
                return item.get("entry") or entry, item["message"]
            return entry, result.get("message", "对齐确认未生效")

        return super().run_action(entry_id, action)

    def check_offset_threshold(self, align_id: str, max_offset: int) -> tuple[bool, str]:
        """检查对齐偏移是否超过阈值。"""
        rows = store.rows(self.MODULE)
        for r in rows:
            if r.get("对齐编号") == align_id:
                offset = int(r.get("偏移毫秒", "0"))
                if offset > max_offset:
                    r["status"] = "偏移超限"
                    r["abnormal"] = True
                    return False, f"偏移 {offset}ms 超过阈值 {max_offset}ms，需要纠错回路处理"
                return True, f"偏移 {offset}ms 在阈值内"
        return False, f"对齐条目 {align_id} 不存在"

    def get_alignments_by_segment(self, segment_id: str) -> list[dict[str, Any]]:
        """获取指定语音段的所有对齐结果。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("关联分段") == segment_id]

    def get_overshoot_alignments(self, max_offset: int) -> list[dict[str, Any]]:
        """获取所有偏移超限的对齐结果。"""
        rows = store.rows(self.MODULE)
        return [
            r for r in rows
            if int(r.get("偏移毫秒", "0")) > max_offset
        ]

    def recalculate_alignment(
        self, align_id: str, new_start: int, new_end: int, new_offset: int,
    ) -> tuple[bool, str]:
        """重新计算对齐参数并更新。"""
        rows = store.rows(self.MODULE)
        for r in rows:
            if r.get("对齐编号") == align_id:
                r["对齐起始毫秒"] = str(new_start)
                r["对齐结束毫秒"] = str(new_end)
                r["偏移毫秒"] = str(new_offset)
                r["对齐方式"] = "纠错后重算"
                r["status"] = "已对齐"
                r["abnormal"] = False
                return True, f"对齐 {align_id} 已重新计算"
        return False, f"对齐条目 {align_id} 不存在"