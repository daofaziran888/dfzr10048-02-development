"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class FailRedeliverService(BaseModuleService):
    MODULE = "fail_redeliver"
    ENTITY = "重投单"
    OPERATION_TERM = "关联"
    LIST_FIELDS = ["重投编号", "关联分片", "失败阶段", "失败原因", "重投次数", "重投策略", "重投结论", "重投时间"]
    REQUIRED_FIELDS = ["重投编号", "关联分片", "失败阶段"]
    STATUS_ORDER = ["待重投", "重投中", "已补齐", "重投放弃"]
    ACTION_RULES = {"启动重投": "重投中", "确认补齐": "已补齐", "放弃重投": "重投放弃"}
    NEGATIVE_ACTIONS = []
