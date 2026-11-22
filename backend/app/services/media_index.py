"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class MediaIndexService(BaseModuleService):
    MODULE = "media_index"
    ENTITY = "索引条目"
    OPERATION_TERM = "关联"
    LIST_FIELDS = ["索引编号", "关联媒体源", "索引词", "命中分段数", "命中毫秒位置", "索引版本", "构建耗时", "构建时间"]
    REQUIRED_FIELDS = ["索引编号", "关联媒体源", "索引词"]
    STATUS_ORDER = ["构建中", "已就绪", "已过期", "构建失败"]
    ACTION_RULES = {"启动构建": "构建中", "标记就绪": "已就绪", "登记失败": "构建失败"}
    NEGATIVE_ACTIONS = []
