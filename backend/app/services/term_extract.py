"""术语抽取抽取领域服务：从转写文本中抽取术语并统计出现次数与词典命中，产出术语条目数据集供媒体索引构建消费。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class TermExtractService(BaseModuleService):
    MODULE = "term_extract"
    ENTITY = "术语条目"
    OPERATION_TERM = "抽取"
    LIST_FIELDS = ["术语编号", "关联任务", "术语文本", "出现次数", "首次出现毫秒", "所属领域", "词典命中", "抽取批次"]
    REQUIRED_FIELDS = ["术语编号", "关联任务", "术语文本"]
    STATUS_ORDER = ["已抽取", "待确认", "已入典", "已剔除"]
    ACTION_RULES = {"提交确认": "待确认", "加入词典": "已入典", "剔除术语": "已剔除"}
    NEGATIVE_ACTIONS = []

    def extract_term(
        self, term_id: str, task_id: str, term_text: str,
        occurrences: int, first_ms: int, domain: str,
        batch: str, dict_hit: bool,
    ) -> tuple[dict[str, Any] | None, str]:
        """抽取术语并写入。"""
        rows = store.rows(self.MODULE)
        entry = {
            "id": max((int(r.get("id", 0)) for r in rows), default=0) + 1,
            "术语编号": term_id, "关联任务": task_id,
            "术语文本": term_text, "出现次数": str(occurrences),
            "首次出现毫秒": str(first_ms), "所属领域": domain,
            "词典命中": "是" if dict_hit else "否",
            "抽取批次": batch,
            "status": "已抽取", "pending": True, "abnormal": False,
        }
        rows.append(entry)
        return entry, f"术语 {term_id} 已抽取"

    def get_unmatched(self) -> list[dict[str, Any]]:
        """获取所有词典未命中的术语。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("词典命中") == "否"]

    def get_by_batch(self, batch: str) -> list[dict[str, Any]]:
        """获取指定批次的术语。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("抽取批次") == batch]

    def get_confirmed_terms(self) -> list[dict[str, Any]]:
        """获取所有已入典的术语。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("status") == "已入典"]