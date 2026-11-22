"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class TranscribeTaskService(BaseModuleService):
    MODULE = "transcribe_task"
    ENTITY = "转写任务"
    OPERATION_TERM = "关联"
    LIST_FIELDS = ["任务编号", "关联分片", "转写引擎", "语言设定", "输出文本行数", "平均置信度", "转写耗时", "任务批次"]
    REQUIRED_FIELDS = ["任务编号", "关联分片", "转写引擎"]
    STATUS_ORDER = ["待转写", "转写中", "已产出", "产出异常"]
    ACTION_RULES = {"启动转写": "转写中", "确认产出": "已产出", "登记异常": "产出异常"}
    NEGATIVE_ACTIONS = []
