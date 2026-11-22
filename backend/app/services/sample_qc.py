"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class SampleQcService(BaseModuleService):
    MODULE = "sample_qc"
    ENTITY = "质检样本"
    OPERATION_TERM = "关联"
    LIST_FIELDS = ["样本编号", "关联任务", "抽样比例", "抽样分段数", "字错数", "字错率", "质检结论", "质检人标识"]
    REQUIRED_FIELDS = ["样本编号", "关联任务", "抽样比例"]
    STATUS_ORDER = ["待质检", "质检中", "已通过", "已驳回"]
    ACTION_RULES = {"启动质检": "质检中", "通过样本": "已通过", "驳回样本": "已驳回"}
    NEGATIVE_ACTIONS = ["驳回样本"]
