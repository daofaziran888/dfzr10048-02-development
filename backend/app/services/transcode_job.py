"""转码作业转换领域服务：把分片转成转写引擎可接受的统一编码与采样率，产出转码作业数据集供转写任务消费。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class TranscodeJobService(BaseModuleService):
    MODULE = "transcode_job"
    ENTITY = "转码作业"
    OPERATION_TERM = "转换"
    LIST_FIELDS = ["作业编号", "关联分片", "目标编码", "目标采样率", "输出字节", "转码耗时", "失败原因", "完成时间"]
    REQUIRED_FIELDS = ["作业编号", "关联分片", "目标编码"]
    STATUS_ORDER = ["待转码", "转码中", "已完成", "已失败"]
    ACTION_RULES = {"启动转码": "转码中", "确认完成": "已完成", "登记失败": "已失败"}
    NEGATIVE_ACTIONS = []
