"""业务路由汇总：试算固定路由先注册，通用资源路由随后按模块 key 分派。"""
from __future__ import annotations

from app.routers import alignment_trial, resource

ROUTERS = [alignment_trial, resource]
