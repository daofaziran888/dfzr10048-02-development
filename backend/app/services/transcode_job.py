"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class TranscodeJobService(BaseModuleService):
    MODULE = "transcode_job"
    ENTITY = "转码作业"
    OPERATION_TERM = "关联"
    LIST_FIELDS = ["作业编号", "关联分片", "目标编码", "目标采样率", "输出字节", "转码耗时", "失败原因", "完成时间"]
    REQUIRED_FIELDS = ["作业编号", "关联分片", "目标编码"]
    STATUS_ORDER = ["待转码", "转码中", "已完成", "已失败"]
    ACTION_RULES = {"启动转码": "转码中", "确认完成": "已完成", "登记失败": "已失败"}
    NEGATIVE_ACTIONS = []
