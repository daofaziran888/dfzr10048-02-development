"""媒体源采集领域服务：接入并登记音视频媒体源实体，产出媒体源数据集供采集通道拉取。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class MediaSourceService(BaseModuleService):
    MODULE = "media_source"
    ENTITY = "媒体源"
    OPERATION_TERM = "采集"
    LIST_FIELDS = ["媒体源编号", "来源渠道", "媒体标题", "总时长秒", "采样率", "声道数", "容器格式", "接入时间"]
    REQUIRED_FIELDS = ["媒体源编号", "来源渠道", "媒体标题"]
    STATUS_ORDER = ["已登记", "拉取中", "已就绪", "拉取失败"]
    ACTION_RULES = {"启动拉取": "拉取中", "确认就绪": "已就绪", "登记失败": "拉取失败"}
    NEGATIVE_ACTIONS = []

    def register_media(
        self, media_code: str, channel: str, title: str,
        duration: int, sample_rate: int, channels: int, container: str,
    ) -> tuple[dict[str, Any] | None, str]:
        """登记新媒体源：校验后写入媒体源表。"""
        rows = store.rows(self.MODULE)
        for r in rows:
            if r.get("媒体源编号") == media_code:
                return None, f"媒体源编号 {media_code} 已存在"
        entry = {
            "id": max((int(r.get("id", 0)) for r in rows), default=0) + 1,
            "媒体源编号": media_code, "来源渠道": channel,
            "媒体标题": title, "总时长秒": str(duration),
            "采样率": str(sample_rate), "声道数": str(channels),
            "容器格式": container, "接入时间": "2026-11-01",
            "status": "已登记", "pending": True, "abnormal": False,
        }
        rows.append(entry)
        return entry, f"媒体源 {media_code} 已登记"

    def get_ready_sources(self) -> list[dict[str, Any]]:
        """获取所有已就绪的媒体源，供采集通道拉取。"""
        rows = store.rows(self.MODULE)
        return [r for r in rows if r.get("status") == "已就绪"]

    def compute_total_duration(self) -> tuple[int, int]:
        """计算所有媒体源的总时长秒数及已就绪总时长。"""
        rows = store.rows(self.MODULE)
        total = sum(int(r.get("总时长秒", "0")) for r in rows)
        ready_total = sum(
            int(r.get("总时长秒", "0")) for r in rows
            if r.get("status") == "已就绪"
        )
        return total, ready_total