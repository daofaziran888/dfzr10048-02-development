"""分片水位调度领域服务：记录已处理分片序号与滞后，连续分片全部产出后才推进水位，产出的水位读数数据集供失败重投与归档判断消费。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class ShardWatermarkService(BaseModuleService):
    MODULE = "shard_watermark"
    ENTITY = "水位读数"
    OPERATION_TERM = "调度"
    LIST_FIELDS = ["水位编号", "关联媒体源", "已处理分片序号", "总分片数", "滞后分片数", "最近推进时间", "滞后原因", "推进批次"]
    REQUIRED_FIELDS = ["水位编号", "关联媒体源", "已处理分片序号"]
    STATUS_ORDER = ["已推进", "轻微滞后", "严重滞后", "推进中断"]
    ACTION_RULES = {"推进水位": "轻微滞后", "登记滞后": "严重滞后", "标记中断": "推进中断"}
    NEGATIVE_ACTIONS = []

    def compute_lag_ratio(self, watermark_id: str) -> float:
        """计算指定水位的滞后率：滞后分片数 / 总分片数。"""
        rows = store.rows(self.MODULE)
        for r in rows:
            if r.get("水位编号") == watermark_id:
                total = int(r.get("总分片数", "1"))
                lag = int(r.get("滞后分片数", "0"))
                return lag / total if total > 0 else 0.0
        return 0.0

    def check_advance_blocked(self, watermark_id: str) -> tuple[bool, str]:
        """检查水位是否被阻塞：有滞后分片且无重投在进行中则推进中断。"""
        rows = store.rows(self.MODULE)
        for r in rows:
            if r.get("水位编号") == watermark_id:
                lag = int(r.get("滞后分片数", "0"))
                if lag > 0 and r.get("status") != "严重滞后":
                    r["status"] = "严重滞后"
                    return True, f"水位 {watermark_id} 有 {lag} 个滞后分片，推进中断"
                return False, "水位可推进"
        return False, f"水位 {watermark_id} 不存在"

    def advance_watermark(
        self, watermark_id: str, processed_seq: int, batch: str,
    ) -> tuple[bool, str]:
        """推进水位到指定分片序号。"""
        rows = store.rows(self.MODULE)
        for r in rows:
            if r.get("水位编号") == watermark_id:
                r["已处理分片序号"] = str(processed_seq)
                r["推进批次"] = batch
                r["最近推进时间"] = "2026-11-01"
                r["status"] = "已推进"
                r["pending"] = False
                return True, f"水位 {watermark_id} 已推进至分片 {processed_seq}"
        return False, f"水位 {watermark_id} 不存在"

    def get_lagging_watermarks(self) -> list[dict[str, Any]]:
        """获取所有有滞后分片的水位。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if int(r.get("滞后分片数", "0")) > 0]