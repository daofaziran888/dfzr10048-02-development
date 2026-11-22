"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class CaptureChannelService(BaseModuleService):
    MODULE = "capture_channel"
    ENTITY = "通道配置"
    OPERATION_TERM = "采集"
    LIST_FIELDS = ["通道编号", "关联媒体源", "并发上限", "单段时长秒", "限速字节秒", "重试上限", "已拉取字节", "最近拉取"]
    REQUIRED_FIELDS = ["通道编号", "关联媒体源", "并发上限"]
    STATUS_ORDER = ["待启用", "运行中", "已限速", "已停用"]
    ACTION_RULES = {"启用通道": "运行中", "限流通道": "已限速", "停用通道": "已停用"}
    NEGATIVE_ACTIONS = ["停用通道"]
