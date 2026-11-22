"""转写配额校验领域服务：按渠道维护每日转写分钟配额，超额时排队而非丢弃已完成转写，产出配额条目数据集供调度与仲裁消费。"""
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
