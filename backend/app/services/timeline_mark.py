"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class TimelineMarkService(BaseModuleService):
    MODULE = "timeline_mark"
    ENTITY = "标注点"
    OPERATION_TERM = "关联"
    LIST_FIELDS = ["标注点编号", "关联媒体源", "标注毫秒", "标注类别", "标注文本", "标注人标识", "关联分段数", "创建时间"]
    REQUIRED_FIELDS = ["标注点编号", "关联媒体源", "标注毫秒"]
    STATUS_ORDER = ["已打点", "待复核", "已复核", "已作废"]
    ACTION_RULES = {"提交复核": "待复核", "完成复核": "已复核", "作废标注点": "已作废"}
    NEGATIVE_ACTIONS = ["作废标注点"]
