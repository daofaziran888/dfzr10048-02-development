"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class ArchiveShelfService(BaseModuleService):
    MODULE = "archive_shelf"
    ENTITY = "归档条目"
    OPERATION_TERM = "读取"
    LIST_FIELDS = ["归档编号", "关联媒体源", "架位标识", "归档内容类别", "归档字节", "保留窗口", "可恢复标记", "归档时间"]
    REQUIRED_FIELDS = ["归档编号", "关联媒体源", "架位标识"]
    STATUS_ORDER = ["待归档", "已归档", "可恢复", "已清理"]
    ACTION_RULES = {"执行归档": "已归档", "标记可恢复": "可恢复", "确认清理": "已清理"}
    NEGATIVE_ACTIONS = []
