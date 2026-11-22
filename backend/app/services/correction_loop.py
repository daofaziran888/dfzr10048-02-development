"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class CorrectionLoopService(BaseModuleService):
    MODULE = "correction_loop"
    ENTITY = "纠错单"
    OPERATION_TERM = "关联"
    LIST_FIELDS = ["纠错编号", "关联版本", "纠错范围毫秒", "原文本", "纠正文本", "纠错来源", "是否触发重算", "纠错时间"]
    REQUIRED_FIELDS = ["纠错编号", "关联版本", "纠错范围毫秒"]
    STATUS_ORDER = ["已登记", "处理中", "已合入", "已拒绝"]
    ACTION_RULES = {"启动处理": "处理中", "合入版本": "已合入", "拒绝纠错": "已拒绝"}
    NEGATIVE_ACTIONS = ["拒绝纠错"]
