"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class MediaSourceService(BaseModuleService):
    MODULE = "media_source"
    ENTITY = "媒体源"
    OPERATION_TERM = "采集"
    LIST_FIELDS = ["媒体源编号", "来源渠道", "媒体标题", "总时长秒", "采样率", "声道数", "容器格式", "接入时间"]
    REQUIRED_FIELDS = ["媒体源编号", "来源渠道", "媒体标题"]
    STATUS_ORDER = ["已登记", "拉取中", "已就绪", "拉取失败"]
    ACTION_RULES = {"启动拉取": "拉取中", "确认就绪": "已就绪", "登记失败": "拉取失败"}
    NEGATIVE_ACTIONS = []
