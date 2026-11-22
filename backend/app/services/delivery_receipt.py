"""交付回执写入领域服务：记录字幕包交付接收方的行数与签收结论，产出回执记录数据集供归档架位与审计核查消费。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class DeliveryReceiptService(BaseModuleService):
    MODULE = "delivery_receipt"
    ENTITY = "回执记录"
    OPERATION_TERM = "写入"
    LIST_FIELDS = ["回执编号", "关联字幕包", "接收方标识", "交付行数", "交付格式", "交付结论", "重交次数", "交付时间"]
    REQUIRED_FIELDS = ["回执编号", "关联字幕包", "接收方标识"]
    STATUS_ORDER = ["待交付", "交付中", "已签收", "部分签收"]
    ACTION_RULES = {"启动交付": "交付中", "确认签收": "已签收", "登记部分签收": "部分签收"}
    NEGATIVE_ACTIONS = []
