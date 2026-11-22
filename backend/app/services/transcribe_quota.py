"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class TranscribeQuotaService(BaseModuleService):
    MODULE = "transcribe_quota"
    ENTITY = "配额条目"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["配额编号", "来源渠道", "转写引擎", "日配额分钟", "已用分钟", "计量窗口", "超额处置", "最近结算"]
    REQUIRED_FIELDS = ["配额编号", "来源渠道", "转写引擎"]
    STATUS_ORDER = ["充足", "接近上限", "已超额", "已冻结"]
    ACTION_RULES = {"调整配额": "接近上限", "登记超额": "已超额", "冻结配额": "已冻结"}
    NEGATIVE_ACTIONS = []
