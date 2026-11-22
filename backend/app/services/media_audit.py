"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class MediaAuditService(BaseModuleService):
    MODULE = "media_audit"
    ENTITY = "审计条目"
    OPERATION_TERM = "采集"
    LIST_FIELDS = ["审计编号", "关联对象", "操作类型", "变更前值", "变更后值", "操作者标识", "操作来源", "操作时间"]
    REQUIRED_FIELDS = ["审计编号", "关联对象", "操作类型"]
    STATUS_ORDER = ["已记录", "待核查", "已核查", "已封存"]
    ACTION_RULES = {"提交核查": "待核查", "完成核查": "已核查", "封存条目": "已封存"}
    NEGATIVE_ACTIONS = []
