"""置信复核校验领域服务：对低于阈值的语音段做人工复核并回写结论，产出复核条目数据集供转写版本生效前置消费。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class ConfidenceReviewService(BaseModuleService):
    MODULE = "confidence_review"
    ENTITY = "复核条目"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["复核编号", "关联分段", "段置信度", "复核阈值", "复核结论", "复核人标识", "复核耗时", "回写版本"]
    REQUIRED_FIELDS = ["复核编号", "关联分段", "段置信度"]
    STATUS_ORDER = ["待复核", "复核中", "已通过", "已驳回"]
    ACTION_RULES = {"启动复核": "复核中", "通过条目": "已通过", "驳回条目": "已驳回"}
    NEGATIVE_ACTIONS = ["驳回条目"]

    def needs_review(self, segment_confidence: float, threshold: float) -> bool:
        """判断是否需要人工复核。"""
        return segment_confidence < threshold

    def submit_review(
        self, review_id: str, conclusion: str, reviewer: str,
        elapsed_seconds: int, writeback_version: str,
    ) -> tuple[bool, str, dict[str, Any] | None]:
        """提交复核结论并回写版本。"""
        rows = store.rows(self.MODULE)
        for r in rows:
            if r.get("复核编号") == review_id:
                r["复核结论"] = conclusion
                r["复核人标识"] = reviewer
                r["复核耗时"] = str(elapsed_seconds)
                r["回写版本"] = writeback_version
                if conclusion == "通过":
                    r["status"] = "已通过"
                    r["pending"] = False
                else:
                    r["status"] = "已驳回"
                    r["pending"] = True
                    r["abnormal"] = True
                return True, f"复核 {review_id} 结论: {conclusion}", dict(r)
        return False, f"复核条目 {review_id} 不存在", None

    def get_reviews_by_segment(self, segment_id: str) -> list[dict[str, Any]]:
        """获取指定语音段的所有复核条目。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("关联分段") == segment_id]

    def get_reviews_by_version(self, version_id: str) -> list[dict[str, Any]]:
        """获取回写到指定版本的所有复核条目。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("回写版本") == version_id]

    def all_passed_for_version(self, version_id: str) -> bool:
        """检查回写到指定版本的所有复核是否都已通过。"""
        reviews = self.get_reviews_by_version(version_id)
        if not reviews:
            return False
        return all(r.get("status") == "已通过" for r in reviews)