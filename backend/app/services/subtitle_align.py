"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class SubtitleAlignService(BaseModuleService):
    MODULE = "subtitle_align"
    ENTITY = "对齐结果"
    OPERATION_TERM = "关联"
    LIST_FIELDS = ["对齐编号", "关联分段", "字幕行号", "对齐起始毫秒", "对齐结束毫秒", "偏移毫秒", "对齐方式", "对齐行数"]
    REQUIRED_FIELDS = ["对齐编号", "关联分段", "字幕行号"]
    STATUS_ORDER = ["待对齐", "对齐中", "已对齐", "偏移超限"]
    ACTION_RULES = {"启动对齐": "对齐中", "确认对齐": "已对齐", "登记超限": "偏移超限"}
    NEGATIVE_ACTIONS = []
