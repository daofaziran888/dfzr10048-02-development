"""采集通道采集领域服务：管理通道限速参数与并发拉取，产出通道配置数据集供分片切分消费。"""
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
