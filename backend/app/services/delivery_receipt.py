"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class DeliveryReceiptService(BaseModuleService):
    MODULE = "delivery_receipt"
    ENTITY = "回执记录"
    OPERATION_TERM = "关联"
    LIST_FIELDS = ["回执编号", "关联字幕包", "接收方标识", "交付行数", "交付格式", "交付结论", "重交次数", "交付时间"]
    REQUIRED_FIELDS = ["回执编号", "关联字幕包", "接收方标识"]
    STATUS_ORDER = ["待交付", "交付中", "已签收", "部分签收"]
    ACTION_RULES = {"启动交付": "交付中", "确认签收": "已签收", "登记部分签收": "部分签收"}
    NEGATIVE_ACTIONS = []
