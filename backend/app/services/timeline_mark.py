"""时间轴标注写入领域服务：在媒体时间轴上打点标注章节与关键事件，产出标注点数据集供媒体索引构建与检索消费。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class TimelineMarkService(BaseModuleService):
    MODULE = "timeline_mark"
    ENTITY = "标注点"
    OPERATION_TERM = "写入"
    LIST_FIELDS = ["标注点编号", "关联媒体源", "标注毫秒", "标注类别", "标注文本", "标注人标识", "关联分段数", "创建时间"]
    REQUIRED_FIELDS = ["标注点编号", "关联媒体源", "标注毫秒"]
    STATUS_ORDER = ["已打点", "待复核", "已复核", "已作废"]
    ACTION_RULES = {"提交复核": "待复核", "完成复核": "已复核", "作废标注点": "已作废"}
    NEGATIVE_ACTIONS = ["作废标注点"]
