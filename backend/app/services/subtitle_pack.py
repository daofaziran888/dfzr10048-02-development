"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class SubtitlePackService(BaseModuleService):
    MODULE = "subtitle_pack"
    ENTITY = "字幕包"
    OPERATION_TERM = "关联"
    LIST_FIELDS = ["字幕包编号", "关联媒体源", "绑定版本", "字幕行数", "覆盖时长秒", "导出格式", "下载次数", "生成时间"]
    REQUIRED_FIELDS = ["字幕包编号", "关联媒体源", "绑定版本"]
    STATUS_ORDER = ["待生成", "生成中", "可下载", "已失效"]
    ACTION_RULES = {"启动生成": "生成中", "标记可下载": "可下载", "强制失效": "已失效"}
    NEGATIVE_ACTIONS = []
