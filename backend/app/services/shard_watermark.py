"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class ShardWatermarkService(BaseModuleService):
    MODULE = "shard_watermark"
    ENTITY = "水位读数"
    OPERATION_TERM = "关联"
    LIST_FIELDS = ["水位编号", "关联媒体源", "已处理分片序号", "总分片数", "滞后分片数", "最近推进时间", "滞后原因", "推进批次"]
    REQUIRED_FIELDS = ["水位编号", "关联媒体源", "已处理分片序号"]
    STATUS_ORDER = ["已推进", "轻微滞后", "严重滞后", "推进中断"]
    ACTION_RULES = {"推进水位": "轻微滞后", "登记滞后": "严重滞后", "标记中断": "推进中断"}
    NEGATIVE_ACTIONS = []
