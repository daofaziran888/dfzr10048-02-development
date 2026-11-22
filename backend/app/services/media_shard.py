"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class MediaShardService(BaseModuleService):
    MODULE = "media_shard"
    ENTITY = "分片记录"
    OPERATION_TERM = "关联"
    LIST_FIELDS = ["分片编号", "关联通道", "起始秒", "结束秒", "分片字节", "校验和", "分片序号", "落盘时间"]
    REQUIRED_FIELDS = ["分片编号", "关联通道", "起始秒"]
    STATUS_ORDER = ["已落盘", "校验中", "校验通过", "校验不符"]
    ACTION_RULES = {"发起校验": "校验中", "确认通过": "校验通过", "登记不符": "校验不符"}
    NEGATIVE_ACTIONS = []
