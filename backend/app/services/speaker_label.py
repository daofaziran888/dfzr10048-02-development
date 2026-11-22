"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class SpeakerLabelService(BaseModuleService):
    MODULE = "speaker_label"
    ENTITY = "标注条目"
    OPERATION_TERM = "关联"
    LIST_FIELDS = ["标注编号", "关联分段", "说话人标识", "声纹特征值", "标注来源", "标注置信度", "改标次数", "标注时间"]
    REQUIRED_FIELDS = ["标注编号", "关联分段", "说话人标识"]
    STATUS_ORDER = ["机器标注", "待人工确认", "已确认", "存在分歧"]
    ACTION_RULES = {"提交确认": "待人工确认", "确认标注": "已确认", "登记分歧": "存在分歧"}
    NEGATIVE_ACTIONS = []
