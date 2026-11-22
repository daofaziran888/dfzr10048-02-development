"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class ConfidenceReviewService(BaseModuleService):
    MODULE = "confidence_review"
    ENTITY = "复核条目"
    OPERATION_TERM = "关联"
    LIST_FIELDS = ["复核编号", "关联分段", "段置信度", "复核阈值", "复核结论", "复核人标识", "复核耗时", "回写版本"]
    REQUIRED_FIELDS = ["复核编号", "关联分段", "段置信度"]
    STATUS_ORDER = ["待复核", "复核中", "已通过", "已驳回"]
    ACTION_RULES = {"启动复核": "复核中", "通过条目": "已通过", "驳回条目": "已驳回"}
    NEGATIVE_ACTIONS = ["驳回条目"]
