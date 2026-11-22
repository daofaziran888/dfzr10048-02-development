"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class SpeechSegmentService(BaseModuleService):
    MODULE = "speech_segment"
    ENTITY = "语音段"
    OPERATION_TERM = "关联"
    LIST_FIELDS = ["分段编号", "关联任务", "起始毫秒", "结束毫秒", "段内文本", "段置信度", "静音前毫秒", "重叠标记"]
    REQUIRED_FIELDS = ["分段编号", "关联任务", "起始毫秒"]
    STATUS_ORDER = ["已切分", "待对齐", "已对齐", "边界冲突"]
    ACTION_RULES = {"提交对齐": "待对齐", "确认对齐": "已对齐", "登记冲突": "边界冲突"}
    NEGATIVE_ACTIONS = []
