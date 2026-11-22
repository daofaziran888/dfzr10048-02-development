"""归档架位归档领域服务：把完成交付的媒体分片与字幕包按架位归档，保留窗口内可恢复读取，产出归档条目数据集供空间管理与恢复消费。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class ArchiveShelfService(BaseModuleService):
    MODULE = "archive_shelf"
    ENTITY = "归档条目"
    OPERATION_TERM = "归档"
    LIST_FIELDS = ["归档编号", "关联媒体源", "架位标识", "归档内容类别", "归档字节", "保留窗口", "可恢复标记", "归档时间"]
    REQUIRED_FIELDS = ["归档编号", "关联媒体源", "架位标识"]
    STATUS_ORDER = ["待归档", "已归档", "可恢复", "已清理"]
    ACTION_RULES = {"执行归档": "已归档", "标记可恢复": "可恢复", "确认清理": "已清理"}
    NEGATIVE_ACTIONS = []
