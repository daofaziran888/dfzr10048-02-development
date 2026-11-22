"""失败重投回填领域服务：登记转码或转写失败分片的重投单，只处理仍缺失分片不覆盖已成功产出，产出重投单数据集供水位推进消费。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class FailRedeliverService(BaseModuleService):
    MODULE = "fail_redeliver"
    ENTITY = "重投单"
    OPERATION_TERM = "回填"
    LIST_FIELDS = ["重投编号", "关联分片", "失败阶段", "失败原因", "重投次数", "重投策略", "重投结论", "重投时间"]
    REQUIRED_FIELDS = ["重投编号", "关联分片", "失败阶段"]
    STATUS_ORDER = ["待重投", "重投中", "已补齐", "重投放弃"]
    ACTION_RULES = {"启动重投": "重投中", "确认补齐": "已补齐", "放弃重投": "重投放弃"}
    NEGATIVE_ACTIONS = []

    def register_redeliver(
        self, redeliver_id: str, shard_id: str, fail_stage: str,
        fail_reason: str, strategy: str,
    ) -> tuple[dict[str, Any] | None, str]:
        """登记失败重投单。"""
        rows = store.rows(self.MODULE)
        entry = {
            "id": max((int(r.get("id", 0)) for r in rows), default=0) + 1,
            "重投编号": redeliver_id, "关联分片": shard_id,
            "失败阶段": fail_stage, "失败原因": fail_reason,
            "重投次数": "0", "重投策略": strategy,
            "重投结论": "-", "重投时间": "-",
            "status": "待重投", "pending": True, "abnormal": False,
        }
        rows.append(entry)
        return entry, f"重投单 {redeliver_id} 已登记"

    def execute_redeliver(
        self, redeliver_id: str, success: bool, conclusion: str,
    ) -> tuple[bool, str]:
        """执行重投并记录结论。"""
        rows = store.rows(self.MODULE)
        for r in rows:
            if r.get("重投编号") == redeliver_id:
                count = int(r.get("重投次数", "0")) + 1
                r["重投次数"] = str(count)
                r["重投时间"] = "2026-11-01"
                if success:
                    r["重投结论"] = conclusion
                    r["status"] = "已补齐"
                    r["pending"] = False
                    return True, f"重投 {redeliver_id} 已补齐"
                else:
                    r["重投结论"] = conclusion
                    r["status"] = "待重投" if count < 3 else "重投放弃"
                    r["pending"] = count < 3
                    return False, f"重投 {redeliver_id} 第 {count} 次失败"
        return False, f"重投单 {redeliver_id} 不存在"

    def get_by_shard(self, shard_id: str) -> list[dict[str, Any]]:
        """获取指定分片的所有重投单。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("关联分片") == shard_id]

    def get_pending(self) -> list[dict[str, Any]]:
        """获取所有待重投的单据。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("status") == "待重投"]