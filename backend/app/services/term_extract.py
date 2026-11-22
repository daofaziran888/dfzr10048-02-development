"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class TermExtractService(BaseModuleService):
    MODULE = "term_extract"
    ENTITY = "术语条目"
    OPERATION_TERM = "关联"
    LIST_FIELDS = ["术语编号", "关联任务", "术语文本", "出现次数", "首次出现毫秒", "所属领域", "词典命中", "抽取批次"]
    REQUIRED_FIELDS = ["术语编号", "关联任务", "术语文本"]
    STATUS_ORDER = ["已抽取", "待确认", "已入典", "已剔除"]
    ACTION_RULES = {"提交确认": "待确认", "加入词典": "已入典", "剔除术语": "已剔除"}
    NEGATIVE_ACTIONS = []
